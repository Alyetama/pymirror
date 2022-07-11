#!/usr/bin/env python3
# coding: utf-8

import argparse
import concurrent.futures
import json
import time
from pathlib import Path

from dracula import DraculaPalette as Dp
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from pymirror.config import config
from pymirror.helpers import Shared, console, logger, selenium_exceptions
from pymirror.start_driver import StartDrive


class Mirroredto:

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.config = config()

    def _mirroredto(self, drivers: list) -> list:

        def process(driver, batch):
            file_size = Path(self.args.input).stat().st_size / 1e+6
            with open(f'{self.config["data_path"]}/more_links.json') as j:
                more_links = json.load(j)

            local_limit = len(Shared.all_links)
            mirroredto_links = []
            try:
                if self.args.number:
                    if local_limit >= int(self.args.number):
                        return
                    local_limit += 1
                time.sleep(2)
                driver.get('https://www.mirrored.to/')
                time.sleep(5)
                html = driver.find_element(By.TAG_NAME, 'html')
                _ = [html.send_keys(Keys.ARROW_DOWN) for _ in range(3)]

                for x in batch:
                    try:
                        if len(batch) > 8 and x == 'GoFileIo':
                            driver.find_element(By.ID, x.lower()).click()
                        elif more_links['mirroredto'][x]['limit'] \
                                > file_size:
                            driver.find_element(By.ID, x.lower()).click()
                    except selenium_exceptions as e:
                        # console.print(SeleniumExceptionInfo(e))
                        continue

                time.sleep(2)
                resolved_file = str(Path(self.args.input).resolve())
                driver.find_element(
                    By.CSS_SELECTOR, '#uploadifive-html_file_upload > '
                    'input[type=file]:nth-child(3)').send_keys(resolved_file)
                time.sleep(1)

                driver.find_element(By.ID, 'upload_button').click()
                time.sleep(5)

                while True:
                    if driver.current_url != 'https://www.mirrored.to/':
                        time.sleep(1)
                        break

                link = driver.find_element(By.CLASS_NAME, 'mlink').text
                driver.get(link)
                time.sleep(2)
                driver.find_element(By.CLASS_NAME, 'secondary').click()
                time.sleep(2)

                start = time.time()

                while True:
                    time.sleep(5)
                    status = [
                        x.text for x in driver.find_elements(
                            By.CLASS_NAME, 'id_Success')
                    ]
                    if len(status) >= 8 or time.time() - start > 60:
                        break

                for x in driver.find_elements(By.CLASS_NAME, 'get_btn'):
                    try:
                        x.click()
                    except selenium_exceptions:
                        continue

                current_window = driver.current_window_handle
                for handle in driver.window_handles:
                    driver.switch_to.window(handle)
                    try:
                        link = driver.find_element(By.CLASS_NAME,
                                                   'code_wrap').text
                        Shared.all_links.append(link)
                        mirroredto_links.append(link)
                        console.print(f'[[{Dp.g}] OK [/{Dp.g}]] {link}')
                        logger.info(f'[ OK ] {link}')
                        if handle != current_window:
                            driver.close()
                    except selenium_exceptions:
                        pass

            except Exception as exception:
                raise exception

            finally:
                driver.quit()
                if self.args.debug:
                    console.print(f'[{Dp.y}]Closed driver instance spawned '
                                  f'in {__file__}')
            return mirroredto_links

        first_batch = [
            'GoFileIo', 'TusFiles', 'OneFichier', 'ZippyShare', 'UsersDrive',
            'BayFiles', 'AnonFiles', 'ClicknUpload'
        ]
        second_batch = [
            'GoFileIo', 'DownloadGG', 'TurboBit', 'Uptobox', 'SolidFiles',
            'DailyUploads', 'UploadEe', 'DropApk', 'MixdropCo', 'FilesIm',
            'MegaupNet', 'dlupload', 'file-upload'
        ]

        if self.args.debug:
            batches = [first_batch]
        else:
            batches = [first_batch, second_batch]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            mirroredto_urls = []
            results = [
                executor.submit(process, driver, batch)
                for driver, batch in zip(drivers, batches)
            ]
            for future in concurrent.futures.as_completed(results):
                mirroredto_urls.append(future.result())

        return mirroredto_urls

    def upload(self, headless=True):
        if self.args.debug:
            driver = StartDrive(cur_module=Path(__file__).name).start_driver
            drivers = [driver(headless)]
        else:
            driver = StartDrive(None).start_driver
            drivers = [driver(headless), driver(headless)]
        mirroredto_urls = self._mirroredto(drivers)
        return mirroredto_urls
