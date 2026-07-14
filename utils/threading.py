from PySide6.QtCore import QThread, Signal
from core.media_engine import generate_waveform_data

class WaveformWorker(QThread):
    # Signals allow the background thread to talk back to the UI thread
    finished = Signal(list) 
    
    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path

    def run(self):
        # This code runs in the background
        peaks = generate_waveform_data(self.video_path)
        # Emit the result back to the UI thread
        self.finished.emit(peaks)