import requests
import logging
import os
import time
from requests.adapters import HTTPAdapter, Retry

class Downloader:
    def __init__(self, progress_callback=None, status_callback=None):
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        
    def download_file(self, url, local_filename):
        try:
            session = requests.Session()
            session.headers.update({
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'User-Agent': 'Ascendara-Installer'
            })
            
            retry_strategy = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

            with session.get(url, stream=True, timeout=30) as r:
                if r.status_code != 200:
                    logging.error(f"Server response: {r.text}")
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                
                if self.progress_callback:
                    self.progress_callback(0.25)  # Initial setup phase
                
                with open(local_filename, 'wb', buffering=8*1024*1024) as f:
                    if total_size == 0:
                        f.write(r.content)
                    else:
                        downloaded = 0
                        for chunk in r.iter_content(chunk_size=8*1024*1024):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if self.progress_callback:
                                    progress = (downloaded / total_size * 74) + 25
                                    progress = min(progress * 1.5, 99)
                                    self.progress_callback(progress / 100)
                
                if self.progress_callback:
                    self.progress_callback(1.0)
                if self.status_callback:
                    self.status_callback("Installing... 100%")
                return local_filename
                
        except Exception as e:
            logging.error(f"Download error: {str(e)}")
            if os.path.exists(local_filename):
                try:
                    os.remove(local_filename)
                except:
                    pass
            raise e

    def get_latest_github_release(self):
        try:
            api_url = "https://api.github.com/repos/ascendara/Ascendara/releases/latest"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for asset in data['assets']:
                if asset['name'].lower().endswith('.exe'):
                    return asset['browser_download_url']
            
            raise Exception("No installer found in latest release")
        except Exception as e:
            logging.error(f"Failed to get latest release: {str(e)}")
            raise