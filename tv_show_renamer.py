import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
import re
from functools import lru_cache
from threading import Timer
import logging
from typing import List, Tuple, Dict, Optional
import mimetypes

# Set up logging
logging.basicConfig(filename='tv_show_renamer.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def debounce(wait: float):
    """ Decorator that will postpone a function's execution until after wait seconds
        have elapsed since the last time it was invoked. 
        
        Args:
            wait (float): Time to wait in seconds before executing the function
    """
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
    """A GUI application for renaming TV show files with consistent naming patterns."""
    
    def __init__(self, master: tk.Tk):
        """Initialize the TV Show Renamer application.
        
        Args:
            master (tk.Tk): The root window of the application
        """
        self.master = master
        master.title("TV Show File Renamer")
        master.geometry("800x800")
        
        # Make the window resizable
        master.resizable(True, True)
        
        self.configure_styles()

        # Initialize variables
        self.directory = tk.StringVar()
        self.season_number = tk.StringVar(value="01")
        self.start_episode = tk.StringVar(value="01")
        self.end_episode = tk.StringVar(value="")
        self.file_extensions = tk.StringVar(value=".mp4,.mkv,.avi")

        self.previous_directory = None  # Track the previous directory
        self.undo_stack: List[List[Tuple[str, str]]] = []
        self.selected_files: Dict[str, tk.BooleanVar] = {}
        
        # Create progress bar (hidden by default)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = None
        
        self.create_widgets()

    def configure_styles(self):
        """Configure the visual styles for the application."""
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
            
            # Configure widget styles
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
            self.style.configure('TButton', 
                               background=colors["PRIMARY_COLOR"], 
                               foreground=colors["SURFACE_COLOR"], 
                               font=('Segoe UI', 11, 'bold'),
                               borderwidth=0,
                               padding=(10, 5))
            self.style.configure('Horizontal.TProgressbar',
                               background=colors["PRIMARY_COLOR"],
                               troughcolor=colors["BACKGROUND_COLOR"])
            
            # Configure widget states
            self.style.map('TEntry', 
                          fieldbackground=[('readonly', colors["SURFACE_COLOR"])])
            self.style.map('TButton', 
                          background=[('active', colors["SECONDARY_COLOR"])])
            
        except Exception as e:
            self.handle_error("Error configuring styles", e)

    def create_widgets(self):
        """Create and arrange all GUI widgets."""
        try:
            # Create main frame
            main_frame = ttk.Frame(self.master, padding="50 50 50 50", style='TFrame')
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            self.master.columnconfigure(0, weight=1)
            self.master.rowconfigure(0, weight=1)

            # Configure main_frame to be expandable
            main_frame.columnconfigure(1, weight=1)
            main_frame.rowconfigure(7, weight=1)

            # Directory selection
            ttk.Label(main_frame, text="Directory:").grid(row=0, column=0, sticky="w", padx=5, pady=10)
            entry_frame = ttk.Frame(main_frame, style='TFrame')
            entry_frame.grid(row=0, column=1, padx=5, pady=10, sticky="we")
            entry_frame.columnconfigure(0, weight=1)
            self.dir_entry = tk.Entry(entry_frame, textvariable=self.directory, 
                                    font=('Segoe UI', 11), bd=1, relief=tk.SOLID)
            self.dir_entry.grid(row=0, column=0, sticky="we", ipady=5, ipadx=5)
            ttk.Button(main_frame, text="Browse", command=self.browse_directory).grid(row=0, column=2, padx=(10,0), pady=10)

            # Season number
            ttk.Label(main_frame, text="Season Number:").grid(row=1, column=0, sticky="w", padx=5, pady=10)
            self.season_entry = tk.Entry(main_frame, textvariable=self.season_number, width=10, 
                                       font=('Segoe UI', 11), bd=1, relief=tk.SOLID)
            self.season_entry.grid(row=1, column=1, sticky="w", padx=5, pady=10, ipady=5, ipadx=5)

            # Episode range
            ttk.Label(main_frame, text="Start Episode:").grid(row=2, column=0, sticky="w", padx=5, pady=10)
            self.start_ep_entry = tk.Entry(main_frame, textvariable=self.start_episode, width=10, 
                                         font=('Segoe UI', 11), bd=1, relief=tk.SOLID)
            self.start_ep_entry.grid(row=2, column=1, sticky="w", padx=5, pady=10, ipady=5, ipadx=5)

            ttk.Label(main_frame, text="End Episode:").grid(row=3, column=0, sticky="w", padx=5, pady=10)
            self.end_ep_entry = tk.Entry(main_frame, textvariable=self.end_episode, width=10, 
                                       font=('Segoe UI', 11), bd=1, relief=tk.SOLID)
            self.end_ep_entry.grid(row=3, column=1, sticky="w", padx=5, pady=10, ipady=5, ipadx=5)

            # File extensions
            ttk.Label(main_frame, text="File Extensions:").grid(row=4, column=0, sticky="w", padx=5, pady=10)
            self.ext_entry = tk.Entry(main_frame, textvariable=self.file_extensions, width=30, 
                                    font=('Segoe UI', 11), bd=1, relief=tk.SOLID)
            self.ext_entry.grid(row=4, column=1, sticky="w", padx=5, pady=10, ipady=5, ipadx=5)

            # Buttons
            button_frame = ttk.Frame(main_frame, style='TFrame')
            button_frame.grid(row=6, column=0, columnspan=3, pady=20)
            ttk.Button(button_frame, text="Preview", command=self.preview_rename).grid(row=0, column=0, padx=5)
            ttk.Button(button_frame, text="Rename", command=self.rename_files).grid(row=0, column=1, padx=5)
            ttk.Button(button_frame, text="Undo", command=self.undo_rename).grid(row=0, column=2, padx=5)
            ttk.Button(button_frame, text="Reset", command=self.reset_fields).grid(row=0, column=3, padx=5)

            # Progress bar
            self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var,
                                              maximum=100, mode='determinate')
            self.progress_bar.grid(row=7, column=0, columnspan=3, sticky="ew", pady=10)
            self.progress_bar.grid_remove()  # Hide initially

            # Preview area
            preview_frame = ttk.Frame(main_frame, style='TFrame')
            preview_frame.grid(row=8, column=0, columnspan=3, sticky="nsew", pady=20)
            preview_frame.columnconfigure(0, weight=1)
            preview_frame.rowconfigure(2, weight=1)

            ttk.Label(preview_frame, text="File Names Preview", font=('Segoe UI', 11, 'bold')).grid(row=0, column=0, pady=(0, 5))

            self.select_all_var = tk.BooleanVar(value=True)
            select_all_checkbox = tk.Checkbutton(preview_frame, text="Select All", 
                                               variable=self.select_all_var, 
                                               command=self.toggle_select_all)
            select_all_checkbox.grid(row=1, column=0, sticky="w", padx=5)

            # Preview frame with scrollbars
            self.preview_frame_inner = ttk.Frame(preview_frame, style='TFrame')
            self.preview_frame_inner.grid(row=2, column=0, sticky="nsew")
            self.preview_frame_inner.columnconfigure(0, weight=1)
            self.preview_frame_inner.rowconfigure(0, weight=1)

            # Scrollbars
            preview_v_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical")
            preview_v_scrollbar.grid(row=2, column=1, sticky="ns")

            preview_h_scrollbar = ttk.Scrollbar(preview_frame, orient="horizontal")
            preview_h_scrollbar.grid(row=3, column=0, sticky="ew")

            # Canvas configuration
            self.preview_canvas = tk.Canvas(self.preview_frame_inner,
                                          yscrollcommand=preview_v_scrollbar.set,
                                          xscrollcommand=preview_h_scrollbar.set,
                                          height=300)
            self.preview_canvas.grid(row=0, column=0, sticky="nsew")

            # Content frame
            self.preview_content_frame = ttk.Frame(self.preview_canvas, style='TFrame')
            self.preview_canvas.create_window((0, 0), window=self.preview_content_frame,
                                           anchor="nw", tags="preview_content")

            # Configure scrollbars
            preview_v_scrollbar.config(command=self.preview_canvas.yview)
            preview_h_scrollbar.config(command=self.preview_canvas.xview)

            # Bind events
            self.preview_content_frame.bind("<Configure>", self.on_frame_configure)
            self.preview_canvas.bind("<Configure>", self.on_canvas_configure)
            self.preview_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

            # Bind input fields to preview update
            for widget in (self.dir_entry, self.season_entry, self.start_ep_entry, 
                         self.end_ep_entry, self.ext_entry):
                widget.bind('<KeyRelease>', self.update_preview)

        except Exception as e:
            self.handle_error("Error creating widgets", e)

    def validate_file_type(self, filename: str) -> bool:
        """Validate if the file extension matches user-specified extensions.
        
        Args:
            filename (str): The name of the file to validate
            
        Returns:
            bool: True if file extension matches specified extensions, False otherwise
        """
        try:
            # Get file extension (including the dot)
            ext = os.path.splitext(filename)[1].lower()
            
            # Get user-specified extensions and normalize them
            allowed_extensions = [
                ext.strip().lower() if ext.strip().startswith('.') else f'.{ext.strip().lower()}'
                for ext in self.file_extensions.get().split(',')
            ]
            
            # Return True only if the extension matches one of the specified extensions
            return ext in allowed_extensions
            
        except Exception:
            return False

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        self.preview_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the inner frame"""
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """Handle canvas resize events."""
        self.preview_canvas.itemconfig("preview_content", width=event.width)
        self.preview_content_frame.configure(width=event.width)
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))

    def browse_directory(self):
        """Open directory selection dialog and update the directory path."""
        try:
            directory = filedialog.askdirectory()
            if directory:
                if not os.path.isdir(directory):
                    raise NotADirectoryError(f"Selected path is not a directory: {directory}")
                self.directory.set(directory)
                self.get_files.cache_clear()
                self.update_preview()
        except Exception as e:
            self.handle_error("Error browsing directory", e)

    def preview_rename(self):
        """Generate preview of renamed files."""
        try:
            self.clear_preview()
            files = self.get_files()
            if not files:
                self.show_info("No Files", "No matching files found in the selected directory.")
                return

            # Sort files to ensure consistent ordering
            files.sort()
            
            # Get episode range
            start_ep = int(self.start_episode.get() or 1)
            end_ep = int(self.end_episode.get() or (start_ep + len(files) - 1))
            
            if end_ep < start_ep:
                self.show_error("Invalid Episode Range", 
                              "End episode number must be greater than or equal to start episode.")
                return

            # Clear existing checkboxes
            self.selected_files.clear()

            # Create preview entries
            for i, old_name in enumerate(files):
                ep_num = start_ep + i
                if ep_num > end_ep:
                    break

                new_name = self.generate_new_filename(old_name, ep_num)
                
                # Create a frame for each file
                file_frame = ttk.Frame(self.preview_content_frame)
                file_frame.grid(row=i, column=0, sticky="ew", pady=2)
                file_frame.columnconfigure(1, weight=1)
                file_frame.columnconfigure(2, weight=1)

                # Add checkbox
                self.selected_files[old_name] = tk.BooleanVar(value=True)
                checkbox = tk.Checkbutton(file_frame, variable=self.selected_files[old_name])
                checkbox.grid(row=0, column=0, padx=(5,10))

                # Add old and new filenames
                ttk.Label(file_frame, text=old_name).grid(row=0, column=1, sticky="w", padx=5)
                ttk.Label(file_frame, text="→").grid(row=0, column=2, padx=5)
                ttk.Label(file_frame, text=new_name).grid(row=0, column=3, sticky="w", padx=5)

        except ValueError as ve:
            self.show_error("Invalid Input", str(ve))
        except Exception as e:
            self.handle_error("Error generating preview", e)

    def rename_files(self):
        """Rename the selected files according to the preview."""
        try:
            if not self.directory.get() or not os.path.isdir(self.directory.get()):
                self.show_error("Invalid Directory", "Please select a valid directory.")
                return

            files_to_rename = []
            total_files = 0
            renamed_count = 0

            # Get episode range
            start_ep = int(self.start_episode.get() or 1)
            
            # Collect files to rename
            for i, old_name in enumerate(self.selected_files.keys()):
                if self.selected_files[old_name].get():
                    ep_num = start_ep + i
                    new_name = self.generate_new_filename(old_name, ep_num)
                    files_to_rename.append((old_name, new_name))
                    total_files += 1

            if not files_to_rename:
                self.show_info("No Files Selected", "Please select files to rename.")
                return

            # Show progress bar
            self.progress_bar.grid()
            self.progress_var.set(0)

            # Perform renaming
            renamed_files = []
            for old_name, new_name in files_to_rename:
                try:
                    old_path = os.path.join(self.directory.get(), old_name)
                    new_path = os.path.join(self.directory.get(), new_name)
                    
                    # Check if destination file already exists
                    if os.path.exists(new_path):
                        raise FileExistsError(f"File already exists: {new_name}")
                    
                    os.rename(old_path, new_path)
                    renamed_files.append((old_name, new_name))
                    renamed_count += 1
                    
                    # Update progress
                    progress = (renamed_count / total_files) * 100
                    self.progress_var.set(progress)
                    self.master.update_idletasks()
                    
                except Exception as e:
                    self.show_error("Rename Error", f"Error renaming {old_name}: {str(e)}")
                    # Continue with remaining files

            # Add to undo stack if any files were renamed
            if renamed_files:
                self.undo_stack.append(renamed_files)

            # Hide progress bar
            self.progress_bar.grid_remove()
            self.progress_var.set(0)

            # Show completion message
            self.show_info("Rename Complete", 
                         f"Successfully renamed {renamed_count} out of {total_files} files.")
            
            # Clear preview and cache
            self.clear_preview()
            self.get_files.cache_clear()
            self.preview_rename()

        except ValueError as ve:
            self.show_error("Invalid Input", str(ve))
        except Exception as e:
            self.handle_error("Error renaming files", e)
            self.progress_bar.grid_remove()

    def undo_rename(self):
        """Undo the last rename operation."""
        try:
            if not self.undo_stack:
                self.show_info("Nothing to Undo", "No rename operations to undo.")
                return

            # Get the last rename operation
            renamed_files = self.undo_stack[-1]
            total_files = len(renamed_files)
            restored_count = 0

            # Show progress bar
            self.progress_bar.grid()
            self.progress_var.set(0)

            # Perform undo
            for old_name, new_name in renamed_files:
                try:
                    current_path = os.path.join(self.directory.get(), new_name)
                    original_path = os.path.join(self.directory.get(), old_name)
                    
                    # Check if original filename is available
                    if os.path.exists(original_path):
                        raise FileExistsError(f"Cannot restore original filename: {old_name}")
                    
                    os.rename(current_path, original_path)
                    restored_count += 1
                    
                    # Update progress
                    progress = (restored_count / total_files) * 100
                    self.progress_var.set(progress)
                    self.master.update_idletasks()
                    
                except Exception as e:
                    self.show_error("Undo Error", f"Error restoring {new_name}: {str(e)}")
                    # Continue with remaining files

            # Remove the operation from undo stack
            self.undo_stack.pop()

            # Hide progress bar
            self.progress_bar.grid_remove()
            self.progress_var.set(0)

            # Show completion message
            self.show_info("Undo Complete", 
                         f"Successfully restored {restored_count} out of {total_files} files.")
            
            # Refresh preview
            self.get_files.cache_clear()
            self.preview_rename()

        except Exception as e:
            self.handle_error("Error undoing rename", e)
            self.progress_bar.grid_remove()

    def reset_fields(self):
        """Reset all input fields to their default values."""
        try:
            self.directory.set("")
            self.season_number.set("01")
            self.start_episode.set("01")
            self.end_episode.set("")
            self.file_extensions.set(".mp4,.mkv,.avi")
            self.clear_preview()
            self.get_files.cache_clear()
        except Exception as e:
            self.handle_error("Error resetting fields", e)

    def clear_preview(self):
        """Clear the preview area."""
        for widget in self.preview_content_frame.winfo_children():
            widget.destroy()
        self.selected_files.clear()

    def toggle_select_all(self):
        """Toggle selection state of all files."""
        try:
            select_all = self.select_all_var.get()
            for var in self.selected_files.values():
                var.set(select_all)
        except Exception as e:
            self.handle_error("Error toggling selection", e)

    @debounce(0.5)
    def update_preview(self, event=None):
        """Update the preview when input fields change."""
        # Clear the file cache if extension field changes
        if event and event.widget == self.ext_entry:
            self.get_files.cache_clear()
        self.preview_rename()


    @lru_cache(maxsize=1)
    def get_files(self) -> List[str]:
        """Get list of valid files in the selected directory."""
        try:
            if not self.directory.get() or not os.path.isdir(self.directory.get()):
                return []

            files = []
            for filename in os.listdir(self.directory.get()):
                if os.path.isfile(os.path.join(self.directory.get(), filename)) and \
                   self.validate_file_type(filename):
                    files.append(filename)
            return files
        except Exception as e:
            self.handle_error("Error getting files", e)
            return []

    def generate_new_filename(self, old_name: str, episode_number: int) -> str:
        """Generate new filename based on season and episode numbers."""
        try:
            # Get file extension
            ext = os.path.splitext(old_name)[1]
            
            # Format season and episode numbers
            season = str(int(self.season_number.get())).zfill(2)
            episode = str(episode_number).zfill(2)
            
            # Generate new name
            return f"S{season}E{episode}{ext}"
            
        except ValueError as ve:
            raise ValueError("Invalid season or episode number")
        except Exception as e:
            raise Exception(f"Error generating filename: {str(e)}")

    def show_error(self, title: str, message: str):
        """Show error message dialog."""
        messagebox.showerror(title, message)
        logging.error(f"{title}: {message}")

    def show_info(self, title: str, message: str):
        """Show information message dialog."""
        messagebox.showinfo(title, message)

    def handle_error(self, context: str, error: Exception):
        """Handle and log errors."""
        message = f"{context}: {str(error)}"
        logging.error(message)
        self.show_error("Error", message)

def main():
    """Main entry point of the application."""
    try:
        root = tk.Tk()
        app = TVShowRenamer(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        messagebox.showerror("Fatal Error", f"Application failed to start: {str(e)}")

if __name__ == "__main__":
    main()

