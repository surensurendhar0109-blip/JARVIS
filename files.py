"""Folders and file search."""
import os
import platform
import subprocess
import time
from pathlib import Path

from ..router import skill

HOME = Path.home()


def open_path(path):
    system = platform.system()
    if system == "Windows":
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif system == "Darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


@skill(r"^open (?:my |the )?(downloads|documents|desktop|pictures|music|videos|home)(?: folder| directory)?$")
def open_folder(m, ctx):
    name = m.group(1)
    path = HOME if name == "home" else HOME / name.capitalize()
    if not path.exists():
        return f"I can't find your {name} folder."
    open_path(path)
    return f"Opening {name}."


@skill(r"^(?:find|search for|locate) (?:a |the |my )?file (?:called |named )?(.+)")
def find_file(m, ctx):
    needle = m.group(1).strip().lower()
    deadline, hits = time.time() + 8, []
    for root, dirs, names in os.walk(HOME):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in ("appdata", "node_modules", "library")]
        for n in names:
            if needle in n.lower():
                hits.append(Path(root) / n)
        if hits or time.time() > deadline:
            if hits:
                break
            return "I searched for a few seconds without luck."
    if not hits:
        return "I couldn't find a file like that."
    open_path(hits[0].parent)
    return f"Found {hits[0].name} in {hits[0].parent.name}. I've opened the folder."
