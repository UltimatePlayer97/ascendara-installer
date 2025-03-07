import os
import requests
import logging
from typing import Optional, Dict
from pathlib import Path

class Downloader:
    """Class for handling file downloads with progress reporting"""
    
    def __init__(self, progress_callback=None, status_callback=None):
        """Initialize the downloader with optional callbacks"""
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        logging.info("Downloader initialized")
    
    def download_file(self, url: str, local_path: str, headers: Optional[Dict] = None) -> str:
        """
        Download a file from URL to local path with progress tracking
        
        Args:
            url: URL to download from
            local_path: Local path to save the file to
            headers: Optional headers to include in the request
            
        Returns:
            str: Path to the downloaded file
        """
        try:
            # Ensure download directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            logging.info(f"Downloading file from {url} to {local_path}")
            
            if self.status_callback:
                self.status_callback(f"Downloading {Path(local_path).name}...")
            
            # Chrome-like headers for better compatibility
            default_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            
            # Merge default headers with custom headers if provided
            if headers:
                default_headers.update(headers)
            
            # Stream the download with larger chunks and a generous timeout
            with requests.get(url, headers=default_headers, stream=True, timeout=30) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                
                # Use a large buffer for better performance
                with open(local_path, 'wb', buffering=1024*1024) as f:
                    if total_size == 0:
                        f.write(response.content)
                    else:
                        downloaded = 0
                        # Use larger chunks (1MB) for faster downloads
                        for chunk in response.iter_content(chunk_size=1024*1024):
                            if chunk:
                                downloaded += len(chunk)
                                f.write(chunk)
                                
                                # Calculate and report progress (capped at 100%)
                                if self.progress_callback and total_size:
                                    progress = min((downloaded / total_size) * 100, 100.0)
                                    logging.debug(f"Download progress: {progress:.1f}%")
                                    self.progress_callback(progress)
            
            logging.info(f"Download completed: {local_path}")
            return local_path
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Download failed: {str(e)}")
            if self.status_callback:
                self.status_callback(f"Download error: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error during download: {str(e)}")
            if self.status_callback:
                self.status_callback(f"Error: {str(e)}")
            raise

    def get_latest_github_release(self):
        try:
            # First try to get version from api.ascendara.app
            try:
                response = requests.get('https://api.ascendara.app', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'appVer' in data and data.get('status') == 'OK':
                        version = data['appVer']
                        return f'https://github.com/tagoWorks/ascendara/releases/download/{version}/Ascendara.Setup.{version}.exe'
            except:
                pass  # Silently fall back to GitHub API if this fails
            
            # Fallback to GitHub API
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json'
            }
            
            api_url = "https://api.github.com/repos/ascendara/Ascendara/releases/latest"
            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for asset in data['assets']:
                if asset['name'].lower().endswith('.exe'):
                    return asset['browser_download_url']
            
            raise Exception("No installer found in latest release")
        except Exception as e:
            logging.error(f"Failed to get latest release: {str(e)}")
            raise