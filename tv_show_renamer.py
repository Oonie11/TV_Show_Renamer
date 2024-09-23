import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json

class TVShowRenamer:
    def __init__(self, master):
        self.master = master
        master.title("TV Show File Renamer")
        master.geometry("600x600")

        self.directory = tk.StringVar()
        self.season_number = tk.StringVar(value="01")
        self.start_episode = tk.StringVar(value="01")
        self.end_episode = tk.StringVar(value="")
        self.file_extensions = tk.StringVar(value=".mp4,.mkv,.avi")

        self.undo_stack = []

        self.create_widgets()
        self.load_settings()

    def create_widgets(self):
        # Directory selection
        tk.Label(self.master, text="Directory:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(self.master, textvariable=self.directory, width=50).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(self.master, text="Browse", command=self.browse_directory).grid(row=0, column=2, padx=5, pady=5)

        # Season number
        tk.Label(self.master, text="Season Number:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(self.master, textvariable=self.season_number, width=10).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Start episode
        tk.Label(self.master, text="Start Episode:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(self.master, textvariable=self.start_episode, width=10).grid(row=2, column=1, sticky="w", padx=5, pady=5)

        # End episode
        tk.Label(self.master, text="End Episode:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(self.master, textvariable=self.end_episode, width=10).grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # File extensions
        tk.Label(self.master, text="File Extensions:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(self.master, textvariable=self.file_extensions, width=20).grid(row=4, column=1, sticky="w", padx=5, pady=5)

        # Buttons
        tk.Button(self.master, text="Preview Rename", command=self.preview_rename).grid(row=5, column=0, pady=10)
        tk.Button(self.master, text="Rename Files", command=self.rename_files).grid(row=5, column=1, pady=10)
        tk.Button(self.master, text="Undo Last Rename", command=self.undo_rename).grid(row=5, column=2, pady=10)
        tk.Button(self.master, text="Save Settings", command=self.save_settings).grid(row=6, column=0, pady=10)
        tk.Button(self.master, text="Reset", command=self.reset_fields).grid(row=6, column=1, pady=10)

        # Preview area
        self.preview_area = tk.Text(self.master, height=15, width=70)
        self.preview_area.grid(row=7, column=0, columnspan=3, padx=5, pady=5)

        # Progress bar
        self.progress = ttk.Progressbar(self.master, length=400, mode='determinate')
        self.progress.grid(row=8, column=0, columnspan=3, padx=5, pady=5)

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

        self.progress['value'] = 0
        messagebox.showinfo("Success", "Files have been renamed!")

    def undo_rename(self):
        if not self.undo_stack:
            messagebox.showinfo("Undo", "Nothing to undo!")
            return

        last_rename = self.undo_stack.pop()
        total_files = len(last_rename)
        self.progress['maximum'] = total_files
        self.progress['value'] = 0

        for new_path, old_path in last_rename:
            try:
                os.rename(new_path, old_path)
                print(f"Undone: {new_path} -> {old_path}")
            except Exception as e:
                print(f"Error undoing rename of {new_path}: {str(e)}")

            self.progress['value'] += 1
            self.master.update_idletasks()

        self.progress['value'] = 0
        messagebox.showinfo("Undo", "Last rename operation has been undone!")

    def save_settings(self):
        settings = {
            'directory': self.directory.get(),
            'season_number': self.season_number.get(),
            'start_episode': self.start_episode.get(),
            'end_episode': self.end_episode.get(),
            'file_extensions': self.file_extensions.get()
        }
        with open('renamer_settings.json', 'w') as f:
            json.dump(settings, f)
        messagebox.showinfo("Settings Saved", "Your settings have been saved.")

    def load_settings(self):
        try:
            with open('renamer_settings.json', 'r') as f:
                settings = json.load(f)
            self.directory.set(settings.get('directory', ''))
            self.season_number.set(settings.get('season_number', '01'))
            self.start_episode.set(settings.get('start_episode', '01'))
            self.end_episode.set(settings.get('end_episode', ''))
            self.file_extensions.set(settings.get('file_extensions', '.mp4,.mkv,.avi'))
        except FileNotFoundError:
            pass  # It's okay if the settings file doesn't exist yet

    def reset_fields(self):
        self.directory.set('')
        self.season_number.set('01')
        self.start_episode.set('01')
        self.end_episode.set('')
        self.file_extensions.set('.mp4,.mkv,.avi')
        self.preview_area.delete(1.0, tk.END)
        messagebox.showinfo("Reset", "All fields have been reset to default values.")

    def validate_inputs(self):
        try:
            int(self.season_number.get())
            int(self.start_episode.get())
            if self.end_episode.get():
                int(self.end_episode.get())
            return True
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for season and episodes.")
            return False

if __name__ == "__main__":
    root = tk.Tk()
    app = TVShowRenamer(root)
    root.mainloop()
