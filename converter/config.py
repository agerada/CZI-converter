# converter/config.py
import yaml
from pathlib import Path

class Config:
    def __init__(self, config_path='config.yaml'):
        self.config_path = Path(config_path)
        self.load_config()

    def load_config(self):
        if not self.config_path.is_file():
            raise FileNotFoundError(f"Configuration file {self.config_path} not found.")
        with open(self.config_path, 'r') as file:
            config = yaml.safe_load(file)

        self.INPUT_FOLDER = Path(config['INPUT_FOLDER'])
        self.OUTPUT_FOLDER = Path(config['OUTPUT_FOLDER'])
        self.PROCESSED_FILES_RECORD = Path(config['PROCESSED_FILES_RECORD'])
        self.CHECK_INTERVAL_SECONDS = config.get('CHECK_INTERVAL_SECONDS', 10)
        self.LOG_FILE = Path(config.get('LOG_FILE', 'logs/conversion_automation.log'))
        self.RUN_ONCE = config.get('RUN_ONCE', True)
        self.OUTPUT_TILE_SIZE = config.get('OUTPUT_TILE_SIZE', 2048)
        self.OUTPUT_TILE_FORMAT = config.get('OUTPUT_TILE_FORMAT', 'tif')
