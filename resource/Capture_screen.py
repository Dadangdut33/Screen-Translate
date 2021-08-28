import pyautogui
import backend.Capture as capture
import backend.JsonHandling as fJson
from tkinter import *
import tkinter.ttk as ttk
from Mbox import Mbox

class CaptureUI():
    root = Tk()
    stayOnTop = True
    currOpacity = '0.7'

    # Empty for padding purposes
    Label(root, text="").grid(row=0, column=0)
    Label(root, text="").grid(row=0, column=2)
    Label(root, text="").grid(row=0, column=3)
    Label(root, text="").grid(row=0, column=4)
    Label(root, text="").grid(row=0, column=5)
    Label(root, text="").grid(row=0, column=6)

    # Label for opacity slider
    opacityLabel = Label(root, text="Opacity: " + str(currOpacity))
    opacityLabel.grid(row=0, column=4, sticky='w')

    # Slider function
    root.attributes('-alpha', 0.7)
    def sliderOpac(self, x):
        self.root.attributes('-alpha', x)
        self.opacityLabel.config(text="Opacity: " + str(round(float(x), 2)))
        self.currOpacity = x

    # Capture the text
    def getText(self, offsetXY=["auto", "auto"]):
        opacBefore = self.currOpacity
        self.root.attributes('-alpha', 0)
        # Get xywh of the screen
        x, y, w, h = self.root.winfo_x(), self.root.winfo_y(
        ), self.root.winfo_width(), self.root.winfo_height()

        # X Y offset
        if offsetXY[0] == "auto":
            offsetX = pyautogui.size().width
            offsetY = pyautogui.size().height
        else:
            offsetX = offsetXY[0]
            offsetY = offsetXY[1]

        #  Alignment offset
        if offsetXY[1] == "auto":
            if(offsetX > offsetY):  # Horizontal alignment
                if(x < offsetX):
                    x += offsetX
            else:  # Vertical Alignment
                if(y < offsetY):
                    y += offsetY
        elif offsetXY[1] == "horizontal":
            if(x < offsetX):
                x += offsetX
        elif offsetXY[1] == "vertical":
            if(y < offsetY):
                y += offsetY

        # Capture screen
        coords = [x, y, w, h]
        tStatus, teserract_Loc = fJson.readSetting()
        if tStatus == False or teserract_Loc['tesseract_loc'] == "":
            self.root.wm_withdraw()  # Hide the capture window
            x = Mbox("Error: Tesseract Not Set!",
                        "Please set tesseract_loc in Setting.json.\nYou can set this in setting or modify it manually in resource/backend/json/Setting.json", 0)
            self.root.wm_deiconify()  # Show the capture window
            return

        status, result = capture.captureImg(coords, "jpn", teserract_Loc['tesseract_loc'], True)
        print(status)
        print(result)
        self.root.attributes('-alpha', opacBefore)

    def __init__(self):
        self.root.title('Capture Screen')
        self.root.geometry('500x150')
        self.root.wm_attributes('-topmost', True)
        
        # Menubar
        def stay_on_top():
            if self.stayOnTop:
                self.root.wm_attributes('-topmost', False)
                self.stayOnTop = False
            else:
                self.root.wm_attributes('-topmost', True)
                self.stayOnTop = True

        def disable_stay_on_top():
            self.root.wm_attributes('-topmost', False)

        menubar = Menu(self.root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_checkbutton(label="Disable Stay on Top", command=stay_on_top)
        menubar.add_cascade(label="Options", menu=filemenu)

        # Add to self.root
        self.root.config(menu=menubar)

        # Button
        captureBtn = Button(self.root, text="Translate", command=self.getText)
        captureBtn.grid(row=0, column=1, sticky='e')

        # opacity slider # the slider will be added to main menu not here
        opacitySlider = ttk.Scale(self.root, from_=0.01, to=1.0, value=0.7, orient=HORIZONTAL, command=self.sliderOpac)
        opacitySlider.grid(row=0, column=7, sticky='e')
# x = CaptureUI()
# x.root.mainloop()