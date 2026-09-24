import os

SUPPORTED_EXTENSIONS = (".mp3", ".wav", ".ogg", ".flac")


def format_song_name(filepath: str) -> str:
   
    if not filepath:
        return "No song loaded"
    basename = os.path.basename(filepath)
    name, _ = os.path.splitext(basename)
    return name.replace("_", " ").replace("-", " ").title()


def format_time(seconds: float) -> str:
    
    if seconds < 0:
        seconds = 0
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes}:{secs:02d}"


def validate_audio_file(filepath: str) -> tuple[bool, str]:
    
    if not filepath:
        return False, "No file path provided."
    if not os.path.isfile(filepath):
        return False, f"File not found: {filepath}"
    _, ext = os.path.splitext(filepath)
    if ext.lower() not in SUPPORTED_EXTENSIONS:
        return False, (
            f"Unsupported format '{ext}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    return True, ""


def get_file_size_label(filepath: str) -> str:
    """Return a human-readable file size string (KB / MB)."""
    try:
        size = os.path.getsize(filepath)
        if size >= 1_048_576:
            return f"{size / 1_048_576:.1f} MB"
        return f"{size / 1024:.1f} KB"
    except OSError:
        return "Unknown size"