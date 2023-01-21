from threading import Thread
import tkinter.ttk as ttk
import tkinter as tk
import requests
from PIL import Image, ImageTk


from screen_translate._version import __version__
from screen_translate.Logging import logger
from screen_translate.Globals import gClass, path_logo_png, path_logo_icon, app_name, fJson
from screen_translate.utils.Helper import OpenUrl, nativeNotify
from .Tooltip import CreateToolTip

# Classes
class AboutWindow:
    """About Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: tk.Tk):
        gClass.aw = self  # type: ignore
        self.root = tk.Toplevel(master)
        self.root.title("About Screen Translate")
        self.root.geometry("450x325")
        self.root.wm_withdraw()

        # Top frame
        self.f_top = tk.Frame(self.root, bg="white")
        self.f_top.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.f_bot = tk.Frame(self.root, bg="#F0F0F0")
        self.f_bot.pack(side=tk.BOTTOM, fill=tk.X, expand=False)

        self.f_bot_l = tk.Frame(self.f_bot, bg="#F0F0F0")
        self.f_bot_l.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.f_bot_l_t = tk.Frame(self.f_bot_l, bg="#F0F0F0")
        self.f_bot_l_t.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.f_bot_l_b = tk.Frame(self.f_bot_l, bg="#F0F0F0")
        self.f_bot_l_b.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.f_bot_r = tk.Frame(self.f_bot, bg="#F0F0F0")
        self.f_bot_r.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Top frame
        try:  # Try catch the logo so if logo not found it can still run
            self.canvasImg = tk.Canvas(self.f_top, width=98, height=98, bg="white")
            self.canvasImg.pack(side=tk.TOP, padx=5, pady=5)
            self.imgObj = Image.open(path_logo_png)
            self.imgObj = self.imgObj.resize((100, 100), Image.ANTIALIAS)

            self.img = ImageTk.PhotoImage(self.imgObj, master=self.canvasImg)
            self.canvasImg.create_image(2, 50, anchor=tk.W, image=self.img)
        except Exception:
            self.logoNotFoud = tk.Label(self.f_top, text="Fail To Load Logo, Logo not found", bg="white", fg="red")
            self.logoNotFoud.pack(side=tk.TOP, padx=5, pady=5)
            self.root.geometry("375x325")

        self.lbl_title = tk.Label(self.f_top, text="Screen Translate", bg="white", font=("Helvetica", 12, "bold"))
        self.lbl_title.pack(padx=5, pady=2, side=tk.TOP)

        self.lbl_content = tk.Label(
            self.f_top,
            text="An open source OCR Translation tool.\n\n"
            + "This program is completely open source, you can improve it if you\nwant by sending a pull request, you can also submit an issue if you\n found any bugs. If you are confused on how to use it you can\n"
            + "check the tutorial linked in the menu bar",
            bg="white",
        )
        self.lbl_content.pack(padx=5, pady=0, side=tk.TOP)

        # tk.Label for version
        self.lbl_version = tk.Label(self.f_bot_l_t, text=f"Version: {__version__}", font=("Segoe UI", 8))
        self.lbl_version.pack(padx=5, pady=2, ipadx=0, side=tk.LEFT)

        self.checkUpdateLabelFg = "blue"
        self.checkUpdateLabelText = "(check for update)"
        self.checkUpdateLabelFunc = self.check_for_update

        self.checkUpdateLabel = tk.Label(self.f_bot_l_t, text=self.checkUpdateLabelText, fg=self.checkUpdateLabelFg, font=("Segoe UI", 8))
        self.checkUpdateLabel.pack(padx=0, pady=2, ipadx=0, side=tk.LEFT)
        self.checkUpdateLabel.bind("<Button-1>", self.checkUpdateLabelFunc)
        self.tooltipCheckUpdate = CreateToolTip(self.checkUpdateLabel, "Click to check for update")

        # tk.Label for Icons credit
        self.lbl_icon = tk.Label(self.f_bot_l_b, text="Translate Icons in logo from", font=("Segoe UI", 8))
        self.lbl_icon.pack(padx=5, pady=0, side=tk.LEFT)

        self.lbl_icon_link = tk.Label(self.f_bot_l_b, text="Icons8.com 🡽", font=("Segoe UI", 8), fg="blue")
        self.lbl_icon_link.pack(padx=0, pady=0, side=tk.LEFT)
        self.lbl_icon_link.bind("<Button-1>", self.open_icons8)
        self.icons_8_ToolTip = CreateToolTip(self.lbl_icon_link, "Open Icons8 in web browser")

        # Button
        self.btn_ok = ttk.Button(self.f_bot_r, text="Ok", command=self.on_closing, width=10)
        self.btn_ok.pack(padx=5, pady=5, side=tk.RIGHT)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(path_logo_icon)
        except:
            pass

        self.onInit()

    def onInit(self):
        if fJson.settingCache["checkUpdateOnStart"]:
            logger.info("Checking for update on start")
            self.checkingOnStart = True
            self.check_for_update()

    # Show/Hide
    def show(self):
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    # Open link
    def open_dl_link(self, _event=None):
        OpenUrl("https://github.com/Dadangdut33/Screen-Translate/releases")

    def open_icons8(self, _event=None):
        OpenUrl("https://icons8.com/")

    def check_for_update(self, _event=None, onStart=False):
        if self.checking:
            return

        self.checking = True
        self.checkUpdateLabelText = "Checking..."
        self.checkUpdateLabelFg = "black"
        self.tooltipCheckUpdate.text = "Checking... Please wait"
        self.checkUpdateLabel.config(text=self.checkUpdateLabelText, fg=self.checkUpdateLabelFg)
        self.root.update()
        logger.info("Checking for update...")

        Thread(target=self.req_update_check, daemon=True).start()

    def req_update_check(self):
        try:
            # request to github api, compare version. If not same tell user to update
            req = requests.get("https://raw.githubusercontent.com/Dadangdut33/Screen-Translate/main/version.txt")

            if req is not None and req.status_code == 200:
                data = req.json()
                latest_version = str(data["tag_name"])
                if __version__ < latest_version:
                    logger.info(f"New version found: {latest_version}")
                    self.checkUpdateLabelText = "New version available"
                    self.checkUpdateLabelFg = "blue"
                    self.checkUpdateLabelFunc = self.open_dl_link
                    self.tooltipCheckUpdate.text = "Click to go to the latest release page"
                    nativeNotify("New version available", "Visit the repository to download the latest update", path_logo_png, app_name)
                else:
                    logger.info("No update available")
                    self.checkUpdateLabelText = "You are using the latest version"
                    self.checkUpdateLabelFg = "green"
                    self.checkUpdateLabelFunc = self.check_for_update
                    self.tooltipCheckUpdate.text = "Up to date"
            else:
                logger.warning("Failed to check for update")
                self.checkUpdateLabelText = "Fail to check for update!"
                self.checkUpdateLabelFg = "red"
                self.checkUpdateLabelFunc = self.check_for_update
                self.tooltipCheckUpdate.text = "Click to try again"
                if not self.checkingOnStart:  # suppress error if checking on start
                    nativeNotify("Fail to check for update!", "Click to try again", path_logo_png, app_name)

            self.checkUpdateLabel.config(text=self.checkUpdateLabelText, fg=self.checkUpdateLabelFg)
            self.checkUpdateLabel.bind("<Button-1>", self.checkUpdateLabelFunc)

            self.checking = False
        except Exception as e:
            logger.exception(e)
            self.checkUpdateLabelText = "Fail to check for update!"
            self.checkUpdateLabelFg = "red"
            self.checkUpdateLabelFunc = self.check_for_update
            self.tooltipCheckUpdate.text = "Click to try again"
            self.checkUpdateLabel.config(text=self.checkUpdateLabelText, fg=self.checkUpdateLabelFg)
            self.checkUpdateLabel.bind("<Button-1>", self.checkUpdateLabelFunc)
        finally:
            self.checking = False
