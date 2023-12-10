import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from rss_downloader import RSSDownloader

class RSSDownloaderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RSS Downloader")

        self.downloader = RSSDownloader()

        self.tabs = ttk.Notebook(self.root)
        self.main_tab = ttk.Frame(self.tabs)
        self.settings_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.main_tab, text="Main")
        self.tabs.add(self.settings_tab, text="Settings")
        self.tabs.pack(expand=1, fill="both")

        self.populate_main_tab()

        self.populate_settings_tab()

        self.root.mainloop()

    def populate_main_tab(self):
        main_frame = ttk.Frame(self.main_tab, padding=(10, 10, 10, 10))
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # RSS downloadler Label
        download_label = ttk.Label(main_frame, text='RSS Downloader:')
        download_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Download Button
        download_button = ttk.Button(main_frame, text="Download", command=self.manual_download, style="Download.TButton")
        download_button.grid(row=1, column=0, columnspan=2, pady=10)

        # Separator Line
        separator = ttk.Separator(main_frame, orient="horizontal")
        separator.grid(row=2, column=0, columnspan=2, sticky="NSEW", pady=10)

        # Watchlist Label
        watchlist_label = ttk.Label(main_frame, text='Watchlist:')
        watchlist_label.grid(row=3, column=0, columnspan=2, pady=10)

        # Watchlist Listbox
        self.watchlist_listbox = tk.Listbox(main_frame, selectmode=tk.SINGLE, height=10, width=60)
        self.watchlist_listbox.grid(row=4, column=0, columnspan=2, pady=10)

        # Remove Button
        remove_button = ttk.Button(main_frame, text="Remove Item", command=self.remove_watchlist_item)
        remove_button.grid(row=5, column=0, columnspan=2, pady=10)

        # Add Button
        add_button = ttk.Button(main_frame, text="Add Item", command=self.add_watchlist_item)
        add_button.grid(row=6, column=0, columnspan=2, pady=10)

        # Refresh Button
        refresh_button = ttk.Button(main_frame, text="Refresh Watchlist", command=self.refresh_watchlist)
        refresh_button.grid(row=7, column=0, columnspan=2, pady=10)

        self.root.style = ttk.Style()
        self.root.style.configure("Download.TButton", padding=(10, 5), borderwidth=2, relief="solid")

        # Refresh Watchlist initially
        self.refresh_watchlist()

    def manual_download(self):
        downloaded_items = self.downloader.download()
        if downloaded_items:
            message = "Manual download successful. Downloaded items:\n" + "\n".join(downloaded_items)
            messagebox.showinfo("Manual Download", message)
        else:
            messagebox.showinfo("Manual Download", "No new items found.")

    def refresh_watchlist(self):
        self.watchlist_listbox.delete(0, tk.END)
        watchlist = self.downloader.get_watchlist()
        for item in watchlist:
            self.watchlist_listbox.insert(tk.END, item.title())

    def remove_watchlist_item(self):
        selected_index = self.watchlist_listbox.curselection()
        if not selected_index:
            return

        item = self.watchlist_listbox.get(selected_index)
        confirmed = messagebox.askyesno("Remove Item", f"Are you sure you want to remove '{item}' from the watchlist?")
        
        if confirmed:
            success = self.downloader.remove_item_from_watchlist(item.lower())
            if success:
                self.refresh_watchlist()
                messagebox.showinfo("Watchlist", f"Item '{item}' removed from watchlist.")
            else:
                messagebox.showwarning("Watchlist", f"Item '{item}' not found in the watchlist.")

    def add_watchlist_item(self):
        item = simpledialog.askstring("Add Item", "Enter the item to add to the watchlist:")
        if item:
            self.downloader.add_item_to_watchlist(item)
            self.refresh_watchlist()
            messagebox.showinfo("Watchlist", f"Item '{item}' added to the watchlist.")


    def populate_settings_tab(self):
        settings_frame = ttk.Frame(self.settings_tab, padding=(10, 10, 10, 10))
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Settings Label
        settings_label = ttk.Label(settings_frame, text="Settings:")
        settings_label.grid(row=0, column=0, columnspan=3, pady=10)

        self.settings_var = dict()

        settings = self.downloader.get_settings()
        for i, (setting, value) in enumerate(settings.items(), start=1):
            # Skip qBittorrent-related settings if 'qbit_integration' is 'no'
            if not setting == 'qbit_integration' and 'qbit' in setting.lower() and settings['qbit_integration'] == 'no':
                continue

            ttk.Label(settings_frame, text=f"{setting}:").grid(row=i, column=0, pady=5)

            # Check if the value is either 'yes' or 'no'
            if value.lower() in ['yes', 'no']:
                # For 'yes' or 'no', add a binary choice (Yes/No) instead of an entry box
                choice_var = tk.StringVar(value=value.capitalize())  # Initialize the choice with the current value
                choice_combobox = ttk.Combobox(settings_frame, values=['Yes', 'No'], textvariable=choice_var, state='readonly')
                choice_combobox.grid(row=i, column=1, pady=5)
                self.settings_var[setting] = choice_var
            elif "qbit_path" in setting.lower():
                # For "qbit_path", add Entry and Browse button to choose a file
                entry = ttk.Entry(settings_frame, width=40)
                entry.insert(0, value)
                entry.grid(row=i, column=1, pady=5)
                browse_button = ttk.Button(settings_frame, text="Browse", command=lambda s=setting, e=entry: self.browse_file(s, e))
                browse_button.grid(row=i, column=2, pady=5)
                self.settings_var[setting] = entry
            elif "download_dir" in setting.lower():
                # For "download_dir", add Entry and Browse button to choose a directory
                entry = ttk.Entry(settings_frame, width=40)
                entry.insert(0, value)
                entry.grid(row=i, column=1, pady=5)
                browse_button = ttk.Button(settings_frame, text="Browse", command=lambda s=setting, e=entry: self.browse_directory(s, e))
                browse_button.grid(row=i, column=2, pady=5)
                self.settings_var[setting] = entry
            else:
                # For other settings, just add Entry
                entry = ttk.Entry(settings_frame, width=50)
                entry.insert(0, value)
                entry.grid(row=i, column=1, columnspan=2, pady=5)
                self.settings_var[setting] = entry

        # Save Settings Button
        save_button = ttk.Button(settings_frame, text="Save Settings", command=self.save_settings)
        save_button.grid(row=len(settings) + 1, column=0, columnspan=3, pady=10)

    def save_settings(self):
        for setting, var in self.settings_var.items():
            if isinstance(var, tk.StringVar):
                # For binary choices, convert Yes/No to lowercase before saving
                self.downloader.change_setting(setting, var.get().lower())
            else:
                # For other settings, save the entry value
                self.downloader.change_setting(setting, var.get())
        messagebox.showinfo("Settings", "Settings saved.")
        self.populate_settings_tab()


    def browse_file(self, setting, entry):
        file_path = filedialog.askopenfilename()
        if file_path:
            entry.delete(0, tk.END)
            entry.insert(0, file_path)

    def browse_directory(self, setting, entry):
        folder_path = filedialog.askdirectory()
        if folder_path:
            entry.delete(0, tk.END)
            entry.insert(0, folder_path)
            

if __name__ == "__main__":
    app = RSSDownloaderGUI()
