import tkinter as tk
from tkinter import ttk
import pyperclip

from tksheet import Sheet
from screen_translate.components.custom.MBox import Mbox
from screen_translate.Globals import gClass, fJson, path_logo_icon
from screen_translate.Logging import logger

# ----------------------------------------------------------------------
class HistoryWindow:
    """History Window"""

    # ----------------------------------------------------------------
    def __init__(self, master: tk.Tk):
        self.root = tk.Toplevel(master)
        self.root.title("History")
        self.root.geometry("700x350")
        self.root.wm_attributes("-topmost", False)  # Default False
        self.root.wm_withdraw()
        gClass.hw = self  # type: ignore

        # Layout
        # frameOne
        self.f_1 = ttk.Frame(self.root)
        self.f_1.pack(side=tk.TOP, fill=tk.BOTH, padx=5, pady=(5, 0), expand=True)

        self.f_bot = ttk.Frame(self.root)
        self.f_bot.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False)

        # -----------------------
        # elements
        # sheet
        self.sheet_history = Sheet(
            self.f_1,
            page_up_down_select_row=True,
            startup_select=(0, 1, "rows"),
            header_font="Arial 10 bold",
            headers=["Engine", "From - To", "Query", "Result"],
        )
        self.sheet_history.enable_bindings()
        self.sheet_history.change_theme("light blue" if "light" in fJson.settingCache["theme"] else "dark blue")
        self.sheet_history.edit_bindings(enable=False)
        self.sheet_history.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Other stuff
        self.btn_refresh = ttk.Button(self.f_bot, text="🔄 Refresh", command=self.refresh)
        self.btn_refresh.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5, expand=False)

        self.btn_copy_to_clipboard = ttk.Button(self.f_bot, text="↳ Copy to Clipboard", command=self.copyToClipboard)
        self.btn_copy_to_clipboard.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5, expand=False)

        self.btn_copy_to_translate_box = ttk.Button(self.f_bot, text="↳ Copy to Translate Menu", command=self.copyToTranslateMenu)
        self.btn_copy_to_translate_box.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5, expand=False)

        self.btn_delete_selected = ttk.Button(self.f_bot, text="✕ Delete Selected", command=self.deleteSelected)
        self.btn_delete_selected.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5, expand=False)

        self.btn_delete_all = ttk.Button(self.f_bot, text="✕ Delete All", command=self.deleteAll)
        self.btn_delete_all.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5, expand=False)

        self.btn_ok = ttk.Button(self.f_bot, text="Ok", command=self.on_closing, style="Accent.TButton")
        self.btn_ok.pack(side=tk.RIGHT, fill=tk.X, padx=5, pady=5, expand=False)

        # ----------------------------------------------------------------
        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(path_logo_icon)
        except:
            pass

    # ----------------------------------------------------------------
    # Functions
    def show(self):
        self.refresh()
        self.root.after(0, self.root.deiconify)

    def on_closing(self):
        self.root.wm_withdraw()

    def refresh(self):
        """
        Refresh the history
        """
        success, data = fJson.readHistory()
        if not success:
            self.sheet_history.set_sheet_data(data=[["Error when fetching history!"]], redraw=True)
            return

        # Error already handled in jsonHandling
        if success:
            listData = []
            # convert json to list, then make it a list in list...
            for item in data["tl_history"]:  # type: ignore
                addToList = [item["engine"], f"{item['from']} - {item['to']}", item["query"], item["result"]]  # type: ignore

                listData.append(addToList)

            self.sheet_history.set_sheet_data(data=listData)
            self.sheet_history.set_all_cell_sizes_to_text(redraw=True)
            # ------------------------------------------------------------
            logger.info("History loaded")

    def deleteAll(self):
        """
        Delete all history data
        """
        if Mbox("Confirmation", "Are you sure you want to delete all history?", 3, self.root):
            status, statusText = fJson.deleteAllHistory()
            if status == True:
                logger.info("Success: " + statusText)
                Mbox("Success", statusText, 0, self.root)
            # Error already handled in jsonHandling

            # Refresh
            self.refresh()

    def deleteSelected(self):
        """
        Delete selected history
        """
        selected = list(self.sheet_history.get_selected_rows(get_cells=False, return_tuple=False, get_cells_as_rows=True))

        if len(selected) > 0:
            if Mbox("Confirmation", "Are you sure you want to delete the selected history?", 3, self.root):

                logger.debug("Deleting: " + str(selected))
                status, statusText = fJson.deleteCertainHistory(selected)
                if status == True:
                    logger.info(statusText)
                    Mbox("Info", statusText, 0, self.root)
                # Error already handled in jsonHandling

                # Refresh
                self.refresh()

    def copyToClipboard(self):
        """
        Copy selected history to clipboard
        """
        selected = list(self.sheet_history.get_selected_rows(get_cells=False, return_tuple=False, get_cells_as_rows=True))

        if len(selected) > 0:
            selectedData = self.sheet_history.get_row_data(selected[0], return_copy=False)

            pyperclip.copy(selectedData[2] + " -> " + selectedData[3])  # type: ignore

            # update button
            self.btn_copy_to_clipboard.config(text="✓ Copied to clipboard!")

            # update button after 1.5 seconds
            self.root.after(1500, lambda: self.btn_copy_to_clipboard.config(text="↳ Copy to Clipboard"))

    def copyToTranslateMenu(self):
        """
        Copy selected history to translate menu
        """
        selected = list(self.sheet_history.get_selected_rows(get_cells=False, return_tuple=False, get_cells_as_rows=True))

        if len(selected) > 0:
            selectedData = self.sheet_history.get_row_data(selected[0], return_copy=False)

            gClass.clear_mw_q()
            gClass.clear_mw_res()
            gClass.clear_ex_q()
            gClass.clear_ex_res()
            gClass.insert_mw_q(selectedData[2])  # type: ignore
            gClass.insert_mw_res(selectedData[3])  # type: ignore
            gClass.insert_ex_q(selectedData[2])  # type: ignore
            gClass.insert_ex_res(selectedData[3])  # type: ignore

            # update button
            self.btn_copy_to_translate_box.config(text="✓ Copied to Translate Menu!")

            # update button after 1.5 seconds
            self.root.after(1500, lambda: self.btn_copy_to_translate_box.config(text="↳ Copy to Translate Menu"))
