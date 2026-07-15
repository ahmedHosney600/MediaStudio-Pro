import locale
import ctypes
import ctypes.util
from ctypes import CFUNCTYPE, c_void_p, c_char_p
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QOpenGLContext
from PySide6.QtCore import Qt, Signal

# Fix locale before any mpv import — Qt stomps over locale settings needed by libmpv
locale.setlocale(locale.LC_NUMERIC, 'C')

import mpv

# Load macOS OpenGL framework for reliable proc address resolution
_opengl_lib_path = ctypes.util.find_library('OpenGL')
_opengl_lib = ctypes.cdll.LoadLibrary(_opengl_lib_path) if _opengl_lib_path else None

# ctypes callback type matching libmpv's expected signature: (ctx, name) -> address
OpenGlCbGetProcAddrFn = CFUNCTYPE(c_void_p, c_void_p, c_char_p)


class MpvWidget(QOpenGLWidget):
    """
    A QOpenGLWidget that embeds mpv using the Render API.
    mpv renders video frames directly into the widget's OpenGL framebuffer.
    """
    rightClicked = Signal()
    _frame_ready = Signal()  # Cross-thread signal for repaint

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #000000;")
        self._update_pending = False
        
        self._player = mpv.MPV(
            vo='libmpv',
            hwdec='videotoolbox-copy',  # Hardware decoding with safe copy to RAM. Prevents CPU thermal throttling on macOS (which degrades performance over time) and avoids OpenGL interop bugs.
            profile='fast',           
            keep_open='yes',
            idle='yes',
            input_default_bindings=False,
            input_vo_keyboard=False,
            osc=False,
            osd_level=0,
        )
        
        self._current_position = 0.0
        
        @self._player.property_observer('time-pos')
        def on_time_pos(_name, value):
            if value is not None:
                self._current_position = value
        self._time_observer = on_time_pos
        
        
        self._ctx = None
        self._is_loaded = False
        self._proc_addr_cb = None  # prevent GC of ctypes callback
        
        # Connect cross-thread signal to update() for safe repaint
        self._frame_ready.connect(self.update)

    def initializeGL(self):
        """Called once when the OpenGL context is ready. Initialize mpv render context."""
        glctx = QOpenGLContext.currentContext()
        
        # Create the proc address callback as a proper ctypes CFUNCTYPE
        def _get_proc_address(ctx, name):
            if isinstance(name, bytes):
                name_str = name.decode('utf-8')
            else:
                name_str = name
            
            # Try macOS OpenGL framework first (most reliable on macOS)
            if _opengl_lib:
                try:
                    addr = ctypes.cast(getattr(_opengl_lib, name_str), c_void_p).value
                    if addr:
                        return addr
                except AttributeError:
                    pass
            
            # Fallback to Qt's getProcAddress
            if glctx:
                result = glctx.getProcAddress(name_str)
                if result:
                    return int(result)
            
            return 0
        
        # Wrap in CFUNCTYPE and keep reference to prevent garbage collection
        self._proc_addr_cb = OpenGlCbGetProcAddrFn(_get_proc_address)
        
        self._ctx = mpv.MpvRenderContext(
            self._player,
            'opengl',
            opengl_init_params={'get_proc_address': self._proc_addr_cb}
        )
        
        # Register callback — mpv calls this (from its thread) when a new frame is ready
        self._ctx.update_cb = self._on_mpv_update

    def _on_mpv_update(self):
        """Called by mpv (from a background thread) when a new frame is ready."""
        if not self._update_pending:
            self._update_pending = True
            self._frame_ready.emit()

    def paintGL(self):
        """Render the current mpv frame into our OpenGL framebuffer."""
        self._update_pending = False
        if self._ctx is None:
            return
        
        # Get actual pixel dimensions (critical for Retina/HiDPI on macOS)
        ratio = self.devicePixelRatioF()
        w = int(self.width() * ratio)
        h = int(self.height() * ratio)
        
        fbo = self.defaultFramebufferObject()
        
        self._ctx.render(
            flip_y=True,
            opengl_fbo={
                'fbo': fbo,
                'w': w,
                'h': h,
            }
        )

    def resizeGL(self, w, h):
        """Handle resize — mpv auto-adjusts on next render call."""
        pass

    # ==========================================
    # PUBLIC PLAYBACK API
    # ==========================================

    def load(self, file_path):
        """Load a media file into the player (non-blocking)."""
        self._player.pause = True  # Start paused
        self._player.play(file_path)
        self._is_loaded = True

    def play(self):
        """Resume or start playback."""
        if not self._is_loaded:
            return
        self._player.pause = False

    def pause(self):
        """Pause playback."""
        if not self._is_loaded:
            return
        self._player.pause = True

    def stop(self):
        """Stop playback (pause and stay at current frame)."""
        self.pause()

    def seek(self, time_sec):
        """Seek to a position in seconds."""
        if not self._is_loaded:
            return
        try:
            self._player.seek(time_sec, reference='absolute')
        except Exception:
            pass

    @property
    def position(self):
        """Current playback position in seconds."""
        if not self._is_loaded:
            return 0.0
        return self._current_position

    @property
    def is_playing(self):
        """Whether the player is currently playing (not paused)."""
        if not self._is_loaded:
            return False
        try:
            return not self._player.pause
        except Exception:
            return False

    def set_volume(self, vol):
        """Set volume (0.0 to 1.0 range, mapped to mpv's 0-100)."""
        self._player.volume = vol * 100

    def set_playback_rate(self, rate):
        """Set playback speed multiplier."""
        self._player.speed = rate

    # ==========================================
    # EVENT HANDLING
    # ==========================================

    def mousePressEvent(self, event):
        """Emit rightClicked signal on right-click for stop-playback behavior."""
        if event.button() == Qt.RightButton:
            self.rightClicked.emit()
        super().mousePressEvent(event)

    def closeEvent(self, event):
        """Clean up mpv on widget close."""
        self._cleanup()
        super().closeEvent(event)

    def _cleanup(self):
        """Release mpv resources."""
        if self._ctx is not None:
            self._ctx.free()
            self._ctx = None
        if self._player is not None:
            self._player.terminate()
            self._player = None
