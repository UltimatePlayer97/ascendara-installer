import customtkinter as ctk
from utils.logging import log_stream

class LogWindow(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Ascendara Installer Logs")
        self.geometry("800x400")
        self.minsize(600, 300)
        self.attributes('-alpha', 0.0)
        
        # Match main window theme
        self.configure(fg_color="#0f172a")
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=0)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Add log text area
        self.log_text = ctk.CTkTextbox(
            self.main_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#1e1b4b",
            text_color="#e2e8f0",
            corner_radius=8,
            wrap="none"
        )
        self.log_text.pack(fill="both", expand=True)
        
        # Add clear button
        self.clear_button = ctk.CTkButton(
            self.main_frame,
            text="Clear Logs",
            font=ctk.CTkFont(size=14),
            fg_color="#4f46e5",
            hover_color="#4338ca",
            height=32,
            command=self.clear_logs
        )
        self.clear_button.pack(pady=(10, 0))
        
        self.update_logs()
        self.fade_in()
    
    def fade_in(self, current_alpha=0.0):
        if current_alpha < 1.0:
            current_alpha += 0.1
            self.attributes('-alpha', current_alpha)
            self.after(20, lambda: self.fade_in(current_alpha))
    
    def fade_out(self, current_alpha=1.0, on_complete=None):
        if current_alpha > 0:
            current_alpha -= 0.1
            self.attributes('-alpha', current_alpha)
            self.after(20, lambda: self.fade_out(current_alpha, on_complete))
        elif on_complete:
            on_complete()
    
    def close(self):
        self.fade_out(on_complete=self.destroy)
    
    def clear_logs(self):
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.configure(state="disabled")
    
    def update_logs(self):
        log_content = log_stream.getvalue()
        
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.insert("1.0", log_content)
        self.log_text.configure(state="disabled")
        self.log_text.see("end")
        
        self.after(100, self.update_logs)