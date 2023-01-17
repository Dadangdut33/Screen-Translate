import tkinter as tk
import tkinter.ttk as ttk
import pyperclip

from .MBox import Mbox
from screen_translate.Globals import gClass, fJson, path_logo_icon
from screen_translate.Logging import logger


# ----------------------------------------------------------------------
class HistoryUI:
    """History Window"""

    # ----------------------------------------------------------------
    def __init__(self, master):
        gClass.hw = self  # type: ignore
        self.root = tk.Toplevel(master)
        self.root.title("History")
        self.root.geometry("700x300")
        self.root.wm_attributes("-topmost", False)  # Default False
        self.root.wm_withdraw()

        # Layout
        # frameOne
        self.firstFrame = ttk.Frame(self.root)
        self.firstFrame.pack(side=tk.TOP, fill=tk.BOTH, padx=5, expand=True)
        self.firstFrameScrollX = ttk.Frame(self.root)
        self.firstFrameScrollX.pack(side=tk.TOP, fill=tk.X, padx=5, expand=False)

        self.bottomFrame = ttk.Frame(self.root)
        self.bottomFrame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False)

        # elements
        # Treeview
        self.historyTreeView = ttk.Treeview(self.firstFrame, columns=("Id", "From-To", "Query"))
        self.historyTreeView["columns"] = ("Id", "From-To", "Query")

        # Scrollbar
        self.scrollbarY = ttk.Scrollbar(self.firstFrame, orient=tk.VERTICAL)
        self.scrollbarY.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbarX = ttk.Scrollbar(self.firstFrameScrollX, orient=tk.HORIZONTAL)
        self.scrollbarX.pack(side=tk.TOP, fill=tk.X)

        self.scrollbarX.config(command=self.historyTreeView.xview)
        self.scrollbarY.config(command=self.historyTreeView.yview)
        self.historyTreeView.config(yscrollcommand=self.scrollbarY.set, xscrollcommand=self.scrollbarX.set)
        self.historyTreeView.bind("<Button-1>", self.handle_click)

        # Other stuff
        self.btnRefresh = ttk.Button(self.bottomFrame, text="🔄 Refresh", command=self.refresh)
        self.btnCopyToClipboard = ttk.Button(self.bottomFrame, text="↳ Copy to Clipboard", command=self.copyToClipboard)
        self.btnCopyToTranslateBox = ttk.Button(self.bottomFrame, text="↳ Copy to Translate Menu", command=self.copyToTranslateMenu)
        self.btnDeleteSelected = ttk.Button(self.bottomFrame, text="✕ Delete Selected", command=self.deleteSelected)
        self.btnDeleteAll = ttk.Button(self.bottomFrame, text="✕ Delete All", command=self.deleteAll)

        self.historyTreeView.heading("#0", text="", anchor=tk.CENTER)
        self.historyTreeView.heading("Id", text="Id", anchor=tk.CENTER)
        self.historyTreeView.heading("From-To", text="From-To", anchor=tk.CENTER)
        self.historyTreeView.heading("Query", text="Query", anchor=tk.W)

        self.historyTreeView.column("#0", width=20, stretch=False)
        self.historyTreeView.column("Id", anchor=tk.CENTER, width=50, stretch=True)
        self.historyTreeView.column("From-To", anchor=tk.CENTER, width=150, stretch=False)
        self.historyTreeView.column("Query", anchor=tk.W, width=10000, stretch=False)  # Make the width ridiculuosly long so it can use the x scrollbar

        self.historyTreeView.pack(side=tk.TOP, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.btnRefresh.pack(side=tk.LEFT, fill=tk.X, padx=(10, 5), pady=5, expand=False)
        self.btnCopyToClipboard.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5, expand=False)
        self.btnCopyToTranslateBox.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5, expand=False)
        self.btnDeleteSelected.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5, expand=False)
        self.btnDeleteAll.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5, expand=False)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(path_logo_icon)
        except:
            pass

        self.refresh()

    # ----------------------------------------------------------------
    # Functions
    def show(self):
        self.refresh()
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    def deleteSelected(self):
        """
        Delete selected history
        """
        selected = self.historyTreeView.selection()

        if len(selected) > 0:
            if Mbox("Confirmation", "Are you sure you want to delete the selected history?", 3, self.root):
                toDeleteList = []
                for item in selected:
                    toDeleteList.append(self.historyTreeView.item(item, "values")[0])

                status, statusText = fJson.deleteCertainHistory(toDeleteList)
                if status == True:
                    logger.info("Delete status: " + statusText)
                    Mbox("Info", statusText, 0, self.root)
                # Error already handled in jsonHandling

                # Refresh
                self.refresh()

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

    def refresh(self):
        """
        Refresh the history
        """
        status, data = fJson.readHistory()
        # Error already handled in jsonHandling
        if status == True:
            listData = []
            # convert json to list, then make it a list in list...
            for item in data["tl_history"]:  # type: ignore
                addToList = [item["id"], item["from"], item["to"], item["query"], item["result"], item["engine"]]  # type: ignore

                listData.append(addToList)

            for i in self.historyTreeView.get_children():
                self.historyTreeView.delete(i)

            count = 0
            for record in listData:
                # Parent
                parentID = count
                self.historyTreeView.insert(parent="", index="end", text="", iid=str(count), values=(record[0], record[1] + "-" + record[2], record[3].replace("\n", " ")))

                count += 1
                # Child
                self.historyTreeView.insert(parent=str(parentID), index="end", text="", iid=str(count), values=(record[0], "Using " + record[5], record[4].replace("\n", " ")))

                count += 1
            # ------------------------------------------------------------
            logger.info("History loaded")
        else:
            for i in self.historyTreeView.get_children():
                self.historyTreeView.delete(i)

    def copyToClipboard(self):
        """
        Copy selected history to clipboard
        """
        sel_Index = self.historyTreeView.focus()
        if sel_Index != "":
            dataRow = self.historyTreeView.item(sel_Index, "values")
            pyperclip.copy(dataRow[2].strip())

            Mbox("Success", "Copied to clipboard", 0, self.root)

    def copyToTranslateMenu(self):
        """
        Copy selected history to translate menu
        """
        sel_Index = self.historyTreeView.focus()
        if sel_Index != "":
            dataRow = self.historyTreeView.item(sel_Index, "values")
            gClass.clear_mw_q()
            gClass.clear_ex_q()
            gClass.insert_mw_q(dataRow[2])
            gClass.insert_ex_q(dataRow[2])

            Mbox("Success", "Copied to translate menu", 0, self.root)

    def handle_click(self, event):
        """
        Handler for the treeview separator. Made it so that it does not do anything.
        """
        if self.historyTreeView.identify_region(event.x, event.y) == "separator":
            return "break"
