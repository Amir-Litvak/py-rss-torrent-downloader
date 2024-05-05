import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from rss_downloader import RSSDownloader
import webbrowser
from multiprocessing import Process
import telegram_bot

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
        self.manual_download()
        """ if self.downloader.get_telegram_integration_status():
            self.proc = Process(target=telegram_bot.bot, daemon=True)
            self.proc.start() """
        self.root.mainloop()

    def populate_main_tab(self):
        main_frame = ttk.Frame(self.main_tab, padding=(10, 10, 10, 10))
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # RSS downloader Label
        download_label = ttk.Label(main_frame, text='RSS Downloader:')
        download_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Download Button
        download_button = ttk.Button(main_frame, text="Download", command=self.manual_download, style="Download.TButton")
        download_button.grid(row=1, column=0, columnspan=3, pady=10)

        # Separator Line
        separator = ttk.Separator(main_frame, orient="horizontal")
        separator.grid(row=2, column=0, columnspan=3, sticky="NSEW", pady=10)

        # Watchlist Label
        watchlist_label = ttk.Label(main_frame, text='Watchlist:')
        watchlist_label.grid(row=3, column=0, columnspan=3, pady=10)

        # Watchlist Treeview (2D Listbox) with Vertical Scrollbar
        columns = ("Item", "Directory Path")
        self.watchlist_tree = ttk.Treeview(main_frame, columns=columns, show="headings", selectmode='browse')

        self.watchlist_tree.heading("Item", text="Item")
        self.watchlist_tree.heading("Directory Path", text="Directory Path")
        self.watchlist_tree.column("Item", width=200, anchor='center')
        self.watchlist_tree.column("Directory Path", width=300, anchor='center')

        # Double-click event binding for the Watchlist Treeview
        self.watchlist_tree.bind("<Double-1>", self.double_click_watchlist_item)


        # Adding Vertical Scrollbar
        tree_scroll_y = ttk.Scrollbar(main_frame, orient="vertical", command=self.watchlist_tree.yview)
        tree_scroll_y.grid(row=4, column=3, sticky="NS")

        self.watchlist_tree.configure(yscrollcommand=tree_scroll_y.set)

        self.watchlist_tree.grid(row=4, column=0, columnspan=3, pady=10)

        # Remove Button
        remove_button = ttk.Button(main_frame, text="Remove Item", command=self.remove_watchlist_item)
        remove_button.grid(row=5, column=0, pady=10)

        # Add Button
        add_button = ttk.Button(main_frame, text="Add Item", command=self.add_watchlist_item)
        add_button.grid(row=5, column=1, pady=10)

        # Select Directory Button
        select_directory_button = ttk.Button(main_frame, text="Change Item Directory", command=self.select_directory)
        select_directory_button.grid(row=5, column=2, pady=10)

        # Refresh Button
        refresh_button = ttk.Button(main_frame, text="Refresh Watchlist", command=self.refresh_watchlist)
        refresh_button.grid(row=6, column=0, columnspan=3, pady=10)

        # External Link Button
        link_button = ttk.Button(main_frame, text="Visit AniChart", command=self.open_anichart)
        link_button.grid(row=7, column=0, columnspan=3, pady=10)

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
        self.watchlist_tree.delete(*self.watchlist_tree.get_children())
        watchlist = self.downloader.get_watchlist()
        for item, dir_path in watchlist.items():
            self.watchlist_tree.insert("", "end", values=(item.title(), dir_path))

    def open_anichart(self):
        webbrowser.open("https://anichart.net")

    def double_click_watchlist_item(self, event):
        selected_item = self.watchlist_tree.selection()
        if selected_item:
            self.select_directory()

    def remove_watchlist_item(self):
        selected_item = self.watchlist_tree.selection()
        if not selected_item:
            return

        item = self.watchlist_tree.item(selected_item, 'values')[0]
        confirmed = messagebox.askyesno("Remove Item", f"Are you sure you want to remove '{item}' from the watchlist?")
        
        if confirmed:
            success = self.downloader.remove_item_from_watchlist(item.lower())
            if success:
                self.refresh_watchlist()
                messagebox.showinfo("Watchlist", f"Item '{item}' removed from watchlist.")
            else:
                messagebox.showwarning("Watchlist", f"Item '{item}' not found in the watchlist.")

    def add_watchlist_item(self):
        dialog = AddItemDialog(self.root)
        self.root.wait_window(dialog.top)
        if dialog.result:
            item_name, dir_path = dialog.result
            self.downloader.add_item_to_watchlist(item_name, dir_path)
            self.refresh_watchlist()
            messagebox.showinfo("Watchlist", f"Item '{item_name}' added to the watchlist with file path '{dir_path}'.")


    def select_directory(self):
        selected_item = self.watchlist_tree.selection()
        if not selected_item:
            return

        item = self.watchlist_tree.item(selected_item, 'values')[0]
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.downloader.add_item_to_watchlist(item, f"{dir_path}/")
            self.refresh_watchlist()
            messagebox.showinfo("Watchlist", f"Directory path for item '{item}' updated.")

    def populate_settings_tab(self):
        settings_frame = ttk.Frame(self.settings_tab, padding=(10, 10, 10, 10))
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Settings Label
        settings_label = ttk.Label(settings_frame, text="Settings:")
        settings_label.grid(row=0, column=0, columnspan=3, pady=10)

        self.settings_var = dict()

        settings = self.downloader.get_settings()
        for i, (setting, value) in enumerate(settings.items(), start=1):
            # Skip qBittorrent-related settings if 'qbit_integration' is 'no' &
            # Skip Telegram-related settings if 'telegram_integration' is 'no'
            if not setting == 'qbit_integration' and 'qbit' in setting.lower() and settings['qbit_integration'] == 'no':
                continue

            if not setting == 'telegram_integration' and 'telegram' in setting.lower() and settings['telegram_integration'] == 'no':
                continue

            ttk.Label(settings_frame, text=f"{setting.replace('_', ' ').title()}:").grid(row=i, column=0, pady=5)

            # Check if the value is either 'yes' or 'no'
            if value.lower() in ['yes', 'no']:
                # For 'yes' or 'no', add a binary choice (Yes/No) instead of an entry box
                choice_var = tk.StringVar(value=value.capitalize())  # Initialize the choice with the current value
                choice_combobox = ttk.Combobox(settings_frame, values=['Yes', 'No'], textvariable=choice_var, state='readonly')
                choice_combobox.grid(row=i, column=1, pady=5)
                self.settings_var[setting] = choice_var
            elif value.lower() in ['magnet', '.torrent file']:
                choice_var = tk.StringVar(value=value.capitalize())  # Initialize the choice with the current value
                choice_combobox = ttk.Combobox(settings_frame, values=['Magnet', '.torrent File'], textvariable=choice_var, state='readonly')
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
            entry.insert(0, folder_path + '/')
            
class AddItemDialog:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Add Item")

        self.result = None

        self.item_label = ttk.Label(self.top, text="Item:")
        self.item_label.grid(row=0, column=0, padx=10, pady=10)

        self.item_entry = ttk.Entry(self.top, width=30)
        self.item_entry.grid(row=0, column=1, padx=10, pady=10)

        self.dir_label = ttk.Label(self.top, text="Directory Path:")
        self.dir_label.grid(row=1, column=0, padx=10, pady=10)

        self.dir_entry = ttk.Entry(self.top, width=30)
        self.dir_entry.grid(row=1, column=1, padx=10, pady=10)

        self.select_dir_button = ttk.Button(self.top, text="Select Directory", command=self.browse_directory)
        self.select_dir_button.grid(row=1, column=2, padx=10, pady=10)

        self.add_button = ttk.Button(self.top, text="Add", command=self.add_item)
        self.add_button.grid(row=2, column=0, columnspan=3, pady=10)

    def browse_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.item_entry.delete(0, tk.END)
            self.item_entry.insert(0, file_path)

    def browse_directory(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, folder_path)

    def add_item(self):
        item_name = self.item_entry.get()
        dir_path = self.dir_entry.get()
        if dir_path:
            dir_path += '/'
        if item_name:
            self.result = (item_name, dir_path)
        self.top.destroy()

