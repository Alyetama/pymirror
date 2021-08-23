#!/usr/bin/env python3
# coding: utf-8

import argparse
import json
import mimetypes
import platform
import shlex
import signal
import statistics
import subprocess
import time
from pathlib import Path
from typing import Optional, Generator

from dracula import DraculaPalette as Dp

from .handlers import custom_error_traceback
from .helpers import Shared, logger, console


class Error(Exception):
    pass


class APIUpload:
    def __init__(self, data: dict, args: argparse.Namespace) -> None:
        self.data = data
        self.args = args

    @staticmethod
    def ping(ip: str) -> bool:
        def _ping(flag: str, _ip: str) -> int:
            out = subprocess.Popen(shlex.split(f'ping {flag} 1 {_ip}'),
                                   stdout=subprocess.PIPE, shell=False)
            out.communicate()
            return out.returncode

        if platform.system() == 'Windows':
            response = _ping('-n', ip[0])
        else:
            response = _ping('-c', ip[0])
        if response in [0, 256, 512]:
            console.print(
                f'[[{Dp.g}] OK [/{Dp.g}]] [{Dp.c}]{ip[1]}[/{Dp.c}] is online!')
            logger.info(f'{ip[1]} is online!')
            return True
        console.print(
            f'[[{Dp.r}] ERROR! [/{Dp.r}]] [{Dp.c}]{ip[1]}[/{Dp.c}] is '
            'down!'
        )
        logger.warning(f'{ip[1]} is offline!')
        return False

    def curl(self, server: str) -> Optional[str]:
        def find_value(key: str, d: dict) -> Generator[str, None, None]:
            for k, v in (
                    d.items() if type(d) is dict else
                    enumerate(d) if type(d) is list else []
            ):
                if k == key:
                    yield v
                if type(v) in [dict, list]:
                    for value in find_value(key, v):
                        yield value

        if server in ['midi']:
            mimetypes.init()
            mime = mimetypes.guess_type(self.args.input)[0]
            if mime is not None:
                mime = mime.split('/')[0]
                if mime in ['audio', 'video', 'image']:
                    pass
                else:
                    return

        file_size = Path(self.args.input).stat().st_size / 1e+6
        size_limit = self.data[server]['limit']
        if file_size > size_limit:
            return
        srv = self.data[server]['server']
        keys = self.data[server]['keys']
        flags = self.data[server]['flags']
        parameter = self.data[server]['parameter']
        cURL = f'curl {flags} "{parameter}{self.args.input}" {srv}'
        cURL = shlex.split(cURL)
        out = subprocess.run(cURL, stdout=subprocess.PIPE)
        try:
            link = json.loads(out.stdout)
        except json.decoder.JSONDecodeError:
            link = out.stdout.decode('UTF-8').strip('\n')
        if keys:
            link = list(find_value(keys[-1], link))
            if link:
                link = link[0]
        if server == 'oshi':
            link = link.split('\n')[1].replace('DL: ', '')
        return link

    def api_uploads(self, responses: list) -> Optional[list]:
        times = []
        api_uploads_links = []
        for n, ((k, _), res) in enumerate(zip(self.data.items(), responses)):
            if self.args.number and n == int(self.args.number):
                break
            if self.args.debug and n == 1:
                break
            if res is False:
                continue
            try:
                signal.signal(signal.SIGALRM, lambda x, y: 1 / 0)
                start = time.time()
                if len(times) > 2:
                    signal.alarm(int(statistics.mean(times)) + 5)
                link = self.curl(k)
                if not link:
                    continue
                if 'bad gateway' in link.lower() or 'error' in link.lower():
                    continue
                console.print(f'[[{Dp.g}] OK [/{Dp.g}]]', link)
                Shared.all_links.append(link)
                api_uploads_links.append(link)
                logger.info(f'[ OK ] {link}')
                times.append(time.time() - start)
            except ZeroDivisionError:
                if self.args.log:
                    logger.error(f'{k} Timed out!')
            except Error as e:
                custom_error_traceback(e,
                                       f'[ ERROR! ] Error in {k}...',
                                       log=self.args.log)
            finally:
                signal.alarm(0)
        return api_uploads_links
