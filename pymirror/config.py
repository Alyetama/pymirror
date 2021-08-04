from pathlib import Path


class Config:
    PROJECT_PATH = f'{Path(__file__).parent}'
    UBLOCK = f'{PROJECT_PATH}/ublock_latest.xpi'
    DATA = f'{PROJECT_PATH}/data/servers_data.json'
    LOG_FILE = 'pymirror.log'
    WIN_GECKO = None
