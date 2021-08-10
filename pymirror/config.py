from pathlib import Path


class Config:
    PROJECT_PATH = f'{Path(__file__).parent}'
    UBLOCK = f'{PROJECT_PATH}/ublock_latest.xpi'
    DATA_PATH = f'{PROJECT_PATH}/data'
    LOG_FILE = 'pymirror.log'
    WIN_GECKO = None
