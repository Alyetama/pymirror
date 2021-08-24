#!/usr/bin/env python3
# coding: utf-8

import argparse
import inspect
import itertools
import signal
import statistics
import time
from pathlib import Path
from typing import Optional

from dracula import DraculaPalette as Dp

from ..helpers import Shared, console, selenium_exceptions
from ..start_driver import StartDrive


class MoreLinks:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.methods = inspect.getmembers(self, predicate=inspect.ismethod)[1:]
        self.file = str(Path(self.args.input).resolve())
        self.file_size = Path(self.args.input).stat().st_size / 1e+6
        self.headless = True

    def getdict_(self):
        return dict(self.methods)

    @staticmethod
    def init_driver():
        return StartDrive(None).start_driver()

    def upload_to_all_(self):
        times = []
        links = []
        sites = {k: v for k, v in MoreLinks(
            self.args).getdict_().items() if not k.endswith('_')}

        if (
                self.args.number
                and int(self.args.number) < len(Shared.all_links) + 5
        ):
            left = int(self.args.number) - len(Shared.all_links)
            sites = dict(itertools.islice(sites.items(), left))

        for name, function in sites.items():
            try:
                signal.signal(signal.SIGALRM, lambda x, y: 1 / 0)
                start = time.time()
                if len(times) > 2:
                    signal.alarm(int(statistics.mean(times)) + 5)
                link = function()
                times.append(time.time() - start)
                Shared.all_links.append(links)
                links.append(link)
                console.print(f'[[{Dp.g}] OK [/{Dp.g}]]', link)
            except selenium_exceptions:
                console.print(
                    f'[[{Dp.r}] ERROR! [/{Dp.r}]]',
                    f'Encountered error while attempting to upload to'
                    f'[{Dp.b}]{name}[/{Dp.b}]'
                )
            finally:
                signal.alarm(0)
        return links

    def usaupload(self) -> Optional[str]:
        if self.file_size > 1000:
            return
        driver = self.init_driver()
        driver.get('https://usaupload.com/register_non_user')
        time.sleep(2)
        driver.find_element_by_id('add_files_btn').send_keys(self.file)
        driver.find_element_by_class_name('upload-button').click()
        while True:
            try:
                link = driver.find_element_by_class_name(
                    'col-xs-4').get_attribute('dtfullurl')
                if link:
                    driver.quit()
                    return link
            except selenium_exceptions:
                time.sleep(1)

    def filesharego(self) -> Optional[str]:
        if self.file_size > 5000:
            return
        driver = self.init_driver()
        driver.get('https://www.filesharego.com')
        time.sleep(2)
        for e in driver.find_elements_by_class_name('nav-item'):
            if 'Upload File' in e.text:
                e.click()
                break
        time.sleep(2)
        driver.find_element_by_class_name('dz-hidden-input').send_keys(
            self.file)
        while True:
            try:
                link_id = driver.find_element_by_id('copy').get_attribute(
                    'data-id')
                link = driver.find_element_by_id(link_id).get_attribute(
                    'value')
                if link:
                    driver.quit()
                    return link
            except selenium_exceptions:
                time.sleep(1)

    def filepizza(self) -> Optional[str]:
        driver = self.init_driver()
        driver.get('https://file.pizza/')
        driver.find_element_by_css_selector(
            '.select-file-label > input:nth-child(1)').send_keys(self.file)
        while True:
            time.sleep(1)
            link = driver.find_element_by_class_name('short-url').text
            if link:
                driver.quit()
                break
        link = link.replace('or, for short: ', '')
        return link

    def expirebox(self) -> Optional[str]:
        if self.file_size > 200:
            return
        driver = self.init_driver()
        driver.get('https://expirebox.com/')
        time.sleep(2)
        driver.find_element_by_id('fileupload').send_keys(self.file)
        while True:
            time.sleep(1)
            try:
                link = driver.find_element_by_css_selector(
                    'div.input-group:nth-child(3) > input:nth-child(1)'
                ).get_attribute('value')
                if link:
                    driver.quit()
                    return link
            except selenium_exceptions:
                time.sleep(1)

    def filepost(self) -> Optional[str]:
        if self.file_size > 3000:
            return
        driver = self.init_driver()
        driver.get('https://filepost.io/')
        driver.find_element_by_css_selector(
            '.drop-region > input:nth-child(4)').send_keys(self.file)
        while True:
            time.sleep(1)
            try:
                e = driver.find_element_by_css_selector(
                    'div.buttons:nth-child(3) > a:nth-child(1)')
                link = e.get_attribute('href').split('&body=')[1]
                if link:
                    driver.quit()
                    return link
            except selenium_exceptions:
                time.sleep(1)

    def sendcm(self) -> str:
        driver = self.init_driver()
        driver.find_element_by_id('file_0').send_keys(self.file)
        up = driver.find_element_by_id('upload_controls')
        up.find_element_by_class_name('btn').click()
        while True:
            try:
                link = driver.find_element_by_css_selector(
                    '.input-group > textarea:nth-child(2)').text
                return link
            except selenium_exceptions:
                time.sleep(1)
