import subprocess
from utils.binary_resolver import get_ffprobe_path

def has_video_stream(file_path):
    cmd = [
        get_ffprobe_path(), "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_type",
        "-of", "default=nw=1:nk=1",
        file_path
    ]
    try:
        out = subprocess.check_output(cmd, text=True).strip()
        return bool(out)
    except:
        return False

print("Has video:", has_video_stream("/Users/ahmedmac/Desktop/My Computer/Programming Proejcts/ScriptCutter/main.py"))
