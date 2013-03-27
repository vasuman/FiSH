import sys
from cx_Freeze import setup, Executable

build_exe_options = {"packages": [], "includes": ["hashlib", "re"]}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "FiSH",
        version = "0.1dev",
        description = "P2P File Shaing",
        options = {"build_exe": build_exe_options},
        executables = [Executable("fish.py", base=base)])