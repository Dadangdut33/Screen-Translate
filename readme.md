# Screen Translate - An Easy to Use OCR Translator
<p align="center">
    <a href="https://github.com/Dadangdut33/Screen-Translate/releases/latest"><img alt="GitHub release (latest SemVer)" src="https://img.shields.io/github/v/release/Dadangdut33/Screen-Translate"></a>
    <a href="https://github.com/Dadangdut33/Screen-Translate/releases/latest"><img src="https://img.shields.io/github/downloads/Dadangdut33/Screen-Translate/total"></a> 
    <a href="https://github.com/Dadangdut33/Screen-Translate/issues"><img alt="GitHub issues" src="https://img.shields.io/github/issues/Dadangdut33/Screen-Translate"></a>
    <a href="https://github.com/Dadangdut33/Screen-Translate/pulls"><img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr/Dadangdut33/Screen-Translate"></a>
    <a href="https://github.com/Dadangdut33/Screen-Translate/commits/main"><img alt="GitHub commits since latest release (by date)" src="https://img.shields.io/github/commits-since/Dadangdut33/Screen-Translate/latest"></a><Br>
    <a href="https://github.com/Dadangdut33/Screen-Translate/stargazers"><img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/Dadangdut33/Screen-Translate?style=social"></a>
    <a href="https://github.com/Dadangdut33/Screen-Translate/network/members"><img alt="GitHub forks" src="https://img.shields.io/github/forks/Dadangdut33/Screen-Translate?style=social"></a>
</p>

STL a.k.a Screen Translate is an OCR translator tool made by utilizing Tesseract. The code is then compiled to .exe by using pyinstaller. 
Inspired by Visual Novel Reader (VNR), [Visual Novel OCR](https://github.com/leminhyen2/Visual-Novel-OCR), and [QTranslate](https://quest-app.appspot.com/)

# What can i use this for?
- You can use this just to translate text from one language to another
- You can use this to capture and translate text from documents, games, pictures, etc. As long as the text is clear enough (Tesseract might not be able to read it if it's not clear enough)

# FAQ
- **[Q]** How do i use this? \
**[A]** You can look at the [user_manual](https://github.com/Dadangdut33/Screen-Translate/tree/main/user_manual) folder or below for more information
- **[Q]** Is this safe? \
**[A]** Yes, it is completely safe. If your antivirus detect this program as a virus, it's only a false positive. If you don't believe it, you can take a look at the code yourself. 
- **[Q]** What do you mean by a "clear enough" text? \
**[A]** It means the text is not too blend it with the background. If the text is light the background needs to be darken, so it is easier to be read. Somewhat like that. In the future i might add some adjustment and more OCR options, so this might be fixed some day.

# Requirements
**For User**
- **[tesseract](https://github.com/UB-Mannheim/tesseract/wiki)**, You only need to install it and its language tessdata
- Internet connection

**For Dev**
- Python 3.5+, checked using [vermin](https://github.com/netromdk/vermin) (I am using python 3.9.6)
- Libraries from python: os, sys, functools, json, webbrowser, subprocess, datetime, Mbox, tkinter, pathlib, asyncio
- External libraries: pyperclip, pytesseract, pyautogui, pillow, deepl_scraper_pp, deep_translator, keyboard

You can install them by running pip_install.bat or by installing them yourself, full details are located at [requirements.txt](https://github.com/Dadangdut33/Screen-Translate/blob/main/requirements.txt).<br>
*If i miss anything please let me know.

# Tutorial on How To Install and Setup
**For User**
1. Download the latest [release](https://github.com/Dadangdut33/Screen-Translate/releases/tag/release) of this program
2. Install tesseract, **make sure to select install all language pack when prompted**
3. Open the ScreenTranslate.exe
4. Check settings, make sure tesseract location is correct
5. Set monitor scaling to 100% so that image is captured accurately (If scaling is not set to 100% you will need to set offset in setting) **(Recommended)**
6. Set offset if on multiple monitors. **(Optional)**
7. Try capturing image and see if it works or not, if it doesn't, go check the image captured in img_cache folder. If it still doesn't work, try to change the offset.
8. Now that you have set everything, the app should be ready. Feel free to submit new issue on the github repository if you encounter any bugs.

**For Dev**
1. Clone the repo or download the source code of the latest release
2. Install tesseract, make sure select install all language pack when prompted
3. Install all the dependencies used for the project
4. Run and test the source code
5. If everything works, you can run the app normally running the ScreenTranslate.py file or using the TempRun.bat

if everything works and you have a suggestion or improvement, you can submit a pull request on the github repository. I will check if it's a good idea to add it.

# How To Compile It To .exe Yourself
You can use [p2exe](https://www.py2exe.org/) or many other stuff. I use [pyinstaller](https://www.pyinstaller.org/) to compile it.<br>
Command used are
```
# On Source Code Directory
pyinstaller ScreenTranslate.spec
```
Read [this stackoverflow post](https://stackoverflow.com/questions/5458048/how-can-i-make-a-python-script-standalone-executable-to-run-without-any-dependen) to learn more on how to do it.

# Tutorial on How To Use
1. Select Language
2. Translate or Capture Image using the capture window
3. Set hotkeys and delays as needed
4. Set offset if needed (Usually when scaling is not 100% or when using multiple monitors)
5. Done

For more information you can check the [user_manual](https://github.com/Dadangdut33/Screen-Translate/tree/main/user_manual) folder

# Reporting bugs
If you encounter any bugs with the program, please report them by opening an issue on the github repository.    

# Disclaimer
This is a free open source software, you can use it for any purpose. However, I am not responsible for any damage caused by this software. Use it at your own risk. **(Not that it will do anything to you, it's just a tool to help you translate text lol)**

This is also non profit, I gain no money from creating this.
