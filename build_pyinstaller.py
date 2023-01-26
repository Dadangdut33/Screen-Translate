import os
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
    "--icon=./assets/logo.ico",
    "--add-data=./assets;assets",
    "--add-data=./user_manual;user_manual",
    "--add-data=./user_manual/Readme.txt;.",
    "--add-data=./user_manual/Changelog.txt;.",
    "--add-data=./LICENSE;.",
    "--add-data=./LICENSE;LICENSE.txt",
    "--exclude-module=pyinstaller",
    "--exclude-module=cx_Freeze",
]

# ask for console or not
console = input("Do you want to hide console window? (y/n) (default y): ")
specName = f"ScreenTranslate {__version__}"
argsName = f"-n{specName}"

if console.lower() == "n":
    specName += "-C"
    argsName += "-C"
    extend = [argsName, "-c"]
    print(">> Console window will be shown")
else:
    extend = [argsName]
    print(">> Console window will be hidden")

options.extend(extend)


# -----------------
# run pyinstaller
parser = generate_parser()
args = parser.parse_args(options)
run_makespec(**vars(args))

# get spec file content as .txt
specFile = f"{specName}.spec"
spec = ""
with open(specFile, "r") as f:
    spec = f.read()
    # replace exe name to ScreenTranslate
    spec = spec.replace(f"name='{specName}'", f"name='ScreenTranslate'", 1)

# write spec file
with open(specFile, "w") as f:
    f.write(spec)

# run pyinstaller
run([specFile])
