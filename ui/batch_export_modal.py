from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QProgressBar, 
                               QPushButton, QHBoxLayout, QMessageBox, QListWidget)
from PySide6.QtCore import Qt, QThread, Signal
import os

from core.exporter import export_clip
from core.matcher import find_precise_clip_boundaries

class BatchExportWorker(QThread):
    progress_updated = Signal(int, str)  # (current_index, message)
    finished_all = Signal(int, int) # (success_count, fail_count)

    def __init__(self, video_path, subtitles, clips_data, save_dir, export_mode, format_type, video_ext, audio_ext, project_folder, main_window):
        super().__init__()
        self.video_path = video_path
        self.subtitles = subtitles
        self.clips_data = clips_data
        self.save_dir = save_dir
        self.export_mode = export_mode
        self.format_type = format_type
        self.video_ext = video_ext
        self.audio_ext = audio_ext
        self.project_folder = project_folder
        self.main_window = main_window
        self.is_cancelled = False

    def run(self):
        success_count = 0
        fail_count = 0
        
        for i, clip in enumerate(self.clips_data):
            if self.is_cancelled:
                break
                
            clip_base = clip['name']
            start_time = clip['start']
            end_time = clip['end']
            
            self.progress_updated.emit(i, f"Exporting {clip_base}...")
            
            if self.format_type in ["Video", "Both"]:
                vid_name = f"{self.project_folder}_{clip_base}_video"
                out_vid = self.main_window.get_unique_filename(self.save_dir, vid_name, self.video_ext)
                success, msg = export_clip(self.video_path, start_time, end_time, self.save_dir, os.path.basename(out_vid), self.export_mode, "Video")
                if success: success_count += 1
                else: fail_count += 1
                
            if self.format_type in ["Audio", "Both"]:
                aud_name = f"{self.project_folder}_{clip_base}_audio"
                out_aud = self.main_window.get_unique_filename(self.save_dir, aud_name, self.audio_ext)
                success, msg = export_clip(self.video_path, start_time, end_time, self.save_dir, os.path.basename(out_aud), self.export_mode, "Audio")
                if success: success_count += 1
                else: fail_count += 1
                
        self.progress_updated.emit(len(self.clips_data), "Finished batch export.")
        self.finished_all.emit(success_count, fail_count)

    def cancel(self):
        self.is_cancelled = True


class BatchExportModal(QDialog):
    def __init__(self, main_window, format_type="Video"):
        super().__init__(main_window)
        self.setWindowTitle("Batch Export Progress")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.main_window = main_window
        self.format_type = format_type

        layout = QVBoxLayout(self)

        self.status_label = QLabel("Initializing batch export...")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.main_window.clip_list.count())
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.log_list = QListWidget()
        layout.addWidget(self.log_list)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_export)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setEnabled(False)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        self.worker = None
        self.start_export()

    def start_export(self):
        script_count = self.main_window.script_clip_list.count()
        custom_count = self.main_window.custom_clip_list.count()
        
        if script_count == 0 and custom_count == 0:
            self.status_label.setText("No clips to export.")
            self.close_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            return

        clips_data = []
        
        # 1. Gather Script Clips
        for row in range(script_count):
            item = self.main_window.script_clip_list.item(row)
            clip_id = self.main_window.get_clip_id(item)
            if clip_id in self.main_window.clip_bounds_cache:
                bounds = self.main_window.clip_bounds_cache[clip_id]
            else:
                raw_list_text = item.text()
                clean_text = raw_list_text.split(": ", 1)[-1] 
                start_time, end_time = find_precise_clip_boundaries(clean_text, self.main_window.current_subtitles)
                bounds = {"start": start_time, "end": end_time}
                
            clip_base = self.main_window.build_clip_export_name(clip_id, row)
            clips_data.append({
                "name": clip_base,
                "start": bounds["start"],
                "end": bounds["end"]
            })
            
        # 2. Gather Custom Clips
        for row in range(custom_count):
            item = self.main_window.custom_clip_list.item(row)
            clip_id = self.main_window.get_clip_id(item)
            if clip_id in self.main_window.clip_bounds_cache:
                bounds = self.main_window.clip_bounds_cache[clip_id]
            else:
                bounds = {"start": 0.0, "end": self.main_window.timeline_view.total_duration}
                
            clip_base = self.main_window.build_clip_export_name(clip_id, row)
            clips_data.append({
                "name": clip_base,
                "start": bounds["start"],
                "end": bounds["end"]
            })

        save_dir = self.main_window.get_project_folder()
        export_mode = self.main_window.app_settings.get("cut_speed", "Fastest (Keyframe Copy)")
        video_ext = os.path.splitext(self.main_window.current_video_path)[1].lstrip('.')
        from core.exporter import get_audio_extension
        audio_ext = get_audio_extension(self.main_window.current_video_path)

        self.worker = BatchExportWorker(
            video_path=self.main_window.current_video_path,
            subtitles=self.main_window.current_subtitles,
            clips_data=clips_data,
            save_dir=save_dir,
            export_mode=export_mode,
            format_type=self.format_type,
            video_ext=video_ext,
            audio_ext=audio_ext,
            project_folder=self.main_window.current_project_folder,
            main_window=self.main_window
        )
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished_all.connect(self.on_finished)
        self.worker.start()

    def update_progress(self, index, message):
        self.progress_bar.setValue(index)
        self.status_label.setText(message)
        self.log_list.addItem(message)
        self.log_list.scrollToBottom()

    def on_finished(self, success_count, fail_count):
        self.status_label.setText(f"Done! {success_count} successful, {fail_count} failed.")
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)

    def cancel_export(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.status_label.setText("Cancelling... waiting for current export to finish.")
            self.cancel_btn.setEnabled(False)
    
    def reject(self):
        if self.worker and self.worker.isRunning():
            self.cancel_export()
        super().reject()
