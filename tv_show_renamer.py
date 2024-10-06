import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
import re
from functools import lru_cache
from threading import Timer
import logging

# Set up logging
logging.basicConfig(filename='tv_show_renamer.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def debounce(wait):
    """ Decorator that will postpone a function's execution until after wait seconds
        have elapsed since the last time it was invoked. """
    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)
            try:
                debounced.t.cancel()
            except(AttributeError):
                pass
            debounced.t = Timer(wait, call_it)
            debounced.t.start()
        return debounced
    return decorator

class TVShowRenamer:
    def __init__(self, master):
        self.master = master
        master.title("TV Show File Renamer")
        master.geometry("800x800")
        
        # Make the window resizable
        master.resizable(True, True)
        
        self.configure_styles()

        self.directory = tk.StringVar()
        self.season_number = tk.StringVar(value="01")
        self.start_episode = tk.StringVar(value="01")
        self.end_episode = tk.StringVar(value="")
        self.file_extensions = tk.StringVar(value=".mp4,.mkv,.avi")

        self.undo_stack = []
        self.file_cache = None
        self.create_widgets()

    def configure_styles(self):
        try:
            self.style = ttk.Style()
            self.style.theme_use('clam')
            
            colors = {
                "PRIMARY_COLOR": "#2196F3",
                "SECONDARY_COLOR": "#1976D2",
                "BACKGROUND_COLOR": "#F5F5F5",
                "SURFACE_COLOR": "#FFFFFF",
                "TEXT_COLOR": "#212121",
                "ACCENT_COLOR": "#FF4081",
                "BORDER_COLOR": "#E0E0E0"
            }
            
            self.style.configure('TFrame', background=colors["BACKGROUND_COLOR"])
            self.style.configure('TLabel', 
                                 background=colors["BACKGROUND_COLOR"], 
                                 foreground=colors["TEXT_COLOR"], 
                                 font=('Segoe UI', 11))
            self.style.configure('TEntry', 
                                 fieldbackground=colors["SURFACE_COLOR"], 
                                 foreground=colors["TEXT_COLOR"], 
                                 font=('Segoe UI', 11),
                                 borderwidth=1)
            self.style.map('TEntry', 
                           fieldbackground=[('readonly', colors["SURFACE_COLOR"])])
            self.style.configure('TButton', 
                                 background=colors["PRIMARY_COLOR"], 
                                 foreground=colors["SURFACE_COLOR"], 
                                 font=('Segoe UI', 11, 'bold'),
                                 borderwidth=0,
                                 padding=(10, 5))
            self.style.map('TButton', 
                           background=[('active', colors["SECONDARY_COLOR"])])
        except Exception as e:
            self.handle_error("Error configuring styles", e)

    def create_widgets(self):
        try:
            main_frame = ttk.Frame(self.master, padding="50 50 50 50", style='TFrame')
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            self.master.columnconfigure(0, weight=1)
            self.master.rowconfigure(0, weight=1)

            # Configure main_frame to be expandable
            main_frame.columnconfigure(1, weight=1)
            main_frame.rowconfigure(6, weight=1)

            ttk.Label(main_frame, text="Directory:").grid(row=0, column=0, sticky="w", padx=5, pady=10)
            entry_frame = ttk.Frame(main_frame, style='TFrame')
            entry_frame.grid(row=0, column=1, padx=5, pady=10, sticky="we")
            entry_frame.columnconfigure(0, weight=1)
            self.dir_entry = tk.Entry(entry_frame, textvariable=self.directory, 
                     font=('Segoe UI', 11), bd=1, relief=tk.SOLID)
            self.dir_entry.grid(row=0, column=0, sticky="we", ipady=5, ipadx=5)
            ttk.Button(main_frame, text="Browse", command=self.browse_directory).grid(row=0, column=2, padx=(10,0), pady=10)

            ttk.Label(main_frame, text="Season Number:").grid(row=1, column=0, sticky="w", padx=5, pady=10)
            self.season_entry = tk.Entry(main_frame, textvariable=self.season_number, width=10, 
                     font=('Segoe UI', 11), bd=1, relief=tk.SOLID)
            self.season_entry.grid(row=1, column=1, sticky="w", padx=5, pady=10, ipady=5, ipadx=5)

            ttk.Label(main_frame, text="Start Episode:").grid(row=2, column=0, sticky="w", padx=5, pady=10)
            self.start_ep_entry = tk.Entry(main_frame, textvariable=self.start_episode, width=10, 
                     font=('Segoe UI', 11), bd=1, relief=tk.SOLID)
            self.start_ep_entry.grid(row=2, column=1, sticky="w", padx=5, pady=10, ipady=5, ipadx=5)

            ttk.Label(main_frame, text="End Episode:").grid(row=3, column=0, sticky="w", padx=5, pady=10)
            self.end_ep_entry = tk.Entry(main_frame, textvariable=self.end_episode, width=10, 
                     font=('Segoe UI', 11), bd=1, relief=tk.SOLID)
            self.end_ep_entry.grid(row=3, column=1, sticky="w", padx=5, pady=10, ipady=5, ipadx=5)

            ttk.Label(main_frame, text="File Extensions:").grid(row=4, column=0, sticky="w", padx=5, pady=10)
            self.ext_entry = tk.Entry(main_frame, textvariable=self.file_extensions, width=30, 
                     font=('Segoe UI', 11), bd=1, relief=tk.SOLID)
            self.ext_entry.grid(row=4, column=1, sticky="w", padx=5, pady=10, ipady=5, ipadx=5)

            button_frame = ttk.Frame(main_frame, style='TFrame')
            button_frame.grid(row=5, column=0, columnspan=3, pady=20)
            ttk.Button(button_frame, text="Preview", command=self.preview_rename).grid(row=0, column=0, padx=5)
            ttk.Button(button_frame, text="Rename", command=self.rename_files).grid(row=0, column=1, padx=5)
            ttk.Button(button_frame, text="Undo", command=self.undo_rename).grid(row=0, column=2, padx=5)
            ttk.Button(button_frame, text="Auto-Detect", command=self.auto_detect_season_episode).grid(row=0, column=3, padx=5)
            ttk.Button(button_frame, text="Reset", command=self.reset_fields).grid(row=0, column=4, padx=5)

            preview_frame = ttk.Frame(main_frame, style='TFrame')
            preview_frame.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=20)
            preview_frame.columnconfigure(0, weight=1)
            preview_frame.rowconfigure(1, weight=1)

            ttk.Label(preview_frame, text="File Names Preview", font=('Segoe UI', 11, 'bold')).grid(row=0, column=0, pady=(0, 5))
            self.preview_text = tk.Text(preview_frame, wrap=tk.NONE,
                                        font=('Consolas', 10), bd=1, relief=tk.SOLID)
            self.preview_text.grid(row=1, column=0, sticky="nsew")
            
            # Vertical scrollbar
            preview_v_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
            preview_v_scrollbar.grid(row=1, column=1, sticky="ns")
            
            # Horizontal scrollbar (new)
            preview_h_scrollbar = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.preview_text.xview)
            preview_h_scrollbar.grid(row=2, column=0, sticky="ew")
            
            # Configure the Text widget to use both scrollbars
            self.preview_text.configure(yscrollcommand=preview_v_scrollbar.set, xscrollcommand=preview_h_scrollbar.set)

            self.dir_entry.bind('<KeyRelease>', self.update_preview)
            self.season_entry.bind('<KeyRelease>', self.update_preview)
            self.start_ep_entry.bind('<KeyRelease>', self.update_preview)
            self.end_ep_entry.bind('<KeyRelease>', self.update_preview)
            self.ext_entry.bind('<KeyRelease>', self.update_preview)
        except Exception as e:
            self.handle_error("Error creating widgets", e)

    def browse_directory(self):
        try:
            directory = filedialog.askdirectory()
            if directory:
                if not os.path.isdir(directory):
                    raise NotADirectoryError(f"Selected path is not a directory: {directory}")
                self.directory.set(directory)
                self.update_preview()
        except Exception as e:
            self.handle_error("Error selecting directory", e)

    @lru_cache(maxsize=1)
    def get_files(self):
        try:
            directory = self.directory.get()
            if not directory:
                raise ValueError("No directory selected")
            
            extensions = self.file_extensions.get().split(',')
            files = [file for file in os.listdir(directory) 
                     if any(file.lower().endswith(ext.strip().lower()) for ext in extensions)]
            return sorted(files)
        except Exception as e:
            self.handle_error("Error getting files", e)
            return []

    def preview_rename(self):
        if not self.validate_inputs():
            return

        try:
            files = self.get_files()
            self.update_preview_text(files)
        except Exception as e:
            self.handle_error("Error previewing rename", e)

    def update_preview_text(self, files):
        try:
            self.preview_text.delete(1.0, tk.END)

            season = self.season_number.get().zfill(2)
            start_ep = int(self.start_episode.get())
            end_ep = int(self.end_episode.get()) if self.end_episode.get() else None

            for i, file in enumerate(files):
                old_name = file
                episode = start_ep + i
                if end_ep and episode > end_ep:
                    break
                ext = os.path.splitext(file)[1]
                new_name = f"S{season}E{episode:02d}{ext}"

                self.preview_text.insert(tk.END, f"{old_name} -> {new_name}\n")
        except Exception as e:
            self.handle_error("Error updating preview text", e)

    def rename_files(self):
        if not self.validate_inputs():
            return

        try:
            files = self.get_files()
            directory = self.directory.get()
            season = self.season_number.get().zfill(2)
            start_ep = int(self.start_episode.get())
            end_ep = int(self.end_episode.get()) if self.end_episode.get() else None

            undo_actions = []

            for i, file in enumerate(files):
                episode = start_ep + i
                if end_ep and episode > end_ep:
                    break
                old_path = os.path.join(directory, file)
                ext = os.path.splitext(file)[1]
                new_name = f"S{season}E{episode:02d}{ext}"
                new_path = os.path.join(directory, new_name)

                try:
                    os.rename(old_path, new_path)
                    undo_actions.append((new_path, old_path))
                except OSError as e:
                    self.handle_error(f"Failed to rename {file}", e)

            self.undo_stack.append(undo_actions)
            self.show_info("Rename", f"Renamed {len(undo_actions)} files successfully.")
            self.update_preview()
        except Exception as e:
            self.handle_error("Error renaming files", e)

    def undo_rename(self):
        if not self.undo_stack:
            self.show_info("Undo", "Nothing to undo.")
            return

        try:
            undo_actions = self.undo_stack.pop()

            for new_path, old_path in undo_actions:
                try:
                    os.rename(new_path, old_path)
                except OSError as e:
                    self.handle_error(f"Failed to undo rename for {new_path}", e)

            self.show_info("Undo", f"Undone {len(undo_actions)} renames successfully.")
            self.update_preview()
        except Exception as e:
            self.handle_error("Error undoing rename", e)

    def auto_detect_season_episode(self):
        try:
            files = self.get_files()
            if not files:
                self.show_info("Auto-Detect", "No files found in the selected directory.")
                return

            season_pattern = r'S(\d+)'
            episode_pattern = r'E(\d+)'

            seasons = []
            episodes = []

            for file in files:
                season_match = re.search(season_pattern, file, re.IGNORECASE)
                episode_match = re.search(episode_pattern, file, re.IGNORECASE)
                
                if season_match:
                    seasons.append(int(season_match.group(1)))
                if episode_match:
                    episodes.append(int(episode_match.group(1)))

            if seasons:
                self.season_number.set(f"{min(seasons):02d}")
            if episodes:
                self.start_episode.set(f"{min(episodes):02d}")
                self.end_episode.set(f"{max(episodes):02d}")

            self.update_preview()
        except Exception as e:
            self.handle_error("Error auto-detecting season and episode", e)

    def reset_fields(self):
        try:
            self.directory.set("")
            self.season_number.set("01")
            self.start_episode.set("01")
            self.end_episode.set("")
            self.file_extensions.set(".mp4,.mkv,.avi")
            self.preview_text.delete(1.0, tk.END)
        except Exception as e:
            self.handle_error("Error resetting fields", e)

    def validate_inputs(self):
        try:
            if not self.directory.get():
                raise ValueError("Please select a directory.")
            if not self.season_number.get().isdigit():
                raise ValueError("Season number must be a positive integer.")
            if not self.start_episode.get().isdigit():
                raise ValueError("Start episode must be a positive integer.")
            if self.end_episode.get() and not self.end_episode.get().isdigit():
                raise ValueError("End episode must be a positive integer.")
            
            # Validate file extensions
            extensions = self.file_extensions.get().split(',')
            if not all(ext.strip().startswith('.') for ext in extensions):
                raise ValueError("All file extensions must start with a dot (.)")
            
            return True
        except ValueError as e:
            self.show_error(str(e))
            return False

    @debounce(0.5)
    def update_preview(self, *args):
        if not self.validate_inputs():
            return
        try:
            files = self.get_files()
            self.update_preview_text(files)
        except Exception as e:
            self.handle_error("Error updating preview", e)

    def handle_error(self, message, exception):
        logging.error(f"{message}: {exception}")
        self.show_error(f"{message}: {exception}")

    def show_error(self, message):
        messagebox.showerror("Error", message)

    def show_info(self, title, message):
        messagebox.showinfo(title, message)

if __name__ == "__main__":
    root = tk.Tk()
    app = TVShowRenamer(root)
    root.mainloop()
