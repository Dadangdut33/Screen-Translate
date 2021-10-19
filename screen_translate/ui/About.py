from tkinter.font import BOLD
import tkinter.ttk as ttk
from tkinter import *
from screen_translate.Public import globalStuff, OpenUrl, CreateToolTip
from PIL import Image, ImageTk

# Classes
class AboutUI():
    """Capture Window"""
    # ----------------------------------------------------------------------
    def __init__(self):
        self.root = Tk()
        self.root.title('About Screen Translate')
        self.root.geometry('375x300')
        self.root.wm_withdraw()
        self.root.resizable(False, False)

        # Top frame
        self.topFrame = Frame(self.root, bg="white")
        self.topFrame.pack(side=TOP, fill=BOTH, expand=True)

        self.bottomFrame = Frame(self.root, bg="#F0F0F0")
        self.bottomFrame.pack(side=BOTTOM, fill=X, expand=False)

        self.bottomLeft = Frame(self.bottomFrame, bg="#F0F0F0")
        self.bottomLeft.pack(side=LEFT, fill=BOTH, expand=True)

        self.botLeftTop = Frame(self.bottomLeft, bg="#F0F0F0")
        self.botLeftTop.pack(side=TOP, fill=BOTH, expand=True)

        self.botLeftBottom = Frame(self.bottomLeft, bg="#F0F0F0")
        self.botLeftBottom.pack(side=BOTTOM, fill=BOTH, expand=True)

        self.bottomRight = Frame(self.bottomFrame, bg="#F0F0F0")
        self.bottomRight.pack(side=RIGHT, fill=BOTH, expand=True)

        # Top frame
        try: # Try catch the logo so if logo not found it can still run
            self.canvasImg = Canvas(self.topFrame, width = 98, height = 98, bg="white")      
            self.canvasImg.pack(side=TOP, padx=5, pady=5) 
            self.imgObj = Image.open(globalStuff.logoPath)
            self.imgObj = self.imgObj.resize((100, 100), Image.ANTIALIAS)

            self.img = ImageTk.PhotoImage(self.imgObj, master=self.canvasImg)
            self.canvasImg.create_image(2, 50, anchor=W, image=self.img)
        except:
            self.logoNotFoud = Label(self.topFrame, text="Fail To Load Logo, Logo not found", bg="white", fg="red")
            self.logoNotFoud.pack(side=TOP, padx=5, pady=5)
            self.root.geometry('375x325')

        self.titleLabel = Label(self.topFrame, text="Screen Translate", bg="white", font=("Helvetica", 12, BOLD))
        self.titleLabel.pack(padx=5, pady=2, side=TOP)

        self.contentLabel = Label(self.topFrame, text="An open source OCR Translation tool.\n Inspired by VNR, Visual Novel OCR, and QTranslate.\n\n" +
        "This program is completely open source, you can improve it if you\nwant by sending a pull request, you can also submit an issue if you\n found any bugs. If you are confused on how to use it you can\n" +
        "check the tutorial linked in the menu bar", bg="white")
        self.contentLabel.pack(padx=5, pady=0, side=TOP)

        # Label for version
        self.versionLabel = Label(self.botLeftTop, text=f"Version: {globalStuff.version}", font=("Segoe UI", 8))
        self.versionLabel.pack(padx=5, pady=2, ipadx=0, side=LEFT)

        self.versionUpdateStatus = Label(self.botLeftTop, text=f"({globalStuff.newVerStatusCache})", fg="blue", font=("Segoe UI", 8))
        self.versionUpdateStatus.pack(padx=0, pady=2, ipadx=0, side=LEFT)
        self.versionUpdateStatus.bind("<Button-1>", self.open_dl_link)
        self.updateToolTip = CreateToolTip(self.versionUpdateStatus, "Click to visit the download page")

        # Label for Icons credit
        self.iconsLabel = Label(self.botLeftBottom, text="Icons from", font=("Segoe UI", 8))
        self.iconsLabel.pack(padx=5, pady=0, side=LEFT)

        self.iconsLabel_2 = Label(self.botLeftBottom, text="Icons8.com", font=("Segoe UI", 8), fg="blue")
        self.iconsLabel_2.pack(padx=0, pady=0, side=LEFT) 
        self.iconsLabel_2.bind("<Button-1>", self.open_icons8)
        self.icons_8_ToolTip = CreateToolTip(self.iconsLabel_2, "Open Icons8 in web browser")

        # Button
        self.okBtn = ttk.Button(self.bottomRight, text="Ok", command=self.on_closing, width=10)
        self.okBtn.pack(padx=5, pady=5, side=RIGHT)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # Show/Hide
    def show(self):
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    # Open link
    def open_dl_link(self, event):
        OpenUrl("https://github.com/Dadangdut33/Screen-Translate/releases")

    def open_icons8(self, event):
        OpenUrl("https://icons8.com/")