#!/usr/bin/env python3
# coding: utf-8

import json
import shlex
import subprocess
import time
from pathlib import Path
from typing import Union, Optional

from dracula import DraculaPalette as Dp

from .config import Config
from .helpers import Shared, console
from .start_driver import StartDrive


class MultiUp:
    def __init__(self, args, file):
        self.args = args
        self.file = file

    def _multiup(self, driver) -> Optional[list]:
        def cURL_request(url: str) -> Union[None, dict]:
            cURL = shlex.split(url)
            out = subprocess.run(cURL, stdout=subprocess.PIPE)
            res = out.stdout.decode('UTF-8').replace('\\', '')
            try:
                res = json.loads(res)
            except json.JSONDecodeError:
                res = None
            return res

        multiup_links = []

        with open(f'{Config.DATA_PATH}/more_links.json') as j:
            more_links = json.load(j)

        server = cURL_request(
            'curl -s https://www.multiup.org/api/get-fastest-server'
        )['server']
        selected_hosts_lst = [
            'filerio.in', 'drop.download', 'download.gg', 'uppit.com',
            'uploadbox.io'
        ]
        limit_n = len(Shared.all_links)
        file_size = Path(self.file).stat().st_size / 1e+6
        for x in selected_hosts_lst:
            if self.args.number:
                if int(self.args.number) <= limit_n:
                    selected_hosts_lst.remove(x)
                    continue
            if file_size > more_links['multiup'][x]['limit']:
                selected_hosts_lst.remove(x)
            else:
                limit_n += 1
        if not selected_hosts_lst:
            return

        if self.args.debug:
            s = ''
        else:
            s = 's'
        selected_hosts = ' '.join(
            [f'-F {x}=true' for x in selected_hosts_lst])
        upload = cURL_request(
            f'curl -{s}F "files[]=@{self.file}" {selected_hosts} {server}')
        if len(upload['files']) == 0:
            upload = cURL_request(f'curl -{s}F "files[]=@{self.file}" '
                                  f'{server}')
        link = upload['files'][0]['url'].replace(
            'download', 'en/mirror')
        driver.get(link)

        i = 0
        j = 0
        es_len = None
        elements = []

        while True:
            time.sleep(1)
            if es_len != len(elements):
                j = 0
            driver.refresh()
            elements = driver.find_elements_by_class_name('host')
            es_len = len(elements)
            if es_len == 2:
                i += 1
            else:
                j += 1
            if j > i + 10:
                break
            elif len(elements) == len(selected_hosts_lst) + 1:
                break

        for e in elements:
            if '(0)' in e.text:
                link = e.get_attribute('link')
                Shared.all_links.append(link)
                multiup_links.append(link)
                console.print(f'[[{Dp.g}] OK [/{Dp.g}]]', link)

        driver.quit()

        return multiup_links

    def upload(self, headless=True):
        if self.args.debug:
            driver = StartDrive(
                cur_module=Path(__file__).name).start_driver(headless)
        else:
            driver = StartDrive(None).start_driver()
        mirroredto_urls = self._multiup(driver)
        return mirroredto_urls
