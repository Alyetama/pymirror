#!/usr/bin/env python3
# coding: utf-8

import argparse
import json
import multiprocessing
import os
import shutil
import signal
import socket
import sys
import tarfile
import time
from pathlib import Path
from typing import Union, NoReturn

from dracula import DraculaPalette as Dp
from rich.panel import Panel

from .api_upload import APIUpload
from .config import Config
from .experimental.more_links import MoreLinks
from .handlers import keyboardInterruptHandler
from .helpers import Shared, console, logger, load_data
from .mirroredto import Mirroredto
from .multiup import MultiUp


class PyMirror:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.data = load_data()

    @staticmethod
    def initializer() -> NoReturn:
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def tgz(self) -> str:
        out_file = f'{Path(self.args.input).parent}/' \
                   f'{Path(self.args.input).name}.tar.gz '
        with tarfile.open(out_file, 'w:gz') as t:
            t.add(self.args.input, arcname=Path(self.args.input).name)
        return out_file

    def return_ips(self) -> list:
        ips = []
        for k, _ in self.data.items():
            try:
                server = self.data[k]['server'].split('/')[2]
            except IndexError:
                server = self.data[k]['server']
            ip = socket.gethostbyname(server)
            ips.append((ip, k))
        return ips

    def style_output(self,
                     links_list: Union[list, str] = None) -> Union[list, str]:
        if isinstance(links_list, str):
            links_list = [x for x in links_list.split('\n') if x != '']
        if links_list is None:
            links_list = Shared.all_links
        links_dict = {}
        for link in links_list:
            try:
                domain = link.split('/')[:-1][2].replace('www.', '')
                name = '.'.join(domain.split('.')[0:])
                if len(name) == 1:
                    name = '.'.join(domain.split('.')[1:])
                elif len(name.split('.')) == 3:
                    name = '.'.join(domain.split('.')[1:])
                links_dict.update({name: link})
            except IndexError:
                continue
        names = list(links_dict.keys())
        links = list(links_dict.values())
        style = self.args.style
        if style == 'list':
            output = links
        elif style == 'markdown':
            output = '\n'.join(
                [f'- [{name}]({link})' for name, link in zip(names, links)])
        elif style == 'reddit':
            output = ' | '.join(
                [f'[Mirror {n + 1}]({link})' for n, link in enumerate(links)])
        else:
            output = '\n'.join(links)
        return output

    def uploader(self) -> Union[list, str]:
        start_time = time.time()
        signal.signal(signal.SIGINT, keyboardInterruptHandler)

        if self.args.experimental and not self.args.more_links:
            raise Exception('You need to add the `--more-links` flag to use '
                            '`--experimental`')

        with open(f'{Config.data_path}/servers_data.json') as j:
            data = json.load(j)

        if self.args.log:
            logger.remove()
            logger.add(Config.log_file, level='DEBUG')
            logger.add(sys.stderr, level='ERROR')

        console.print('Press `CTRL+C` at any time to quit.', style='#f1fa8c')

        if self.args.check_status:
            console.rule('Checking servers status...')
            ips = self.return_ips()
            cpus = multiprocessing.cpu_count() - 1
            with multiprocessing.Pool(cpus, initializer=self.initializer) as p:
                responses = p.map(APIUpload.ping, ips)
        else:
            responses = []

        console.rule('Uploading...')

        file = self.args.input
        if not Path(file).exists():
            raise FileNotFoundError('If you are sure the path is correct, '
                                    'rename the file removing any illegal '
                                    'characters, then try again.')
        if Path(file).is_dir():
            file = self.tgz()

        if len(responses) == 0:
            responses = [True] * len(data.keys())

        APIUpload(self.data, self.args).api_uploads(responses)

        if self.args.more_links:
            Mirroredto(self.args).upload()
            MultiUp(self.args).upload()
            if self.args.experimental:
                MoreLinks(self.args).upload_to_all_()

        output = self.style_output()

        if self.args.delete:
            if Path(self.args.input).is_dir():
                shutil.rmtree(self.args.input)
            else:
                os.remove(file)
        if Path(file).suffixes == ['.tar', '.gz']:
            os.remove(file)
        console.rule(f'Results: {len(Shared.all_links)}')
        print(output)
        os.rename(file, file)
        for x in Shared.all_links:
            logger.info(x)
        run_time = time.strftime('%H:%M:%S',
                                 time.gmtime(time.time() - start_time))
        h, m, s = [int(_) for _ in run_time.split(':')]
        console.print(
            Panel.fit(f'[{Dp.k}]Process took[{Dp.k}] [{Dp.y}]{h}h {m}m {s}s'))
        console.rule('END')
        return output
