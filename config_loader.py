import json

class ConfigLoader:
    def __init__(self, config_file):
        self.config = self.load_config(config_file)
    
    def load_config(self, config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def get_environment_config(self, environment):
        return self.config['Environments'].get(environment.upper(), {})
    
    def get_ftp_credentials(self):
        return {
            'address': self.config['TDMAddress'],
            'user': self.config['FTPUser'],
            'password': self.config['FTPPassword']
        }
    
