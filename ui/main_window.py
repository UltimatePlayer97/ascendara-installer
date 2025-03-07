import customtkinter as ctk
import logging
import os
from PIL import Image
from io import BytesIO
import requests
from core.installer import InstallerProcess
from core.version import version
from utils.logging import setup_logging
from ui.log_window import LogWindow

class AscendaraInstaller(ctk.CTk):
    def __init__(self):
        # Set up logging first
        setup_logging()
        logging.info("Initializing AscendaraInstaller...")
        
        # Initialize the window
        super().__init__()
        
        # Initialize state
        self.log_window = None
        self.current_progress = 0
        
        # Configure window
        logging.info("Setting up window...")
        self._setup_window()
        self._create_title_bar()
        self._create_main_content()
        self._create_log_button()
        self._load_logo()
        self._create_title_and_subtitle()
        self._create_progress_elements()
        
        logging.info(f"Installer Version {version}")
        
        # Make window visible first, then start fade in
        self.update_idletasks()  # Ensure window is ready
        self.deiconify()  # Make sure window is shown
        self.lift()  # Bring to front
        
        # Start installation after fade in
        self.after(100, self.start_fade_in)
        
    def start_fade_in(self):
        """Start the fade in sequence and schedule installation"""
        self.attributes('-alpha', 0.0)
        self.fade_in(completion_callback=self.on_fade_in_complete)
        
    def on_fade_in_complete(self):
        """Called when fade in is complete"""
        logging.info("Window fade in complete, starting installation...")
        self.after(500, self.start_installation)

    def _setup_window(self):
        logging.info("Configuring window properties...")
        self.title("Ascendara Installer")
        self.geometry("900x600")
        self.resizable(False, False)
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        
        # Center window
        x = (self.winfo_screenwidth() - 900) // 2
        y = (self.winfo_screenheight() - 600) // 2
        self.geometry(f"900x600+{x}+{y}")
        logging.info(f"Window positioned at x={x}, y={y}")
        
        if os.name == 'nt':
            self.after(10, lambda: self.attributes('-toolwindow', True))
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        logging.info("Window setup complete")

    def _create_title_bar(self):
        logging.info("Creating title bar...")
        self.main_frame = ctk.CTkFrame(self, fg_color="#ede9fe", corner_radius=0)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        self.title_bar = ctk.CTkFrame(self.main_frame, fg_color="#9333EA", height=20, corner_radius=0)
        self.title_bar.grid(row=0, column=0, sticky="ew")
        self.title_bar.grid_columnconfigure(0, weight=1)
        
        self.window_title = ctk.CTkLabel(
            self.title_bar,
            text="Ascendara Installer",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="white"
        )
        self.window_title.grid(row=0, column=0, padx=8, pady=2, sticky="w")
        
        self.controls_frame = ctk.CTkFrame(self.title_bar, fg_color="transparent")
        self.controls_frame.grid(row=0, column=1, padx=4, pady=2)
        
        self.close_button = ctk.CTkButton(
            self.controls_frame,
            text="✕",
            width=32,
            height=20,
            fg_color="transparent",
            text_color="white",
            hover_color="#dc2626",
            command=self.close
        )
        self.close_button.grid(row=0, column=1, padx=2)
        logging.info("Title bar created")

    def _create_main_content(self):
        logging.info("Creating main content...")
        self.content_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent",
            width=900,
            height=580
        )
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        
        self.inner_content_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color="transparent",
            width=900,
            height=580
        )
        self.inner_content_frame.place(relx=0.5, rely=0.5, anchor="center")
        logging.info("Main content created")

    def _create_log_button(self):
        logging.info("Creating log button...")
        self.log_button = ctk.CTkButton(
            self.inner_content_frame,
            text="Show Logs",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#9333EA",
            hover_color="#7C3AED",
            width=80,
            height=28,
            corner_radius=14,
            command=self.toggle_log_panel
        )
        self.log_button.place(relx=0.96, rely=0.05, anchor="ne")
        logging.info("Log button created")

    def _load_logo(self):
        logging.info("Loading logo...")
        logo_url = "https://raw.githubusercontent.com/Ascendara/ascendara/refs/heads/main/src/public/icon.png"
        try:
            response = requests.get(logo_url)
            if response.status_code == 200:
                logo_image = Image.open(BytesIO(response.content))
                logo_image = logo_image.resize((130, 130), Image.Resampling.LANCZOS)
                self.logo_photo = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(130, 130))
                self.logo_label = ctk.CTkLabel(
                    self.inner_content_frame,
                    text="",
                    image=self.logo_photo,
                    width=130,
                    height=130
                )
                self.logo_label.place(relx=0.5, rely=0.25, anchor="center")
                logging.info("Logo loaded")
            else:
                self._create_fallback_logo()
        except:
            self._create_fallback_logo()

    def _create_fallback_logo(self):
        logging.info("Creating fallback logo...")
        self.logo_frame = ctk.CTkFrame(
            self.inner_content_frame,
            width=120,
            height=120,
            corner_radius=60,
            fg_color="#9333EA"
        )
        self.logo_frame.place(relx=0.5, rely=0.30, anchor="center")
        
        self.logo_inner = ctk.CTkFrame(
            self.logo_frame,
            width=100,
            height=100,
            corner_radius=50,
            fg_color="#7C3AED"
        )
        self.logo_inner.place(relx=0.5, rely=0.5, anchor="center")
        logging.info("Fallback logo created")

    def _create_title_and_subtitle(self):
        logging.info("Creating title and subtitle...")
        self.title_label = ctk.CTkLabel(
            self.inner_content_frame,
            text="Install Ascendara",
            font=ctk.CTkFont(family="Segoe UI", size=72, weight="bold"),
            text_color="#581c87"
        )
        self.title_label.place(relx=0.5, rely=0.45, anchor="center")
        
        try:
            response = requests.get("https://api.ascendara.app/")
            if response.status_code == 200:
                data = response.json()
                appVer = data["appVer"]
                responseText = f"Install Ascendara version {appVer} onto your computer.\nThis should take less than a minute."
            else:
                responseText = "Install the latest version of Ascendara onto your computer"
        except:
            responseText = "Install the latest version of Ascendara onto your computer"
        
        self.subtitle = ctk.CTkLabel(
            self.inner_content_frame,
            text=responseText,
            font=ctk.CTkFont(family="Segoe UI", size=20),
            text_color="#581c87"
        )
        self.subtitle.place(relx=0.5, rely=0.57, anchor="center")
        logging.info("Title and subtitle created")

    def _create_progress_elements(self):
        logging.info("Creating progress elements...")
        self.progress_bar = ctk.CTkProgressBar(
            self.inner_content_frame,
            width=320,
            height=16,
            corner_radius=8,
            fg_color="#E9D5FF",
            progress_color="#9333EA",
            mode="determinate"  # Start in determinate mode
        )
        self.progress_bar.place(relx=0.5, rely=0.80, anchor="center")
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(
            self.inner_content_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=18),
            text_color="#581c87"
        )
        self.status_label.place(relx=0.5, rely=0.85, anchor="center")
        logging.info("Progress elements created")

    def fade_in(self, current_alpha=0.0, completion_callback=None):
        if current_alpha < 1.0:
            current_alpha += 0.1
            self.attributes('-alpha', current_alpha)
            self.after(20, lambda: self.fade_in(current_alpha, completion_callback))
            logging.info(f"Fading in window: {current_alpha:.1f}")
        elif completion_callback:
            completion_callback()

    def fade_out(self, current_alpha=1.0, on_complete=None):
        if current_alpha > 0:
            current_alpha -= 0.1
            self.attributes('-alpha', current_alpha)
            self.after(20, lambda: self.fade_out(current_alpha, on_complete))
        elif on_complete:
            on_complete()

    def close(self):
        if self.log_window and self.log_window.winfo_exists():
            self.log_window.close()
        self.fade_out(on_complete=self.quit)

    def toggle_log_panel(self):
        if self.log_window is None or not self.log_window.winfo_exists():
            self.log_window = LogWindow()
            self.log_window.focus()
            self.log_button.configure(text="Close Console")
        else:
            self.log_window.close()
            self.log_window = None
            self.log_button.configure(text="Open Console")

    def update_progress(self, progress):
        if progress is None:
            # Switch to indeterminate mode for unknown progress
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
        else:
            # Switch back to determinate mode for known progress
            if self.progress_bar.cget("mode") == "indeterminate":
                self.progress_bar.stop()
                self.progress_bar.configure(mode="determinate")
            # Progress comes in as percentage (0-100), normalize to 0-1 for progress bar
            normalized_progress = min(progress / 100, 1.0)
            self.progress_bar.set(normalized_progress)

    def start_installation(self):
        installer = InstallerProcess(
            progress_callback=self.update_progress,
            status_callback=lambda text: self.status_label.configure(text=text),
            completion_callback=lambda success: self.after(2000, self.close) if success else None
        )
        installer.start()

if __name__ == "__main__":
    app = AscendaraInstaller()
    app.mainloop()