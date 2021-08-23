#!/usr/bin/env python3
# coding: utf-8

import argparse
import concurrent.futures
import time
from pathlib import Path
from typing import Optional

from dracula import DraculaPalette as Dp

from ..helpers import Shared, console, selenium_exceptions
from ..start_driver import StartDrive


class MoreLinks:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.file = str(Path(self.args.input).resolve())
        self.driver = StartDrive(None).start_driver()
        self.file_size = Path(self.args.input).stat().st_size / 1e+6
        self.headless = True

    def usaupload(self) -> Optional[str]:
        if self.file_size > 1000:
            return
        self.driver.get('https://usaupload.com/register_non_user')
        time.sleep(2)
        self.driver.find_element_by_id('add_files_btn').send_keys(self.file)
        self.driver.find_element_by_class_name('upload-button').click()
        while True:
            time.sleep(1)
            try:
                link = self.driver.find_element_by_class_name(
                    'col-xs-4').get_attribute('dtfullurl')
                if link:
                    return link
            except selenium_exceptions:
                continue

    def filesharego(self) -> Optional[str]:
        if self.file_size > 5000:
            return
        self.driver.get('https://www.filesharego.com')
        time.sleep(2)
        for e in self.driver.find_elements_by_class_name('nav-item'):
            if 'Upload File' in e.text:
                e.click()
                break
        time.sleep(2)
        self.driver.find_element_by_class_name('dz-hidden-input').send_keys(
            self.file)
        while True:
            try:
                time.sleep(1)
                link_id = self.driver.find_element_by_id('copy').get_attribute(
                    'data-id')
                link = self.driver.find_element_by_id(link_id).get_attribute(
                    'value')
                if link:
                    break
            except selenium_exceptions:
                link = None
                continue
        return link

    def filepizza(self) -> Optional[str]:
        self.driver.get('https://file.pizza/')
        self.driver.find_element_by_css_selector(
            '.select-file-label > input:nth-child(1)').send_keys(self.file)
        while True:
            time.sleep(1)
            link = self.driver.find_element_by_class_name('short-url').text
            if link:
                break
        link = link.replace('or, for short: ', '')
        return link

    def expirebox(self) -> Optional[str]:
        if self.file_size > 200:
            return
        self.driver.get('https://expirebox.com/')
        time.sleep(2)
        self.driver.find_element_by_id('fileupload').send_keys(self.file)
        while True:
            time.sleep(1)
            try:
                link = self.driver.find_element_by_css_selector(
                    'div.input-group:nth-child(3) > input:nth-child(1)'
                ).get_attribute('value')
                if link:
                    break
            except selenium_exceptions:
                link = None
                continue
        return link

    def filepost(self) -> Optional[str]:
        if self.file_size > 3000:
            return
        self.driver.get('https://filepost.io/')
        self.driver.find_element_by_css_selector(
            '.drop-region > input:nth-child(4)').send_keys(self.file)
        while True:
            time.sleep(1)
            try:
                e = self.driver.find_element_by_css_selector(
                    'div.buttons:nth-child(3) > a:nth-child(1)')
                link = e.get_attribute('href').split('&body=')[1]
                if link:
                    break
            except selenium_exceptions:
                link = None
                continue
        return link

    def upload(self):
        hosts = [
            MoreLinks(self.args).filepizza,
            MoreLinks(self.args).usaupload,
            MoreLinks(self.args).filesharego,
            MoreLinks(self.args).expirebox,
            MoreLinks(self.args).filepost
        ]

        if (
                self.args.number
                and int(self.args.number) < len(Shared.all_links) + 5
        ):
            left = int(self.args.number) - len(Shared.all_links)
            hosts = hosts[:left]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            urls = []
            results = [executor.submit(fun) for fun in hosts]
            for future in concurrent.futures.as_completed(results):
                link = future.result()
                urls.append(link)
                Shared.all_links.append(link)
                console.print(f'[[{Dp.g}] OK [/{Dp.g}]]', link)
        return urls
