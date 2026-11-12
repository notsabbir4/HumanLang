"""Your own pictures, sounds and music in a game: the files sit next to the program (or are uploaded in the Playground).

    draw the picture "face.png" at 10, 20 with size 32 by 32
    play the sound "boom.wav"
    play the music "theme.mp3"      (or a built-in tune: "adventure", "chill", "chase", "boss", "doom")
    stop the music
"""
import base64
import os

PICTURES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
AUDIO = {".wav": "audio/wav", ".mp3": "audio/mpeg", ".ogg": "audio/ogg", ".m4a": "audio/mp4"}
BUILTIN_MUSIC = ("adventure", "chill", "chase", "boss", "doom")
MAX_FILE = 3 * 1024 * 1024
MAX_FILES = 24
MAX_TOTAL = 16 * 1024 * 1024


def kind_of(name):
    ext = os.path.splitext(name)[1].lower()
    if ext in PICTURES:
        return "picture"
    if ext in AUDIO:
        return "audio"
    return None


def mime_of(name):
    ext = os.path.splitext(name)[1].lower()
    return PICTURES.get(ext) or AUDIO.get(ext)


def scan_folder(folder, code=None):
    """{file name: kind} of the usable files in a folder; with code, only the ones the program names in quotes."""
    out, total = {}, 0
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return out
    for n in names:
        path = os.path.join(folder, n)
        kind = kind_of(n)
        if not kind or not os.path.isfile(path):
            continue
        if code is not None and f'"{n}"' not in code:
            continue
        size = os.path.getsize(path)
        if size > MAX_FILE or total + size > MAX_TOTAL or len(out) >= MAX_FILES:
            continue
        total += size
        out[n] = kind
    return out


def data_urls(folder, names):
    out = {}
    for n in names:
        with open(os.path.join(folder, n), "rb") as f:
            out[n] = f"data:{mime_of(n)};base64," + base64.b64encode(f.read()).decode()
    return out
