#!/usr/bin/env python3
# coding: utf-8

import json
import requests
import sys
from pathlib import Path

import speedtest


def config():
    home = Path.home()
    CONFIG_DIR = f'{home}/.pymirror/.config'
    if not Path(CONFIG_DIR).exists() or '--refresh-config' in sys.argv:
        print('Configuring pymirror...')
        Path(f'{CONFIG_DIR}/.addons').mkdir(exist_ok=True, parents=True)
        Path(f'{CONFIG_DIR}/data').mkdir(exist_ok=True, parents=True)

        cfg = {
            'project_path': CONFIG_DIR,
            'ublock': f'{CONFIG_DIR}/.addons/ublock_latest.xpi',
            'data_path': f'{CONFIG_DIR}/data',
            'log_file': f'{CONFIG_DIR}/pymirror.log',
            'win_gecko': None,
            'upload_speed': speedtest.Speedtest().upload() / 8e+6
        }

        with open(f'{CONFIG_DIR}/.config', 'w') as j:
            json.dump(cfg, j, indent=4)

        with open(f'{CONFIG_DIR}/data/more_links.json', 'w') as j:
            r = requests.get(
                'https://raw.githubusercontent.com/Alyetama/pymirror/main/pymirror/data/more_links.json'
            )  # noqa E501
            j.write(r.text)

        with open(f'{CONFIG_DIR}/data/servers_data.json', 'w') as j:
            r = requests.get(
                'https://raw.githubusercontent.com/Alyetama/pymirror/main/pymirror/data/servers_data.json'
            )  # noqa E501
            j.write(r.text)

    else:
        with open(f'{CONFIG_DIR}/.config') as j:
            cfg = json.load(j)
    return cfg
