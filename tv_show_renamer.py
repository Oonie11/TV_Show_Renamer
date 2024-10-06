import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import re

class ModernStyle:
    # Light theme colors
    LIGHT_PRIMARY_COLOR = "#3498db"
    LIGHT_SECONDARY_COLOR = "#2980b9"
    LIGHT_BACKGROUND_COLOR = "#f5f5f5"
    LIGHT_SURFACE_COLOR = "#ffffff"
    LIGHT_TEXT_COLOR = "#34495e"
    LIGHT_ACCENT_COLOR = "#e74c3c"
    LIGHT_BORDER_COLOR = "#bdc3c7"

    # Dark theme colors
    DARK_PRIMARY_COLOR = "#3498db"
    DARK_SECONDARY_COLOR = "#2980b9"
    DARK_BACKGROUND_COLOR = "#2c3e50"
    DARK_SURFACE_COLOR = "#34495e"
    DARK_TEXT_COLOR = "#ecf0f1"
    DARK_ACCENT_COLOR = "#e74c3c"
    DARK_BORDER_COLOR = "#7f8c8d"

    # Current theme (start with light theme)
    PRIMARY_COLOR = LIGHT_PRIMARY_COLOR
    SECONDARY_COLOR = LIGHT_SECONDARY_COLOR
    BACKGROUND_COLOR = LIGHT_BACKGROUND_COLOR
    SURFACE_COLOR = LIGHT_SURFACE_COLOR
    TEXT_COLOR = LIGHT_TEXT_COLOR
    ACCENT_COLOR = LIGHT_ACCENT_COLOR
    BORDER_COLOR = LIGHT_BORDER_COLOR

class TVShowRenamer:
    def __init__(self, master):
        self.master = master
        master.title("TV Show File Renamer")
        master.geometry("750x800")
        master.configure(bg=ModernStyle.BACKGROUND_COLOR)

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.directory = tk.StringVar()
        self.season_number = tk.StringVar(value="01")
        self.start_episode = tk.StringVar(value="01")
        self.end_episode = tk.StringVar(value="")
        self.file_extensions = tk.StringVar(value=".mp4,.mkv,.avi")

        self.undo_stack = []

        self.is_dark_theme = False
        self.configure_styles()
        self.create_widgets()
        self.load_settings()

    def configure_styles(self):
        self.style.configure('TFrame', background=ModernStyle.BACKGROUND_COLOR)
        self.style.configure('TLabel', 
                             background=ModernStyle.BACKGROUND_COLOR, 
                             foreground=ModernStyle.TEXT_COLOR, 
                             font=('Segoe UI', 11))
        
        self.style.configure('TEntry', 
                             fieldbackground=ModernStyle.SURFACE_COLOR, 
                             foreground=ModernStyle.TEXT_COLOR, 
                             font=('Segoe UI', 11),
                             borderwidth=0)
        self.style.map('TEntry', 
                       fieldbackground=[('focus', ModernStyle.SURFACE_COLOR)],
                       bordercolor=[('focus', ModernStyle.PRIMARY_COLOR)])
        
        self.style.configure('TButton', 
                             background=ModernStyle.PRIMARY_COLOR, 
                             foreground=ModernStyle.SURFACE_COLOR, 
                             font=('Segoe UI', 11, 'bold'),
                             borderwidth=0,
                             padding=10)
        self.style.map('TButton', 
                       background=[('active', ModernStyle.SECONDARY_COLOR)],
                       relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        
        self.style.configure('TProgressbar', 
                             background=ModernStyle.PRIMARY_COLOR, 
                             troughcolor=ModernStyle.SURFACE_COLOR,
                             borderwidth=0,
                             thickness=10)

    def create_widgets(self):
        main_frame = ttk.Frame(self.master, padding="40 40 40 40", style='TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        # Directory selection
        ttk.Label(main_frame, text="Directory:").grid(row=0, column=0, sticky="w", padx=5, pady=10)
        entry_frame = ttk.Frame(main_frame, style='TFrame')
        entry_frame.grid(row=0, column=1, padx=5, pady=10, sticky="we")
        entry_frame.columnconfigure(0, weight=1)
        self.dir_entry = tk.Entry(entry_frame, textvariable=self.directory, width=50, 
                 font=('Segoe UI', 11), bd=0, relief=tk.FLAT,
                 bg=ModernStyle.SURFACE_COLOR, fg=ModernStyle.TEXT_COLOR)
        self.dir_entry.grid(row=0, column=0, sticky="we", ipady=5, ipadx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_directory).grid(row=0, column=2, padx=(10,0), pady=10)

        # Season number
        ttk.Label(main_frame, text="Season Number:").grid(row=1, column=0, sticky="w", padx=5, pady=10)
        self.season_entry = tk.Entry(main_frame, textvariable=self.season_number, width=10, 
                 font=('Segoe UI', 11), bd=0, relief=tk.FLAT,
                 bg=ModernStyle.SURFACE_COLOR, fg=ModernStyle.TEXT_COLOR)
        self.season_entry.grid(row=1, column=1, sticky="w", padx=5, pady=10, ipady=5, ipadx=5)

        # Start episode
        ttk.Label(main_frame, text="Start Episode:").grid(row=2, column=0, sticky="w", padx=5, pady=10)
        self.start_ep_entry = tk.Entry(main_frame, textvariable=self.start_episode, width=10, 
                 font=('Segoe UI', 11), bd=0, relief=tk.FLAT,
                 bg=ModernStyle.SURFACE_COLOR, fg=ModernStyle.TEXT_COLOR)
        self.start_ep_entry.grid(row=2, column=1, sticky="w", padx=5, pady=10, ipady=5, ipadx=5)

        # End episode
        ttk.Label(main_frame, text="End Episode:").grid(row=3, column=0, sticky="w", padx=5, pady=10)
        self.end_ep_entry = tk.Entry(main_frame, textvariable=self.end_episode, width=10, 
                 font=('Segoe UI', 11), bd=0, relief=tk.FLAT,
                 bg=ModernStyle.SURFACE_COLOR, fg=ModernStyle.TEXT_COLOR)
        self.end_ep_entry.grid(row=3, column=1, sticky="w", padx=5, pady=10, ipady=5, ipadx=5)

        # File extensions
        ttk.Label(main_frame, text="File Extensions:").grid(row=4, column=0, sticky="w", padx=5, pady=10)
        self.ext_entry = tk.Entry(main_frame, textvariable=self.file_extensions, width=20, 
                 font=('Segoe UI', 11), bd=0, relief=tk.FLAT,
                 bg=ModernStyle.SURFACE_COLOR, fg=ModernStyle.TEXT_COLOR)
        self.ext_entry.grid(row=4, column=1, sticky="w", padx=5, pady=10, ipady=5, ipadx=5)

        # Buttons
        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        for i, (text, command) in enumerate([
            ("Preview Rename", self.preview_rename),
            ("Rename Files", self.rename_files),
            ("Undo Last Rename", self.undo_rename),
            ("Save Settings", self.save_settings),
            ("Reset", self.reset_fields),
            ("Toggle Theme", self.toggle_theme),
            ("Auto-Detect", self.auto_detect_season_episode)  # New button
        ]):
            btn = ttk.Button(button_frame, text=text, command=command)
            btn.grid(row=i//3, column=i%3, padx=5, pady=5)
            btn.bind("<Enter>", lambda e, btn=btn: btn.configure(cursor="hand2"))
            btn.bind("<Leave>", lambda e, btn=btn: btn.configure(cursor=""))

        # Preview area
        preview_frame = ttk.Frame(main_frame, style='TFrame', padding="10")
        preview_frame.grid(row=6, column=0, columnspan=3, padx=5, pady=10, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.preview_area = tk.Text(preview_frame, height=15, width=70, 
                                    bg=ModernStyle.SURFACE_COLOR, 
                                    fg=ModernStyle.TEXT_COLOR, 
                                    font=('Consolas', 10),
                                    relief=tk.FLAT, padx=10, pady=10,
                                    wrap=tk.NONE)
        self.preview_area.grid(row=0, column=0, sticky="nsew")

        # Custom scrollbars for preview area
        y_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_area.yview)
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.preview_area.xview)
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        self.preview_area.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=400, mode='determinate', style='TProgressbar')
        self.progress.grid(row=7, column=0, columnspan=3, padx=5, pady=10, sticky="ew")

        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        if self.is_dark_theme:
            ModernStyle.PRIMARY_COLOR = ModernStyle.DARK_PRIMARY_COLOR
            ModernStyle.SECONDARY_COLOR = ModernStyle.DARK_SECONDARY_COLOR
            ModernStyle.BACKGROUND_COLOR = ModernStyle.DARK_BACKGROUND_COLOR
            ModernStyle.SURFACE_COLOR = ModernStyle.DARK_SURFACE_COLOR
            ModernStyle.TEXT_COLOR = ModernStyle.DARK_TEXT_COLOR
            ModernStyle.ACCENT_COLOR = ModernStyle.DARK_ACCENT_COLOR
            ModernStyle.BORDER_COLOR = ModernStyle.DARK_BORDER_COLOR
        else:
            ModernStyle.PRIMARY_COLOR = ModernStyle.LIGHT_PRIMARY_COLOR
            ModernStyle.SECONDARY_COLOR = ModernStyle.LIGHT_SECONDARY_COLOR
            ModernStyle.BACKGROUND_COLOR = ModernStyle.LIGHT_BACKGROUND_COLOR
            ModernStyle.SURFACE_COLOR = ModernStyle.LIGHT_SURFACE_COLOR
            ModernStyle.TEXT_COLOR = ModernStyle.LIGHT_TEXT_COLOR
            ModernStyle.ACCENT_COLOR = ModernStyle.LIGHT_ACCENT_COLOR
            ModernStyle.BORDER_COLOR = ModernStyle.LIGHT_BORDER_COLOR

        self.configure_styles()
        self.update_widget_colors()

    def update_widget_colors(self):
        self.master.configure(bg=ModernStyle.BACKGROUND_COLOR)
        for widget in [self.dir_entry, self.season_entry, self.start_ep_entry, self.end_ep_entry, self.ext_entry]:
            widget.configure(bg=ModernStyle.SURFACE_COLOR, fg=ModernStyle.TEXT_COLOR)
        self.preview_area.configure(bg=ModernStyle.SURFACE_COLOR, fg=ModernStyle.TEXT_COLOR)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory.set(directory)

    def get_files(self):
        directory = self.directory.get()
        extensions = self.file_extensions.get().split(',')
        return [file for file in sorted(os.listdir(directory)) if any(file.endswith(ext.strip()) for ext in extensions)]

    def preview_rename(self):
        if not self.validate_inputs():
            return

        files = self.get_files()
        season = self.season_number.get().zfill(2)
        start = int(self.start_episode.get())
        end = int(self.end_episode.get()) if self.end_episode.get() else start + len(files) - 1

        self.preview_area.delete(1.0, tk.END)
        for i, file in enumerate(files[:end-start+1], start=start):
            _, ext = os.path.splitext(file)
            new_name = f"S{season}E{str(i).zfill(2)}{ext}"
            self.preview_area.insert(tk.END, f"{file} -> {new_name}\n")

    def rename_files(self):
        if not self.validate_inputs():
            return

        files = self.get_files()
        season = self.season_number.get().zfill(2)
        start = int(self.start_episode.get())
        end = int(self.end_episode.get()) if self.end_episode.get() else start + len(files) - 1

        self.undo_stack.append([])  # New undo level

        directory = self.directory.get()
        total_files = min(len(files), end - start + 1)
        self.progress['maximum'] = total_files
        self.progress['value'] = 0

        for i, file in enumerate(files[:end-start+1], start=start):
            _, ext = os.path.splitext(file)
            new_name = f"S{season}E{str(i).zfill(2)}{ext}"
            old_path = os.path.join(directory, file)
            new_path = os.path.join(directory, new_name)
            
            try:
                os.rename(old_path, new_path)
                self.undo_stack[-1].append((new_path, old_path))  # Store for undo
                print(f"Renamed: {file} -> {new_name}")
            except Exception as e:
                print(f"Error renaming {file}: {str(e)}")
            
            self.progress['value'] += 1
            self.master.update_idletasks()

        messagebox.showinfo("Rename Complete", f"Successfully renamed {total_files} files.")
        self.progress['value'] = 0

    def undo_rename(self):
        if not self.undo_stack:
            messagebox.showinfo("Undo", "Nothing to undo.")
            return

        last_rename = self.undo_stack.pop()
        total_files = len(last_rename)
        self.progress['maximum'] = total_files
        self.progress['value'] = 0

        for new_path, old_path in last_rename:
            try:
                os.rename(new_path, old_path)
                print(f"Undone: {os.path.basename(new_path)} -> {os.path.basename(old_path)}")
            except Exception as e:
                print(f"Error undoing rename of {os.path.basename(new_path)}: {str(e)}")
            
            self.progress['value'] += 1
            self.master.update_idletasks()

        messagebox.showinfo("Undo Complete", f"Successfully undone {total_files} renames.")
        self.progress['value'] = 0

    def save_settings(self):
        settings = {
            "directory": self.directory.get(),
            "season_number": self.season_number.get(),
            "start_episode": self.start_episode.get(),
            "end_episode": self.end_episode.get(),
            "file_extensions": self.file_extensions.get(),
            "is_dark_theme": self.is_dark_theme
        }
        with open("settings.json", "w") as f:
            json.dump(settings, f)
        messagebox.showinfo("Settings Saved", "Your settings have been saved.")

    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
            self.directory.set(settings.get("directory", ""))
            self.season_number.set(settings.get("season_number", "01"))
            self.start_episode.set(settings.get("start_episode", "01"))
            self.end_episode.set(settings.get("end_episode", ""))
            self.file_extensions.set(settings.get("file_extensions", ".mp4,.mkv,.avi"))
            self.is_dark_theme = settings.get("is_dark_theme", False)
            if self.is_dark_theme:
                self.toggle_theme()
        except FileNotFoundError:
            pass  # No settings file found, use defaults

    def reset_fields(self):
        self.directory.set("")
        self.season_number.set("01")
        self.start_episode.set("01")
        self.end_episode.set("")
        self.file_extensions.set(".mp4,.mkv,.avi")

    def validate_inputs(self):
        if not self.directory.get():
            messagebox.showerror("Error", "Please select a directory.")
            return False
        if not self.season_number.get().isdigit():
            messagebox.showerror("Error", "Season number must be a positive integer.")
            return False
        if not self.start_episode.get().isdigit():
            messagebox.showerror("Error", "Start episode must be a positive integer.")
            return False
        if self.end_episode.get() and not self.end_episode.get().isdigit():
            messagebox.showerror("Error", "End episode must be a positive integer.")
            return False
        return True

    def auto_detect_season_episode(self):
        directory = self.directory.get()
        if not directory:
            messagebox.showerror("Error", "Please select a directory first.")
            return

        files = self.get_files()
        if not files:
            messagebox.showerror("Error", "No matching files found in the selected directory.")
            return

        season_pattern = r'[Ss](\d{1,2})'
        episode_pattern = r'[Ee](\d{1,3})'

        seasons = []
        episodes = []

        for file in files:
            season_match = re.search(season_pattern, file)
            episode_match = re.search(episode_pattern, file)

            if season_match:
                seasons.append(int(season_match.group(1)))
            if episode_match:
                episodes.append(int(episode_match.group(1)))

        if seasons:
            most_common_season = max(set(seasons), key=seasons.count)
            self.season_number.set(str(most_common_season).zfill(2))

        if episodes:
            min_episode = min(episodes)
            max_episode = max(episodes)
            self.start_episode.set(str(min_episode).zfill(2))
            self.end_episode.set(str(max_episode).zfill(2))

        if seasons or episodes:
            messagebox.showinfo("Auto-Detect", "Season and episode numbers have been automatically detected.")
        else:
            messagebox.showwarning("Auto-Detect", "Could not detect season or episode numbers from the file names.")

if __name__ == "__main__":
    root = tk.Tk()
    app = TVShowRenamer(root)
    
    # Apply some final touches to the root window
    root.option_add("*Font", "Segoe UI 11")
    root.option_add("*Background", ModernStyle.BACKGROUND_COLOR)
    root.option_add("*Foreground", ModernStyle.TEXT_COLOR)

    # Center the window on the screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    root.mainloop()
