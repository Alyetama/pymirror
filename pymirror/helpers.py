#!/usr/bin/env python3
# coding: utf-8
import inspect

import loguru
from rich.console import Console
import selenium.common.exceptions


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


console = Console()
logger = logger()
selenium_exceptions = selenium_exceptions_classes()
