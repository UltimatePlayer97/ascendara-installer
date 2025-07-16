import os
import logging
import threading
import time
import requests
from io import BytesIO
from PIL import Image
import customtkinter as ctk
from core.installer import InstallerProcess
from core.version import version

# Windows dark mode detection helper
def is_windows_dark_mode():
    try:
        import winreg
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        key = winreg.OpenKey(registry, key_path)
        # Value 1 means light mode, 0 means dark mode
        apps_use_light_theme, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return apps_use_light_theme == 0
    except Exception as e:
        logging.warning(f"Could not detect Windows dark mode: {e}")
        return False
        

# Detect Windows dark mode once before initializing CTk
windows_dark_mode = is_windows_dark_mode()
logging.info(f"Windows dark mode detected: {windows_dark_mode}")

if windows_dark_mode:
    ctk.set_appearance_mode("dark")
else:
    ctk.set_appearance_mode("light")

ctk.set_default_color_theme("blue")

class AscendaraInstaller(ctk.CTk):
    def __init__(self):
        """Initialize the main application window"""
        super().__init__()

        logging.info("Initializing main window")

        # Set color schemes for light and dark themes
        self.light_colors = {
            "bg_primary": "#F5F0FF",
            "bg_secondary": "#EBE4FF",
            "bg_tertiary": "#E0D6FF",
            "text_primary": "#6A3CB5",
            "text_secondary": "#8A6BF0",
            "accent": "#8A6BF0",
            "accent_hover": "#7A5BE0",
            "success": "#4CAF50",
            "error": "#F44336"
        }

        self.dark_colors = {
            "bg_primary": "#1E1E2F",
            "bg_secondary": "#2C2C3E",
            "bg_tertiary": "#3A3A4E",
            "text_primary": "#C0C0FF",
            "text_secondary": "#A0A0F0",
            "accent": "#8A6BF0",
            "accent_hover": "#7A5BE0",
            "success": "#4CAF50",
            "error": "#F44336"
        }

        # Choose colors based on detected mode
        self.colors = self.dark_colors if windows_dark_mode else self.light_colors

        # Set up animation properties
        self.frame_time = 1.0 / 60.0  # Target 60 FPS
        self.animation_running = False

        # Initialize log window reference
        self.log_window = None

        # Initialize installer reference
        self.installer = None

        # Track after callbacks
        self.after_ids = {}

        # Initialize variables
        self.x = 0
        self.y = 0
        self._indeterminate_active = False

        logging.info("Setting up window...")
        self._setup_window()

        logging.info("Creating UI...")
        self._create_ui()

        logging.info(f"Installer Version {version}")

        self._start_animation_loop()

        self.attributes('-alpha', 0.0)
        self.fade_in(completion_callback=self.on_fade_in_complete)
        
    def _setup_window(self):
        """Set up the main window properties"""
        logging.info("Configuring window properties...")
        self.title("Ascendara Installer")
        self.geometry("850x550")
        self.resizable(False, False)
        self.overrideredirect(True)  # Frameless window
        
        # Center window on screen
        x = (self.winfo_screenwidth() - 850) // 2
        y = (self.winfo_screenheight() - 550) // 2
        self.geometry(f"850x550+{x}+{y}")
        logging.info(f"Window positioned at x={x}, y={y}")
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
    def _create_ui(self):
        """Create the complete UI structure"""
        # Create main container
        self.main_frame = ctk.CTkFrame(
            self, 
            fg_color=self.colors["bg_primary"],
            corner_radius=0
        )
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Create title bar
        self._create_title_bar()
        
        # Create content area
        self._create_content_area()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_title_bar(self):
        """Create a custom title bar"""
        # Title bar container
        self.title_bar = ctk.CTkFrame(
            self.main_frame,
            fg_color=self.colors["bg_secondary"],
            height=40,
            corner_radius=0
        )
        self.title_bar.pack(fill="x")
        
        # Make the title bar draggable
        self.title_bar.bind("<Button-1>", self._start_window_move)
        self.title_bar.bind("<B1-Motion>", self._on_window_move)
        
        # Title
        self.window_title = ctk.CTkLabel(
            self.title_bar,
            text="Ascendara Installer",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        self.window_title.pack(side="left", padx=15, pady=10)
        
        # Window controls container
        self.controls_frame = ctk.CTkFrame(
            self.title_bar,
            fg_color="transparent"
        )
        self.controls_frame.pack(side="right", padx=10)
        
        # Log button
        self.log_button = ctk.CTkButton(
            self.controls_frame,
            text="📋",
            font=ctk.CTkFont(size=13),
            width=35,
            height=28,
            corner_radius=5,
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["accent"],
            text_color=self.colors["text_primary"],
            command=self._show_logs
        )
        self.log_button.pack(side="left", padx=5, pady=6)
        
        # Minimize button
        self.minimize_button = ctk.CTkButton(
            self.controls_frame,
            text="−",
            font=ctk.CTkFont(size=13),
            width=35,
            height=28,
            corner_radius=5,
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["accent"],
            text_color=self.colors["text_primary"],
            command=self.iconify
        )
        self.minimize_button.pack(side="left", padx=5, pady=6)
        
        # Close button
        self.close_button = ctk.CTkButton(
            self.controls_frame,
            text="×",
            font=ctk.CTkFont(size=13),
            width=35,
            height=28,
            corner_radius=5,
            fg_color="#F44336",
            hover_color="#D32F2F",
            text_color="#FFFFFF",
            command=self.close
        )
        self.close_button.pack(side="left", padx=5, pady=6)
    
    def _create_content_area(self):
        """Create the main content area"""
        # Content container
        self.content_area = ctk.CTkFrame(
            self.main_frame,
            fg_color=self.colors["bg_primary"],
            corner_radius=0
        )
        self.content_area.pack(fill="both", expand=True)
        
        # Create logo section
        self._create_logo_section()
        
        # Welcome section
        self._create_welcome_section()
        
        # Progress section
        self._create_progress_section()
        
        # Install button
        self.install_button = ctk.CTkButton(
            self.content_area,
            text="Install",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            width=150,
            height=40,
            corner_radius=10,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            text_color="#FFFFFF",
            command=self._on_install_click
        )
        self.install_button.pack(pady=(20, 0))
        
        # Exit button
        self.exit_button = ctk.CTkButton(
            self.content_area,
            text="Exit",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            width=150,
            height=40,
            corner_radius=10,
            fg_color=self.colors["bg_secondary"],
            hover_color=self.colors["bg_tertiary"],
            text_color=self.colors["text_primary"],
            command=self.close
        )
        self.exit_button.pack(pady=(10, 0))
    
    def _create_logo_section(self):
        """Create the logo section in the center top"""
        # Logo container
        self.logo_frame = ctk.CTkFrame(
            self.content_area,
            fg_color="transparent",
            height=150
        )
        self.logo_frame.pack(fill="x", pady=(30, 0))
        
        # Try to load logo from URL
        try:
            logo_url = "https://raw.githubusercontent.com/Ascendara/ascendara/refs/heads/main/src/public/icon.png"
            response = requests.get(logo_url)
            if response.status_code == 200:
                logo_image = Image.open(BytesIO(response.content))
                logo_image = logo_image.resize((100, 100), Image.Resampling.LANCZOS)
                self.logo_photo = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(100, 100))
                
                self.logo_label = ctk.CTkLabel(
                    self.logo_frame,
                    text="",
                    image=self.logo_photo
                )
                self.logo_label.pack(pady=10)
            else:
                self._create_fallback_logo()
        except Exception as e:
            logging.error(f"Error loading logo: {e}")
            self._create_fallback_logo()
    
    def _create_fallback_logo(self):
        """Create a fallback logo when image loading fails"""
        # Outer circle
        self.logo_outer = self._create_circle_image(100, self.colors["accent"])
        
        # Create label with the image
        self.logo_label = ctk.CTkLabel(
            self.logo_frame,
            text="A",
            font=ctk.CTkFont(family="Segoe UI", size=40, weight="bold"),
            text_color=self.colors["text_primary"],
            image=self.logo_outer,
            compound="center"
        )
        self.logo_label.pack(pady=10)
    
    def _create_welcome_section(self):
        """Create the welcome/header section"""
        # Welcome container
        self.welcome_frame = ctk.CTkFrame(
            self.content_area,
            fg_color="transparent"
        )
        self.welcome_frame.pack(fill="x", padx=60, pady=(10, 20))
        
        # Main title
        self.main_title = ctk.CTkLabel(
            self.welcome_frame,
            text="Welcome to Ascendara",
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        self.main_title.pack(anchor="center")
        
        # Subtitle
        try:
            response = requests.get("https://api.ascendara.app/")
            if response.status_code == 200:
                data = response.json()
                app_ver = data["appVer"]
                subtitle_text = f"Installing version {app_ver} on your computer"
            else:
                subtitle_text = "Installing the latest version on your computer"
        except:
            subtitle_text = "Installing the latest version on your computer"
        
        self.subtitle = ctk.CTkLabel(
            self.welcome_frame,
            text=subtitle_text,
            font=ctk.CTkFont(family="Segoe UI", size=16),
            text_color=self.colors["text_secondary"]
        )
        self.subtitle.pack(anchor="center", pady=(5, 0))
        
        # Description
        self.description = ctk.CTkLabel(
            self.welcome_frame,
            text="This process will take just a moment.\nThe application will launch automatically when installation is complete.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=self.colors["text_secondary"],
            justify="center"
        )
        self.description.pack(anchor="center", pady=(10, 0))
    
    def _create_progress_section(self):
        """Create the installation progress section"""
        # Progress container
        self.progress_frame = ctk.CTkFrame(
            self.content_area,
            fg_color=self.colors["bg_secondary"],
            corner_radius=15
        )
        self.progress_frame.pack(fill="x", padx=60, pady=20)
        
        # Progress header
        self.progress_header = ctk.CTkFrame(
            self.progress_frame,
            fg_color="transparent"
        )
        self.progress_header.pack(fill="x", padx=20, pady=(20, 10))
        
        # Progress title
        self.progress_title = ctk.CTkLabel(
            self.progress_header,
            text="Installation Progress",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        self.progress_title.pack(side="left")
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.progress_header,
            text="Preparing...",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=self.colors["text_secondary"]
        )
        self.status_label.pack(side="right")
        
        # Progress bar container
        self.progress_bar_frame = ctk.CTkFrame(
            self.progress_frame,
            fg_color="transparent"
        )
        self.progress_bar_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_bar_frame,
            width=600,
            height=15,
            corner_radius=7,
            fg_color=self.colors["bg_primary"],
            progress_color=self.colors["accent"],
            mode="determinate"
        )
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)
        
        # Progress details
        self.progress_details_frame = ctk.CTkFrame(
            self.progress_frame,
            fg_color="transparent"
        )
        self.progress_details_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Current task
        self.current_task = ctk.CTkLabel(
            self.progress_details_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.colors["text_secondary"]
        )
        self.current_task.pack(side="left")
        
        # Percentage
        self.percentage = ctk.CTkLabel(
            self.progress_details_frame,
            text="0%",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        self.percentage.pack(side="right")
    
    def _create_status_bar(self):
        """Create the status bar at the bottom"""
        # Status bar container
        self.status_bar = ctk.CTkFrame(
            self.main_frame,
            fg_color=self.colors["bg_secondary"],
            height=25,
            corner_radius=0
        )
        self.status_bar.pack(side="bottom", fill="x")
        
        # Status text
        self.status_text = ctk.CTkLabel(
            self.status_bar,
            text="Ready to install",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.colors["text_secondary"]
        )
        self.status_text.pack(side="left", padx=10, pady=2)
        
        # Copyright
        self.copyright = ctk.CTkLabel(
            self.status_bar,
            text=" 2025 Ascendara",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.colors["text_secondary"]
        )
        self.copyright.pack(side="right", padx=10, pady=2)
    
    def _start_animation_loop(self):
        """Start a high-performance animation loop running at 60 FPS"""
        self.animation_running = True
        animation_thread = threading.Thread(target=self._animation_loop)
        animation_thread.daemon = True
        animation_thread.start()
        logging.info("Animation loop started")
    
    def _animation_loop(self):
        """Main animation loop that runs at 60 FPS"""
        while self.animation_running:
            start_time = time.time()
            
            # Update UI on the main thread
            self.after(0, self._update_animation_frame)
            
            # Calculate time to sleep to maintain FPS
            elapsed = time.time() - start_time
            sleep_time = max(0, self.frame_time - elapsed)
            time.sleep(sleep_time)
    
    def _update_animation_frame(self):
        """Update a single frame of animation"""
        if hasattr(self, 'progress_bar') and self.progress_bar.cget("mode") == "indeterminate":
            # Only update the indeterminate progress if it's actually in that mode
            # This prevents conflicts with determinate progress updates
            if not hasattr(self, '_indeterminate_active') or self._indeterminate_active:
                # Get the current progress value
                current = self.progress_bar.get()
                
                # Create a smooth back-and-forth animation
                new_value = (current + 0.02) % 1.0
                self.progress_bar.set(new_value)
    
    def _create_circle_image(self, size, color):
        """Create a circular image of specified size and color"""
        # Create a blank image with alpha channel
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        
        # Get a drawing context
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        
        # Draw a filled circle
        draw.ellipse((0, 0, size, size), fill=color)
        
        # Convert to CTkImage
        return ctk.CTkImage(light_image=image, dark_image=image, size=(size, size))
    
    def _start_window_move(self, event):
        """Start window dragging"""
        self.x = event.x
        self.y = event.y
    
    def _on_window_move(self, event):
        """Handle window dragging"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")
    
    def _show_logs(self):
        """Show the log window"""
        if self.log_window is None or not self.log_window.winfo_exists():
            from core.log_window import LogWindow  # Import only when needed to avoid circular imports
            self.log_window = LogWindow(self)
        else:
            self.log_window.lift()
    
    def _on_install_click(self):
        """Handle the install button click"""
        if self.installer is not None and self.installer.is_running():
            logging.info("Installation already in progress")
            return
        
        logging.info("Starting installation process...")
        
        # Disable install button
        self.install_button.configure(state="disabled")
        self.status_text.configure(text="Installing...")
        
        self.progress_bar.configure(mode="indeterminate")
        self._indeterminate_active = True
        
        # Start installer process in a separate thread
        self.installer = InstallerProcess(self)
        installer_thread = threading.Thread(target=self.installer.run)
        installer_thread.daemon = True
        installer_thread.start()
    
    def update_progress(self, value, max_value, task_name=""):
        """Update the progress bar and labels"""
        self._indeterminate_active = False
        self.progress_bar.configure(mode="determinate")
        
        progress_percent = 0
        if max_value > 0:
            progress_percent = min(100, int((value / max_value) * 100))
        
        self.progress_bar.set(value / max_value if max_value > 0 else 0)
        self.percentage.configure(text=f"{progress_percent}%")
        self.current_task.configure(text=task_name)
        self.status_label.configure(text=f"{task_name}...")
    
    def on_fade_in_complete(self):
        logging.info("Fade-in complete, application ready.")
    
    def fade_in(self, completion_callback=None):
        """Fade in the window gradually"""
        alpha = self.attributes('-alpha')
        alpha += 0.05
        if alpha >= 1.0:
            self.attributes('-alpha', 1.0)
            if completion_callback:
                completion_callback()
        else:
            self.attributes('-alpha', alpha)
            self.after(30, lambda: self.fade_in(completion_callback))
    
    def close(self):
        """Close the application gracefully"""
        self.animation_running = False
        self.destroy()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = AscendaraInstaller()
    app.mainloop()
