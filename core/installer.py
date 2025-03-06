import tempfile
import subprocess
import os
import logging
import threading
from .downloader import Downloader

class InstallerProcess:
    def __init__(self, progress_callback=None, status_callback=None, completion_callback=None):
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.completion_callback = completion_callback
        self.downloader = Downloader(progress_callback, status_callback)

    def start(self):
        thread = threading.Thread(target=self._installation_process)
        thread.daemon = True
        thread.start()

    def _installation_process(self):
        try:
            url = "https://lfs.ascendara.app/download"
            download_path = tempfile.gettempdir() + "/AscendaraInstaller.exe"
            
            try:
                local_file = self.downloader.download_file(url, str(download_path))
            except Exception as e:
                logging.error(f"Failed to download from primary server: {str(e)}")
                if self.status_callback:
                    self.status_callback("Primary download failed. Trying GitHub releases...")
                
                try:
                    github_url = self.downloader.get_latest_github_release()
                    local_file = self.downloader.download_file(github_url, str(download_path))
                except Exception as e:
                    logging.error(f"Failed to download from GitHub: {str(e)}")
                    if self.status_callback:
                        self.status_callback("Download failed. Please try again later.")
                    if self.completion_callback:
                        self.completion_callback(False)
                    return
            
            if not os.path.exists(local_file) or os.path.getsize(local_file) == 0:
                raise Exception("Download verification failed")
            
            process = subprocess.Popen([str(download_path)], shell=True)
            
            while True:
                if process.poll() is not None:
                    if self.progress_callback:
                        self.progress_callback(1.0)
                    if self.status_callback:
                        self.status_callback("Installation complete!")
                    if self.completion_callback:
                        self.completion_callback(True)
                    break
        
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Installation error: {error_msg}")
            if self.status_callback:
                self.status_callback(f"Error: {error_msg}")
            if self.completion_callback:
                self.completion_callback(False)