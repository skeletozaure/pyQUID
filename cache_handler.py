import os
import logging

class CacheHandler:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        logging.info(f"Cache directory set to: {self.cache_dir}")

    def get_cached_file_path(self, filename):
        return os.path.join(self.cache_dir, filename)

    def is_cached(self, filename):
        file_path = self.get_cached_file_path(filename)
        exists = os.path.isfile(file_path)
        logging.info(f"Cache check for {filename}: {'Found' if exists else 'Not Found'}")
        return exists

    def save_to_cache(self, filename, data):
        file_path = self.get_cached_file_path(filename)
        try:
            with open(file_path, 'w', encoding='ascii') as f:
                f.write(data)
            logging.info(f"Saved {filename} to cache.")
        except Exception as e:
            logging.error(f"Failed to save {filename} to cache: {e}")
            raise

    def load_from_cache(self, filename):
        file_path = self.get_cached_file_path(filename)
        try:
            with open(file_path, 'r', encoding='ascii') as f:
                data = f.read()
            logging.info(f"Loaded {filename} from cache.")
            return data
        except Exception as e:
            logging.error(f"Failed to load {filename} from cache: {e}")
            raise
