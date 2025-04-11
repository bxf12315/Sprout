import threading
from joblib import Memory
import joblib
from sprout.config import Config
import os
import time
import shutil


class ExpiringMemory:
    def __init__(self, location, expiration_days=7, verbose=0):
        self.memory = Memory(location=location, verbose=verbose)
        self.location = location
        self.expiration_seconds = expiration_days * 24 * 60 * 60

    def cache(self, func):
        cached_func = self.memory.cache(func)

        def wrapper(*args, **kwargs):
            # Check if cache needs to be cleaned
            self._clean_expired_cache()
            return cached_func(*args, **kwargs)

        return wrapper

    def _clean_expired_cache(self):
        """Check and delete expired cache files"""

        def _clean():
            current_time = time.time()
            # Return immediately if the cache directory doesn't exist
            if not os.path.exists(os.path.expanduser(self.location)):
                print("cache directory doesn't exist")
                return

            for root, dirs, files in os.walk(os.path.expanduser(self.location)):

                for file in files:
                    file_path = os.path.expanduser(os.path.join(root, file))
                    print("Check and delete expired cache files = " + file_path)
                    # Get the last modification time of the file
                    file_mod_time = os.path.getmtime(file_path)
                    # Delete the file if it exceeds the expiration time
                    if current_time - file_mod_time > self.expiration_seconds:
                        os.remove(file_path)

                # Remove empty directories
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)

        # Start cleaning in a separate thread
        cleaning_thread = threading.Thread(target=_clean)

        cleaning_thread.start()

    def clear(self):
        """Completely clear the cache directory"""
        if os.path.exists(self.location):
            shutil.rmtree(self.location)
            os.makedirs(self.location, exist_ok=True)


memory = Memory(location=Config.CACHE_PATH, verbose=1)
# memory = ExpiringMemory(location=Config.CACHE_PATH, expiration_days=0.0001, verbose=3)


@memory.cache
def cached_loading(model_bytes, storage):

    return joblib.load(storage.download_model("health", model_bytes))
