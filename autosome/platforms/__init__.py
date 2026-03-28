import subprocess
import sys


def copy_to_clipboard(text: str) -> bool:
    """将文本复制到系统剪贴板。"""
    try:
        if sys.platform == "darwin":
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            proc.communicate(text.encode("utf-8"))
        elif sys.platform == "win32":
            proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE)
            proc.communicate(text.encode("utf-16le"))
        else:
            proc = subprocess.Popen(
                ["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE
            )
            proc.communicate(text.encode("utf-8"))
        return True
    except (FileNotFoundError, OSError):
        return False
