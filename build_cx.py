from screen_translate._version import __version__
from cx_Freeze import setup, Executable

# ! DEEPL SCRAPER IS NOT SUPPORTED when build using cx_freeze !
# I don't really know why but it just get stuck there when calling sync_playwright()
print("WARNING: DEEPL SCRAPER IS NOT SUPPORTED when build using cx_freeze !")
print("I don't really know why but it just get stuck there when calling sync_playwright()")
print("Use pyinstaller instead if you want to build the app yourself")


build_options = {
    "packages": ["asyncio"],
    "includes": [],
    "excludes": ["pyinstaller", "cx_Freeze"],
    "include_files": [
        ("theme", "theme"),
        ("user_manual", "user_manual"),
        ("assets", "lib/assets"),
        ("LICENSE", "LICENSE.txt"),
        ("user_manual/readme.txt", "README.txt"),
    ],
}

import sys

# ask for console or not
console = input("Do you want to hide console window? (y/n) (default y): ").lower()
if console == "n":
    base = None
    print(">> Console window will be shown")
else:
    base = "Win32GUI" if sys.platform == "win32" else None
    print(">> Console window will be hidden")

target = Executable("Main.py", base=base, target_name="ScreenTranslate", icon="assets/logo.ico")

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
