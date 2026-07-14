# ScriptCutter - Pro

A powerful, efficient desktop application built with PySide6 and FFmpeg that automates the process of clipping videos based on text scripts. By matching your script against a subtitle file (SRT/VTT), the application automatically finds the precise boundaries for clips in a video. It also supports adding manual custom clips, previewing the cuts with an interactive timeline and waveform, and batch exporting everything seamlessly.

## ✨ Features

* **Script-Based Automatic Clipping**: Paste segments of a script wrapped in `"""`, and the tool matches the text against imported subtitles to find exact start and end times automatically.
* **Smart Arabic Text Matching**: Specialized logic for normalizing Arabic text (removing tashkeel, standardizing Alef, Yaa, Taa) to ensure bulletproof subtitle matching even with inconsistencies.
* **Custom Manual Clips**: Add custom manual clips, set their bounds via a visual timeline, and organize them in a dedicated tab.
* **Interactive Timeline & Audio Waveform**: Built with `pyqtgraph` to visualize audio peaks. Easily adjust start and end points by dragging intuitive colored handles.
* **Built-in Media Player**: Review cuts accurately with a synchronized video and audio player.
* **Customizable Shortcuts**: Professional NLE (Non-Linear Editor) style JKL navigation. Nudge playhead, jump between clips, and snap bounds using configurable keyboard shortcuts. Also supports Undo/Redo (`Ctrl+Z` / `Cmd+Z`) for bound adjustments.
* **Batch Export System**: Export all generated clips at once (video, audio, or both) using asynchronous background processing to keep the UI responsive.
* **Persistent Settings System**: Save your output directories, customize shortcuts, choose export modes (Fastest vs. Re-encode), and more in a persistent configuration.

## 🚀 Prerequisites

1. **Python 3.8+**
2. **FFmpeg**: Must be installed and accessible in your system's PATH. (`ffmpeg` and `ffprobe` commands must work from your terminal).
   * **macOS**: `brew install ffmpeg`
   * **Windows**: `winget install ffmpeg` or download manually from the official site.
   * **Linux**: `sudo apt install ffmpeg`

## 🛠️ How to Setup

1. Clone or download this repository.
2. Navigate to the project folder in your terminal:
   ```bash
   cd ScriptCutter
   ```
3. Create and activate a virtual environment (Recommended):
   ```bash
   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```
4. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🎮 How to Run

With your virtual environment activated, run the main script:
```bash
python main.py
```

## 📖 How to Use

1. **Load Media**: Click **🎬 Import Video** and select your source video file (.mp4, .mkv, .mov). The app will automatically generate and display an audio waveform in the timeline.
2. **Load Subtitles**: In the **Script Clips** tab, click **📝 Import Subtitles** to load the `.srt` or `.vtt` file corresponding to your video.
3. **Add Script**: In the **Script Importer** text area, paste your script segments. Wrap each distinct clip you want to extract in triple quotes. For example:
   ```text
   """This is the first sentence I want to cut."""
   """And here is another important moment."""
   ```
4. **Generate Clips**: Click **Generate Clips**. The app will match your script against the subtitles and populate the clip list.
5. **Adjust Bounds**: Click on any clip in the list to load it onto the timeline. The selected script text will be highlighted in yellow. You can visually inspect and adjust the start and end points by dragging the green (start) and red (end) lines on the waveform.
6. **Preview**: Use the Spacebar or standard NLE shortcuts (J, K, L) to preview your clips.
7. **Export**: Click **✂️ Export Current Clip** to save just the currently selected clip, or **🚀 Batch Export All** to process and save all clips across all tabs in one go. You can choose to export Video, Audio, or Both.
