#!/usr/bin/env python3
# coding: utf-8

import json
import multiprocessing as mp
import os
import platform
import re
import shlex
import shutil
import signal
import socket
import statistics
import subprocess
import sys
import tarfile
import time
import traceback
from pathlib import Path
from typing import Union, NoReturn, Optional

from dracula import DraculaPalette as Dp
from rich.panel import Panel

from .config import Config
from .handlers import KeyboardInterruptHandler
from .helpers import Shared, console, logger
from .mirroredto import Mirroredto
from .multiup import MultiUp
from .experimental.more_links import MoreLinks


class PyMirror:
    def __init__(self) -> None:
        pass

    @staticmethod
    def custom_error_traceback(exception: Exception,
                               error_msg: str,
                               log: bool = False) -> list:
        if log:
            logger.error(error_msg)
        tb = traceback.format_exception(None, exception,
                                        exception.__traceback__)
        if log:
            logger.error(f'{"-" * 10} Start of error traceback {"-" * 10}')
            for ln in tb:
                logger.error(ln.replace('\n', ''))
            logger.error(f'{"-" * 10} End of error traceback {"-" * 10}')
        return tb

    @staticmethod
    def tgz(input_folder: str) -> str:
        out_file = f'{Path(input_folder).parent}/' \
                   f'{Path(input_folder).name}.tar.gz '
        with tarfile.open(out_file, 'w:gz') as t:
            t.add(input_folder, arcname=Path(input_folder).name)
        return out_file

    @staticmethod
    def initializer() -> NoReturn:
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    @staticmethod
    def return_ips(data: dict) -> list:
        ips = []
        for k, v in data.items():
            try:
                server = data[k]['server'].split('/')[2]
            except IndexError:
                server = data[k]['server']
            ip = socket.gethostbyname(server)
            ips.append((ip, k))
        return ips

    @staticmethod
    def ping(ip: str) -> bool:
        if platform.system() == 'Windows':
            response = os.system(f'ping -n 1 {ip[0]} > /dev/null 2>&1')
        else:
            response = os.system(f'ping -c 1 {ip[0]} > /dev/null 2>&1')
        if response in [0, 256, 512]:
            console.print(
                f'[[{Dp.g}] OK [/{Dp.g}]] [{Dp.c}]{ip[1]}[/{Dp.c}] is online!')
            logger.info(f'{ip[1]} is online!')
            return True
        else:
            console.print(
                f'[[{Dp.r}] ERROR! [/{Dp.r}]] [{Dp.c}]{ip[1]}[/{Dp.c}] is '
                'down!'
            )
            logger.warning(f'{ip[1]} is offline!')
            return False

    @staticmethod
    def curl(data: dict, server: str, file: str) -> Optional[str]:
        file_size = Path(file).stat().st_size / 1e+6
        size_limit = data[server]['limit']
        if file_size > size_limit:
            return
        srv = data[server]['server']
        keys = data[server]['keys']
        flags = data[server]['flags']
        parameter = data[server]['parameter']
        cURL = f'curl {flags} "{parameter}{file}" {srv}'
        cURL = shlex.split(cURL)
        out = subprocess.run(cURL, stdout=subprocess.PIPE)
        try:
            out = json.loads(out.stdout)
        except json.decoder.JSONDecodeError:
            out = out.stdout.decode('UTF-8').strip('\n')

        keyslist = {
            0: 'out',
            1: 'out[keys[0]]',
            2: 'out[keys[0]][keys[1]]',
            3: 'out[keys[0]][keys[1]][keys[2]]'
        }

        link = eval(keyslist[len(keys)])

        if server == 'oshi':
            link = out.split('\n')[1].replace('DL: ', '')

        return link

    @staticmethod
    def api_uploads(args, data: dict, responses: list, file: str) -> list:
        times = []
        api_uploads_links = []
        for n, ((k, _), res) in enumerate(zip(data.items(), responses)):
            if args.number:
                if n == int(args.number):
                    break
            if args.debug:
                if n == 1:
                    break
            if res is False:
                continue
            try:
                signal.signal(signal.SIGALRM, lambda x, y: 1 / 0)
                start = time.time()
                if len(times) > 2:
                    signal.alarm(int(statistics.mean(times)) + 5)
                link = PyMirror.curl(data, k, file)
                if 'bad gateway' in link.lower() or 'error' in link.lower():
                    raise Exception
                console.print(f'[[{Dp.g}] OK [/{Dp.g}]]', link)
                Shared.all_links.append(link)
                api_uploads_links.append(link)
                logger.info(f'[ OK ] {link}')
                times.append(time.time() - start)
            except ZeroDivisionError:
                if args.log:
                    logger.error(f'{k} Timed out!')
            except Exception as e:
                PyMirror.custom_error_traceback(e,
                                                f'[ ERROR! ] Error in {k}...',
                                                log=args.log)
            finally:
                signal.alarm(0)
        return api_uploads_links

    @staticmethod
    def _match_links(links_raw: list) -> list:
        regex = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        links = []
        for link in links_raw:
            if re.match(regex, link) is not None:
                links.append(link)
        return links

    @staticmethod
    def style_output(args, links_dict: dict) -> Union[list, str]:
        names = list(links_dict.keys())
        links = list(links_dict.values())
        style = args.style
        if style == 'list':
            output = '\n'.join(links)
        elif style == 'markdown':
            output = '\n'.join(
                [f'- [{name}]({link})' for name, link in zip(names, links)])
        elif style == 'reddit':
            output = ' | '.join(
                [f'[Mirror {n + 1}]({link})' for n, link in enumerate(links)])
        else:
            output = '\n'.join(links)
        return output

    @staticmethod
    def uploader(args) -> Union[list, str]:
        start_time = time.time()
        signal.signal(signal.SIGINT,
                      KeyboardInterruptHandler.keyboardInterruptHandler)

        if args.experimental and not args.more_links:
            raise Exception('You need to add the `--more-links` flag to use `--experimental`')

        with open(f'{Config.DATA_PATH}/servers_data.json') as j:
            data = json.load(j)

        if args.log:
            logger.remove()
            logger.add(Config.LOG_FILE, level='DEBUG')
            logger.add(sys.stderr, level='ERROR')

        console.print('Press `CTRL+C` at any time to quit.', style='#f1fa8c')

        if args.check_status:
            console.rule('Checking servers status...')
            ips = PyMirror.return_ips(data)
            cpus = mp.cpu_count() - 1
            with mp.Pool(cpus, initializer=PyMirror.initializer) as p:
                responses = p.map(PyMirror.ping, ips)
        else:
            responses = []

        console.rule('Uploading...')

        file = args.input
        if not Path(file).exists():
            raise FileNotFoundError('If you are sure the path is correct, '
                                    'rename the file removing any illegal '
                                    'characters, then try again.')

        if Path(file).is_dir():
            file = PyMirror.tgz(file)

        if len(responses) == 0:
            responses = [True] * len(data.keys())

        PyMirror.api_uploads(args, data, responses, file)

        if args.more_links:
            file_resolved = str(Path(file).resolve())
            Mirroredto(args, file_resolved).upload()
            MultiUp(args, file_resolved).upload()
            if args.experimental:
                MoreLinks(args, file_resolved).upload()

        links_dict = {}
        for link in Shared.all_links:
            domain = link.split('/')[:-1][2].replace('www.', '')
            name = '.'.join(domain.split('.')[0:])
            if len(name) == 1:
                name = '.'.join(domain.split('.')[1:])
            elif len(name.split('.')) == 3:
                name = '.'.join(domain.split('.')[1:])
            links_dict.update({name: link})

        output = PyMirror.style_output(args, links_dict)

        if args.delete:
            if Path(args.input).is_dir():
                shutil.rmtree(args.input)
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
