#!/usr/bin/env python3
# coding: utf-8

import configparser
import uuid
from pathlib import Path

import speedtest


class _MyConfigParser(configparser.ConfigParser):
    def __init__(self, *args, **kwargs) -> None:
        super(_MyConfigParser, self).__init__(*args, **kwargs)

    def write2(self, file_name) -> None:
        with open(file_name, 'w') as cf:
            self.write(cf)


class _Dict(dict):
    def __init__(self, *args, **kwargs) -> None:
        super(_Dict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class _Config:
    def __init__(self, file_name: str = 'config.ini') -> None:
        self.file_name = file_name
        self.config = _MyConfigParser(allow_no_value=True)
        self.project_path = str(Path(__file__).parent)

    def __call__(self) -> _MyConfigParser:
        if not Path(self.file_name).exists():
            print('Creating a config file...')
            config = self.create_config()
            config.write2(self.file_name)
        else:
            config = self.read()
        if (
                config['main']['upload_speed'] == '' or
                config['main']['uuid'] != str(uuid.getnode())  # noqa
        ):
            uspeed = self.upload_speed()
            config['main']['upload_speed'] = str(uspeed)
            config.write2(self.file_name)
        return config

    def read(self):
        conf = self.config
        conf.read(self.file_name)
        return conf

    def create_config(self) -> _MyConfigParser:
        self.config.add_section('main')
        conf = self.config['main']
        conf['project_path'] = self.project_path
        conf['ublock'] = f'{self.project_path}/.addons/ublock_latest.xpi'
        conf['data_path'] = f'{self.project_path}/data'
        conf['log_file'] = 'pymirror.log'
        conf['win_gecko'] = ''
        conf['uuid'] = str(uuid.getnode())
        conf['upload_speed'] = ''
        return self.config

    def get_dict(self) -> _Dict:
        self.config.read(self.file_name)
        config_dict = dict(self.config['main'].items())
        return _Dict(config_dict)

    @staticmethod
    def upload_speed():
        st = speedtest.Speedtest()
        speed = st.upload()
        return speed / 8e+6


_Config().__call__()
_config = _Config().get_dict()
Config = _config
