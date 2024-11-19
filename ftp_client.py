import ftplib
import os
import logging

class FTPClient:
    def __init__(self, address, user, password):
        self.address = address
        self.user = user
        self.password = password
        self.ftp = None

    def connect(self):
        try:
            self.ftp = ftplib.FTP(self.address)
            self.ftp.login(self.user, self.password)
            self.ftp.set_pasv(True)  # Activer le mode passif
            self.ftp.sendcmd('TYPE A')  # Définir le type de transfert sur ASCII
            logging.info(f"Connected to FTP server: {self.address} in ASCII mode and PASV.")
        except ftplib.all_errors as e:
            logging.error(f"FTP connection error: {e}")
            raise

    def download_file(self, remote_path, local_path):
        try:
            with open(local_path, 'w') as f:  # Ouvrir le fichier en mode écriture texte
                def callback(line):
                    f.write(line + '\n')  # Écrire chaque ligne avec un saut de ligne
                self.ftp.retrlines(f"RETR {remote_path}", callback)
            logging.info(f"Downloaded {remote_path} to {local_path} in ASCII mode.")
        except ftplib.all_errors as e:
            logging.error(f"FTP download error: {e}")
            raise

    def disconnect(self):
        if self.ftp:
            try:
                self.ftp.quit()
                logging.info("FTP connection closed.")
            except ftplib.all_errors as e:
                logging.warning(f"Error closing FTP connection: {e}")
