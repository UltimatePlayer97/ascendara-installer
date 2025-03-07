import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import AscendaraInstaller

if __name__ == "__main__":
    app = AscendaraInstaller()
    app.mainloop()