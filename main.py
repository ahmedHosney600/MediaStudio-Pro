import sys
import os
import locale
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QSurfaceFormat
from ui.main_window import MainWindow

def main():
    # Fix locale for libmpv — must happen after PySide6 import but before mpv instances
    locale.setlocale(locale.LC_NUMERIC, 'C')
    
    # Set OpenGL surface format before creating QApplication (required for mpv + QOpenGLWidget on macOS)
    fmt = QSurfaceFormat()
    fmt.setVersion(4, 1)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    QSurfaceFormat.setDefaultFormat(fmt)
    
    # 1. Create the Qt Application
    app = QApplication(sys.argv)
    
    # Optional: Set a dark theme globally
    app.setStyle("Fusion")

    # 2. Instantiate and show the Main Window
    window = MainWindow()
    window.show()

    # 3. Run the application's event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()