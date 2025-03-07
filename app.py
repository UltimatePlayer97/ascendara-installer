import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import customtkinter as ctk
import logging
from ui.main_window import AscendaraInstaller
from utils.logging import setup_logging

# Set up logging
setup_logging()
logging.info("Application started")
logging.info("Initializing Ascendara Installer")

# Create and run the application
app = AscendaraInstaller()
logging.info("Application initialized, starting main loop")
app.mainloop()