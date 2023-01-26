"""
Pyinstaller script to move stuff, rename, and also make a clean output folder
"""

import os, shutil
from PyInstaller.__main__ import generate_parser, run  # type: ignore
from screen_translate._version import __version__


def run_makespec(filenames, **opts):
    # Split pathex by using the path separator
    temppaths = opts["pathex"][:]
    pathex = opts["pathex"] = []
    for p in temppaths:
        pathex.extend(p.split(os.pathsep))

    import PyInstaller.building.makespec

    spec_file = PyInstaller.building.makespec.main(filenames, **opts)
    return spec_file


options = [
    "Main.py",
    "--clean",
    "--additional-hooks-dir=./_pyinstaller_hooks",
    "--runtime-hook=./_pyinstaller_hooks/add_lib.py",
    "--icon=./assets/logo.ico",
    "--add-data=./assets;assets",
    "--add-data=./user_manual;user_manual",
    "--add-data=./user_manual/Readme.txt;.",
    "--add-data=./user_manual/Changelog.txt;.",
    "--add-data=./LICENSE.txt;.",
    "--exclude-module=pyinstaller",
    "--exclude-module=cx_Freeze",
]

# ask for console or not
console = input("Do you want to hide console window? (y/n) (default y): ").lower()
specName = f"ScreenTranslate {__version__}"
argsName = f"-n{specName}"

if console == "n":
    specName += "-C"
    argsName += "-C"
    extend = [argsName, "-c"]
    print(">> Console window will be shown")
else:
    extend = [argsName, "-w"]
    print(">> Console window will be hidden")

options.extend(extend)


# -----------------
# make spec folder
parser = generate_parser()
args = parser.parse_args(options)
run_makespec(**vars(args))

# Edit spec folder
specFile = f"{specName}.spec"
spec = ""
with open(specFile, "r") as f:
    spec = f.read()
    # replace exe name to ScreenTranslate
    spec = spec.replace(f"name='{specName}'", f"name='ScreenTranslate'", 1)

# write spec file
with open(specFile, "w") as f:
    f.write(spec)

# create license.txt file
with open("LICENSE", "r") as f:
    license = f.read()
    with open("LICENSE.txt", "w") as f2:
        f2.write(license)

# run pyinstaller
run([specFile])

# delete license.txt file
print(">> Deleting created license.txt file")
os.remove("LICENSE.txt")

output_folder = f"dist/{specName}"

# create lib folder in output folder
lib_folder = f"{output_folder}/lib"
os.mkdir(lib_folder)

# move all .dll .pyd files to lib folder with some exception
print(">> Moving .dll files to lib folder")
dontMove = ["python3.dll", "python310.dll", "python38.dll", "python39.dll", "libopenblas64__v0.3.21-gcc_10_3_0.dll"]
for file in os.listdir(output_folder):
    if file.endswith(".dll") or file.endswith(".pyd"):
        if file not in dontMove:
            shutil.move(f"{output_folder}/{file}", f"{lib_folder}/{file}")
