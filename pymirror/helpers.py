#!/usr/bin/env python3
# coding: utf-8

import argparse
import inspect
import json
import re
from pathlib import Path

import loguru
import psutil
import selenium.common.exceptions
from rich.console import Console

from .config import Config


class Shared:
    all_links = []
    pids = []


def logger():
    logger_ = loguru.logger
    logger_.remove()
    return logger_


def selenium_exceptions_classes():
    selenium_exceptions_list = inspect.getmembers(selenium.common.exceptions,
                                                  predicate=inspect.isclass)
    return list(zip(*selenium_exceptions_list))[1]


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


def load_data():
    with open(f"{Config.data_path}/servers_data.json") as j:  # noqa
        data = json.load(j)
    return data


def download_time(file: str) -> float:
    file_size = Path(file).stat().st_size / 1e+6
    return file_size / float(Config['main']['upload_speed'])


def kill_firefox_zombies() -> list:
    terminated = []
    for p in psutil.process_iter():
        if 'firefox-bin' in p.name():
            parent = psutil.Process(p.ppid())
            if parent.name() != 'geckodriver':
                continue
            for child in parent.children(recursive=True):
                if 'firefox-bin' in child.name():
                    try:
                        child.terminate()
                        terminated.append(child.pid)
                    except psutil.AccessDenied:
                        continue
    return terminated


console = Console()
logger = logger()
selenium_exceptions = selenium_exceptions_classes()
Namespace = argparse.Namespace
