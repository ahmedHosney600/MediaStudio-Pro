import json
import os
import re

SETTINGS_FILE = "settings.json"

# The defaults if the user opens the app for the very first time
DEFAULT_SETTINGS = {
    "cut_speed": "Fastest (Keyframe Copy)",
    "export_format": "Video",
    "concurrent_tasks": 2,
    "save_path": "",
    "review_duration": 2.0,
    "nudge_short": 0.10,
    "nudge_med": 1.0,
    "nudge_long": 5.0,
    
    "sc_play_forward": "L",
    "sc_play_backward": "J",
    "sc_stop": "K",
    "sc_mark_start": "I",
    "sc_mark_end": "O",
    "sc_snap_start": "Shift+I",
    "sc_snap_end": "Shift+O",
    "sc_preview_cut": "Alt+Space",
    "sc_review_cut": "Shift+Space",
    
    "sc_nudge_start_left": "Alt+Left",
    "sc_nudge_start_right": "Alt+Right",
    "sc_nudge_end_left": "Ctrl+Left",
    "sc_nudge_end_right": "Ctrl+Right",
    
    "sc_nudge_playhead_left_short": "Left",
    "sc_nudge_playhead_right_short": "Right",
    "sc_nudge_playhead_left_med": "Shift+Left",
    "sc_nudge_playhead_right_med": "Shift+Right",
    "sc_nudge_playhead_left_long": "Ctrl+Left",
    "sc_nudge_playhead_right_long": "Ctrl+Right",
    
    "sc_prev_clip": "Up",
    "sc_next_clip": "Down",
    "sc_focus_clip": "Shift+Z",
    "sc_undo": "Ctrl+Z",
    "sc_redo": "Ctrl+Shift+Z"
}

def load_settings():
    """Loads settings from JSON, merges with defaults to ensure all keys exist."""
    settings = DEFAULT_SETTINGS.copy()
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            try:
                loaded = json.load(f)
                settings.update(loaded)
            except json.JSONDecodeError:
                pass
    return settings

def save_settings(settings):
    """Saves the settings dictionary to a JSON file."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)


def time_to_sec(time_str):
    """Converts SRT/VTT timestamp (00:00:01,000 or 00:00:01.000) to seconds."""
    time_str = time_str.replace(',', '.') # Normalize SRT commas to VTT periods
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

def parse_subtitle_file(file_path):
    """Reads an SRT or VTT file and returns a list of subtitle dictionaries."""
    parsed_subtitles = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split the file by double line breaks (which separate subtitle blocks)
    blocks = content.strip().split('\n\n')

    for block in blocks:
        lines = block.split('\n')
        # We need at least an index, a timestamp line, and text
        if len(lines) >= 3: 
            time_line = lines[1]
            
            # Check if this line actually contains the timestamp arrow
            if "-->" in time_line:
                start_str, end_str = time_line.split(" --> ")
                
                try:
                    start_sec = time_to_sec(start_str.strip())
                    end_sec = time_to_sec(end_str.strip())
                    
                    # Join all remaining lines as the text (in case it's multi-line)
                    text = " ".join(lines[2:]).strip()
                    
                    parsed_subtitles.append({
                        "start": start_sec,
                        "end": end_sec,
                        "text": text
                    })
                except Exception as e:
                    print(f"Skipping invalid timestamp line: {time_line}")
                    
    return parsed_subtitles