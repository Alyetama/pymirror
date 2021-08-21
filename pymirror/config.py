#!/usr/bin/env python3
# coding: utf-8

from pathlib import Path


class Config:
    PROJECT_PATH = f'{Path(__file__).parent}'
    UBLOCK = f'{PROJECT_PATH}/.addons/ublock_latest.xpi'
    DATA_PATH = f'{PROJECT_PATH}/data'
    LOG_FILE = 'pymirror.log'
    WIN_GECKO = None
