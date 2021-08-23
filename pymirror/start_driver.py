#!/usr/bin/env python3
# coding: utf-8

import os
import platform
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any

from dracula import DraculaPalette as Dp
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

from .config import Config
from .helpers import Shared, console, selenium_exceptions


class StartDrive:
    def __init__(self, cur_module: Any = None) -> None:
        self.cur_module = cur_module

    @staticmethod
    def download_ublock() -> None:
        Path(Path(Config.UBLOCK).parent).mkdir(exist_ok=True)
        latest = 'https://addons.mozilla.org/firefox/downloads/file/3806442'
        p = subprocess.Popen(
            shlex.split(f'curl -sLo "{Config.UBLOCK}" {latest}'),
            stdout=subprocess.PIPE,
            shell=False
        )
        p.communicate()
        console.print(
            '\nYou\'re running the "--more-links" flag '
            'for the first time. Please wait until everything is ready. '
            'This is a one-time thing.\n',
            style='#f1fa8c')
        if not Path(Config.UBLOCK).exists():
            raise AssertionError

    def start_driver(self, headless: bool = True):
        if not Path(Config.UBLOCK).exists():
            self.download_ublock()

        options = Options()
        profile = webdriver.FirefoxProfile()
        profile.set_preference('media.volume_scale', '0.0')
        if headless:
            options.headless = True
        try:
            driver = webdriver.Firefox(options=options,
                                       firefox_profile=profile,
                                       service_log_path=os.path.devnull)
        except WebDriverException:
            os.environ['WDM_LOG_LEVEL'] = '0'
            os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
            os.environ['WDM_LOCAL'] = '1'
            try:
                driver = webdriver.Firefox(
                    executable_path=GeckoDriverManager().install(),
                    options=options,
                    firefox_profile=profile,
                    service_log_path=os.path.devnull)
            except ValueError:
                raise Exception('Could not find Firefox!')
            except OSError:
                if platform.node() == 'raspberrypi':
                    raise Exception(
                        'It seems like you\'re on a raspberrypi. '
                        'You will need to build gecko driver for ARM: '
                        'https://firefox-source-docs.mozilla.org/testing/'
                        'geckodriver/ARM.html')
        except selenium_exceptions as se:
            console.print(f'[{Dp.b}]{__file__}[{Dp.b}] '
                          f'[{Dp.y}]raised an unexpected issue! '
                          'Try again or remove the `--more-links` flag')
            raise se

        ublock_exists = False
        driver.install_addon(Config.UBLOCK, temporary=True)  # noqa
        time.sleep(1)
        driver.get('about:support')
        body = driver.find_element_by_id('addons-tbody')
        rows = body.find_elements_by_tag_name('tr')
        for row in rows:
            cells = row.find_elements_by_tag_name('td')
            for cell in cells:
                if 'uBlock' in cell.text:
                    ublock_exists = True
        if not ublock_exists:
            raise AssertionError

        capabilities = driver.capabilities
        pid = capabilities['moz:processID']
        Shared.pids.append(pid)
        if self.cur_module is not None:
            console.print(f'Spawned a driver in {self.cur_module}: {pid}')
        return driver
