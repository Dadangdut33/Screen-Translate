import sys

from cx_Freeze import Executable, setup

from screen_translate._version import __version__

build_options = {
    "packages": ["asyncio"],
    "includes": [],
    "excludes": ["cx_Freeze"],
    "include_files": [
        ("../theme", "theme"),
        ("../user_manual", "user_manual"),
        ("../assets", "lib/assets"),
        ("../LICENSE", "LICENSE.txt"),
        ("../user_manual/readme.txt", "README.txt"),
    ],
}

# ask for console or not
console = input("Do you want to hide console window? (y/n) (default y): ").lower()
if console == "n":
    BASE = None
    print(">> Console window will be shown")
else:
    BASE = "Win32GUI" if sys.platform == "win32" else None
    print(">> Console window will be hidden")

target = Executable("Main.py", base=BASE, target_name="ScreenTranslate", icon="../assets/logo.ico")

setup(
    name="Screen Translate",
    version=__version__,
    author="Dadangdut33",
    url="https://github.com/Dadangdut33/Screen-Translate",
    download_url="https://github.com/Dadangdut33/Screen-Translate/releases/latest",
    license="MIT",
    license_files=["LICENSE"],
    description="A Screen Translator/OCR Translator made by using Python and Tesseract",
    options={"build_exe": build_options},
    executables=[target],
)
