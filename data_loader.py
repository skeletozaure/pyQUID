import os
import tempfile
import logging
from config_loader import ConfigLoader
from ftp_client import FTPClient
from cache_handler import CacheHandler

class DataLoader:
    def __init__(self, config_path, environment, use_cache=True):
        self.config_loader = ConfigLoader(config_path)
        self.environment = environment.upper()
        self.env_config = self.config_loader.get_environment_config(self.environment)
        self.ftp_credentials = self.config_loader.get_ftp_credentials()
        self.cache_handler = CacheHandler(self.config_loader.config.get('CacheDirectory', 'cache'))
        self.use_cache = use_cache
        self.docsp_data = []
        self.docfic_data = []

    def gas_split_by_length(self, lengths, line):
        """Divise une ligne en champs basés sur des longueurs fixes."""
        return [line[i:i+length].strip() for i, length in zip(self._cumulative_indices(lengths), lengths)]

    def _cumulative_indices(self, lengths):
        """Génère les indices de début pour chaque segment."""
        index = 0
        for length in lengths:
            yield index
            index += length

    def load_docsp(self):
        docsp_path = self.env_config.get('DOCSP')
        if not docsp_path:
            logging.error(f"DOCSP path not found for environment {self.environment}")
            return

        filename = os.path.basename(docsp_path)
        if self.use_cache and self.cache_handler.is_cached(filename):
            try:
                content = self.cache_handler.load_from_cache(filename)
            except Exception:
                logging.error("Failed to load DOCSP from cache. Attempting to download.")
                content = self._download_and_cache_file(docsp_path, filename)
        else:
            content = self._download_and_cache_file(docsp_path, filename)

        if content is None:
            logging.error("No content loaded for DOCSP.")
            return

        # Traitement des données DOCSP
        lengths = [8, 3, 10, 10, 10, 10, 10, 10, 10]  # Adapter selon les longueurs réelles des champs
        for line in content.splitlines():
            if line.strip():
                elements = self.gas_split_by_length(lengths, line)
                if elements[0]:
                    record = {
                        'NOMPROG': elements[0],
                        'SEQU': elements[1],
                        'NOMSP': elements[2]
                    }
                    self.docsp_data.append(record)
        logging.info(f"Loaded DOCSP data: {len(self.docsp_data)} records.")

    def load_docfic(self):
        docfic_path = self.env_config.get('DOCFIC')
        if not docfic_path:
            logging.error(f"DOCFIC path not found for environment {self.environment}")
            return

        filename = os.path.basename(docfic_path)
        if self.use_cache and self.cache_handler.is_cached(filename):
            try:
                content = self.cache_handler.load_from_cache(filename)
            except Exception:
                logging.error("Failed to load DOCFIC from cache. Attempting to download.")
                content = self._download_and_cache_file(docfic_path, filename)
        else:
            content = self._download_and_cache_file(docfic_path, filename)

        if content is None:
            logging.error("No content loaded for DOCFIC.")
            return

        # Traitement des données DOCFIC
        lengths = [8, 3, 10, 10, 10, 10, 30]  # Adapter selon les longueurs réelles des champs
        for line in content.splitlines():
            if line.strip():
                elements = self.gas_split_by_length(lengths, line)
                if elements[0]:
                    record = {
                        'NOMPROG': elements[0],
                        'SEQU': elements[1],
                        'NOMFIC': elements[2],
                        'TYPOPEN': elements[3],
                        'NUMOPEN': elements[4]
                    }
                    self.docfic_data.append(record)
        logging.info(f"Loaded DOCFIC data: {len(self.docfic_data)} records.")

    def _download_and_cache_file(self, remote_path, filename):
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            temp_file_path = tmp_file.name

        ftp_client = FTPClient(
            self.ftp_credentials['address'],
            self.ftp_credentials['user'],
            self.ftp_credentials['password']
        )

        try:
            ftp_client.connect()
            ftp_client.download_file(remote_path, temp_file_path)
        except Exception as e:
            logging.error(f"Failed to download {remote_path}: {e}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return None
        finally:
            ftp_client.disconnect()

        try:
            with open(temp_file_path, 'r') as f:
                content = f.read()
            self.cache_handler.save_to_cache(filename, content)
            return content
        except Exception as e:
            logging.error(f"Error processing downloaded file {filename}: {e}")
            return None
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def load_data(self):
        self.load_docsp()
        self.load_docfic()
