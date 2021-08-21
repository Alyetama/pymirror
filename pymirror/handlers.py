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
    def __init__(self, pids) -> None:
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
        pass

    @staticmethod
    def keyboardInterruptHandler(self, *args) -> NoReturn:
        sys.tracebacklimit = 0
        print('', end='\r')
        time.sleep(0.5)
        console.print(f'[{Dp.y}]Quitting...')
        firefox_handler = FirefoxInterruptHandler(Shared.pids)
        terminated = firefox_handler.firefoxInterrupt()
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
