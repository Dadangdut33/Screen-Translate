<p align="center">
    <img src="https://raw.github.com/Dadangdut33/Screen-Translate/main/logo.png" width="250px" alt="Screen Translate Logo">
</p>

<h1 align="center"> Screen Translate - An Easy to Use OCR Translator </h1>
<p align="center">
    <a href="https://lgtm.com/projects/g/Dadangdut33/Screen-Translate/alerts/"><img alt="Total alerts" src="https://img.shields.io/lgtm/alerts/g/Dadangdut33/Screen-Translate.svg?logo=lgtm&logoWidth=18"/></a>
    <a href="https://lgtm.com/projects/g/Dadangdut33/Screen-Translate/context:python"><img alt="Language grade: Python" src="https://img.shields.io/lgtm/grade/python/g/Dadangdut33/Screen-Translate.svg?logo=lgtm&logoWidth=18"/></a>
    <a href="https://github.com/Dadangdut33/Screen-Translate/issues"><img alt="GitHub issues" src="https://img.shields.io/github/issues/Dadangdut33/Screen-Translate"></a>
    <a href="https://github.com/Dadangdut33/Screen-Translate/pulls"><img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr/Dadangdut33/Screen-Translate"></a>
    <a href="https://github.com/Dadangdut33/Screen-Translate/releases/latest"><img src="https://img.shields.io/github/downloads/Dadangdut33/Screen-Translate/total"></a> <br>
    <a href="https://github.com/Dadangdut33/Screen-Translate/releases/latest"><img alt="GitHub release (latest SemVer)" src="https://img.shields.io/github/v/release/Dadangdut33/Screen-Translate"></a>
    <a href="https://github.com/Dadangdut33/Screen-Translate/commits/main"><img alt="GitHub commits since latest release (by date)" src="https://img.shields.io/github/commits-since/Dadangdut33/Screen-Translate/latest"></a><Br>
    <a href="https://github.com/Dadangdut33/Screen-Translate/stargazers"><img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/Dadangdut33/Screen-Translate?style=social"></a>
    <a href="https://github.com/Dadangdut33/Screen-Translate/network/members"><img alt="GitHub forks" src="https://img.shields.io/github/forks/Dadangdut33/Screen-Translate?style=social"></a>
</p>

STL a.k.a Screen Translate is an OCR translator tool made by utilizing Tesseract and opencv-python. The code is then compiled to .exe by using pyinstaller. 
Inspired by Visual Novel Reader (VNR), [Visual Novel OCR](https://github.com/leminhyen2/Visual-Novel-OCR), and [QTranslate](https://quest-app.appspot.com/). Also available to download at [sourceforge](https://sourceforge.net/projects/screen-translate/)

<h1>Jump to</h1>

- [Features](#features)
- [What can i use this for?](#what-can-i-use-this-for)
- [FAQ](#faq)
- [Requirements](#requirements)
- [Downloads](#downloads)
- [How To Install and Setup](#how-to-install-and-setup)
- [How To Uninstall](#how-to-uninstall)
- [How To Compile It To .exe Yourself](#how-to-compile-it-to-exe-yourself)
- [How To Use](#how-to-use)
- [Reporting bugs and feature requests](#reporting-bugs-and-feature-requests)
- [Credits](#credits)
- [Disclaimer](#disclaimer)

---
<br>

<p align="center">
    <img src="https://media.discordapp.net/attachments/653206818759376916/919918869899014164/unknown.png" width="700" alt="Screen Translate Looks">
</p>

# Features
- Translation
- OCR Detection
- Snip and translate
  <details open>
  <summary>Example</summary>
    <img src="https://raw.githubusercontent.com/Dadangdut33/Screen-Translate/main/user_manual/6_5_snipdemonstration.png" width="700" alt="Screen Translate Looks">
  </details>
- Capture and translate
  <details open>
  <summary>Example</summary>
    <img src="https://raw.githubusercontent.com/Dadangdut33/Screen-Translate/main/user_manual/6_1_Usage_Example_old.png" width="700" alt="Screen Translate Looks">
    <img src="https://raw.githubusercontent.com/Dadangdut33/Screen-Translate/main/user_manual/6_3_usageExampleNew.png" width="700" alt="Screen Translate Looks">
  </details>

# What can i use this for?
- You can use this just to translate text from one language to another
- You can use this to capture and translate text from documents, games, pictures, etc.
- You can use this to just capture the text if you wanted to by setting the tl engine to None. 

# FAQ
- **[Q]** How do i use this? \
**[A]** You can look at the [user_manual](https://github.com/Dadangdut33/Screen-Translate/tree/main/user_manual) folder or [below](https://github.com/Dadangdut33/Screen-Translate#tutorial-on-how-to-use) for more information
- **[Q]** Is this safe? \
**[A]** Yes, it is completely safe. If your antivirus detect this program as a virus, it's only a false positive. If you don't believe it, you can take a look at the code yourself. 
- **[Q]** What do you mean by a "clear enough" text? \
**[A]** It means the text is not too blend it with the background. If the text is light the background needs to be darken, so it is easier to be read, somewhat like that. But, this has been improved with some tricks which you can experiment with in the settings.

# Requirements
**For User**
- **[tesseract](https://github.com/UB-Mannheim/tesseract/wiki)**, needed for the ocr. Install it with all the language pack.
- **[LibreTranslate](https://github.com/LibreTranslate/LibreTranslate)** for offline translation (Optional).
- Internet connection for the other engines (Needed if not using LibreTranslate). 

**For Dev**
- Python 3.5+, checked using [vermin](https://github.com/netromdk/vermin) (I am using python 3.9.6)
- Install [the dependencies](https://github.com/Dadangdut33/Screen-Translate/blob/main/requirements.txt) You can install them by running `pip_install.bat` or by typing `pip install -r requirements.txt`.

# Downloads
- [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
- [LibreTranslate](https://github.com/LibreTranslate/LibreTranslate) (Optional)
- [The application (ScreenTranslate/STL)](https://github.com/Dadangdut33/Screen-Translate/releases/latest)

# How To Install and Setup
**For User**
1. Download the latest [release](https://github.com/Dadangdut33/Screen-Translate/releases/tag/release) of this program
2. Install tesseract, **make sure to select install all language pack when prompted**
3. Set up LibreTranslate **(Optional)**
4. Open the ScreenTranslate.exe
5. Check settings, make sure tesseract location is correct
6. Set monitor scaling to 100% so that image is captured accurately (If scaling is not set to 100% you will need to set offset in setting) **(Recommended)**
7. Set offset if on multiple monitors. **(Optional)**
8. Try capturing image and see if it works or not, if it doesn't, go check the image captured in img_captured folder. If it still doesn't work, try to change the offset.
9. Now that you have set everything, the app should be ready. Feel free to submit new issue on the github repository if you encounter any bugs.

**For Dev**
1. Clone the repo or download the source code of the latest release
2. Setup virtualenviroment if needed then Install all the dependencies for the project.
```
# On source code directory
# Create a virtualenviroment with the name STL_Venv
python -m venv STL_Venv

# Activate the virtualenviroment
source STL_Venv/bin/activate

# Install the dependencies
pip install -r requirements.txt
```
3. Install tesseract, make sure select install all language pack when prompted
4. Run and test the source code
5. If everything works, you can run the app normally running the ScreenTranslate.py file or using the TempRun.bat

if everything works and you have a suggestion or improvement, you can submit a pull request on the github repository. I will check if it's a good idea to add it.

# How To Uninstall
If you use the installer version, you can run the uninstaller inside the app folder or uninstall it from control panel. For the portable (rar) version, you can just delete them.

# How To Compile It To .exe Yourself
You can use [p2exe](https://www.py2exe.org/) or many other stuff. I use [pyinstaller](https://www.pyinstaller.org/) to compile it.<br>
There are 2 options for compiling, command used are: 
```
# On Source Code Directory
# With console window
pyinstaller ScreenTranslate_Console.spec

# No console window
pyinstaller ScreenTranslate_NoConsole.spec

# If installing using virtualenviroment
# Change STL_Venv to your virtualenviroment name
# With console window
pyinstaller --paths STL_Venv/lib/site-packages ScreenTranslate_Console.spec

# No console window
pyinstaller --paths STL_Venv/lib/site-packages ScreenTranslate_NoConsole.spec
```
Read [this stackoverflow post](https://stackoverflow.com/questions/5458048/how-can-i-make-a-python-script-standalone-executable-to-run-without-any-dependen) to learn more on how to do it.

# How To Use
1. Select Language
2. Translate or Capture Image using the capture window or the snipping feature
3. Set hotkeys and delays as needed
4. Set offset if needed (Usually when scaling is not 100% or when using multiple monitors)
5. Done

For more information you can check the [user_manual](https://github.com/Dadangdut33/Screen-Translate/tree/main/user_manual) folder

# Reporting bugs and feature requests
If you encounter any bugs with the program, please report them by opening an issue on the github repository. You can also request a feature by opening an issue.

# Credits
Icons are taken from [Icons8](https://icons8.com/)

# Disclaimer
This is a free open source software, you can use it for any purpose. However, I am not responsible for any damage caused by this software. Use it at your own risk. **(It won't create any damage though don't worry)**. This is also non profit, I gain no money from creating this.
