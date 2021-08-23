#!/usr/bin/env python3
# coding: utf-8

import sys
import time
import traceback
from typing import NoReturn

import psutil
from dracula import DraculaPalette as Dp

from .helpers import console, logger, Shared


class FirefoxInterruptHandler:
    def __init__(self, pids: list) -> None:
        self.pids = pids

    def firefoxInterrupt(self) -> list:
        terminated = []
        if self.pids:
            for pid in self.pids:
                try:
                    p = psutil.Process(pid)
                    p.terminate()
                    terminated.append(pid)
                except psutil.NoSuchProcess:
                    continue
        return terminated


class KeyboardInterruptHandler:
    def __init__(self) -> None:
        self.firefox_handler = FirefoxInterruptHandler(Shared.pids)

    def keyboardInterruptHandler(self) -> NoReturn:
        sys.tracebacklimit = 0
        print('', end='\r')
        time.sleep(0.5)
        console.print(f'[{Dp.y}]Quitting...')
        terminated = self.firefox_handler.firefoxInterrupt()
        logger.info('Interrupted by the user.')
        if terminated:
            logger.info('Killed interrupted driver instances:', terminated)
        sys.exit(0)


def SeleniumExceptionInfo(exception: Exception) -> str:
    tb = traceback.format_exception(None, exception,
                                    exception.__traceback__)
    tb = ''.join(tb).rstrip()
    logger.error(f'Selenium encountered an error:\n{tb}')
    return tb


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
