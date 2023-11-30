import tkinter as tk
from tkinter import ttk

from tkinter import filedialog
import rss_downloader


class Application:
    def __init__(self):
        self._root = tk.Tk()

        self._root.geometry(f'{self._root.winfo_screenwidth()//2}x{self._root.winfo_screenheight()//2}')
        self._root.title("RSS Downloader")

        self._mainframe = tk.Frame(self._root, background='grey')
        self._mainframe.pack(fill='both', expand=True)

        download_button = ttk.Button(self._mainframe, text='Download', command=self._download)
        download_button.grid(row=0, column=0, pady=10, padx=10)

        self._root.mainloop()
    
    def _download(self):
        rss_downloader.RSSDownloader().single_run()