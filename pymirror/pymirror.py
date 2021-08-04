#!/usr/bin/env python3
# coding: utf-8

import argparse
from glob import glob
import json
import multiprocessing as mp
import os
import platform
import re
import shlex
import shutil
import signal
import socket
import statistics
import string
import subprocess
import sys
import tarfile
import time
import traceback
from pathlib import Path
from types import SimpleNamespace

from rich.console import Console
from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

from .config import Config

console = Console()


class KeyboardInterruptHandler:
    def __init__(self):
        pass

    def keyboardInterruptHandler(*args):
        sys.tracebacklimit = 0
        print('', end='\r')
        time.sleep(0.5)
        console.print('[#f1fa8c]Quitting...')
        logger.info('Interrupted by the user.')
        sys.exit(0)


class CustomHelpFormatter(argparse.HelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=40, width=80)

    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs == 0:
            return super()._format_action_invocation(action)
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return ', '.join(action.option_strings) + ' ' + args_string


def fmt(prog):
    return CustomHelpFormatter(prog)


class PyMirror:
    def __init__(self):
        pass

    def custom_error_traceback(exception: Exception,
                               error_msg: str,
                               log: bool = False,
                               verbose: bool = False):
        if log:
            logger.error(error_msg)
        tb = traceback.format_exception(None, exception,
                                        exception.__traceback__)
        if verbose:
            console.print(tb)
        if log:
            logger.error(f'{"-" * 10} Start of error traceback {"-" * 10}')
            for ln in tb:
                logger.error(ln.replace('\n', ''))
            logger.error(f'{"-" * 10} End of error traceback {"-" * 10}')
        return tb

    def tgz(input_folder: str):
        out_file = f'{Path(input_folder).parent}/{Path(input_folder).name}.tar.gz'
        with tarfile.open(out_file, 'w:gz') as t:
            t.add(input_folder, arcname=Path(input_folder).name)
        return out_file

    def clean_filename(file: str):
        rfile = ''.join([
            Path(x).stem.replace(x, "_") if x in string.punctuation +
            ' ' else x for x in Path(Path(file).stem).stem
        ])
        rfile = f'{rfile}{"".join(Path(file).suffixes)}'
        rfile = f'{Path(file).parent}/{rfile}'
        os.rename(file, rfile)
        return rfile

    def initializer():
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def SeleniumExceptionInfo(exception: Exception):
        tb = traceback.format_exception(None, exception, exception.__traceback__)
        logger.error(f'Selenium encountered an error: {tb}')

    def return_ips(data: dict):
        ips = []
        for k, v in data.items():
            try:
                server = data[k]['server'].split('/')[2]
            except IndexError:
                server = data[k]['server']
            ip = socket.gethostbyname(server)
            ips.append((ip, k))
        return ips

    def ping(ip: str):
        if platform.system() == 'Windows':
            response = os.system(f'ping -n 1 {ip[0]} > /dev/null 2>&1')
        else:
            response = os.system(f'ping -c 1 {ip[0]} > /dev/null 2>&1')
        if response in [0, 256, 512]:
            console.print(
                f'[[#50fa7b]OK[/#50fa7b]] [#8be9fd]{ip[1]}[/#8be9fd] is online!'
            )
            logger.info(f'{ip[1]} is online!')
            return True
        else:
            console.print(
                f'[[#ff5555]ERROR![/#ff5555]] [#8be9fd]{ip[1]}[/#8be9fd] is down!'
            )
            logger.warning(f'{ip[1]} is offline!')
            return False

    def curl(data: dict, server: str, file: str):
        srv = data[server]['server']
        keys = data[server]['keys']
        flags = data[server]['flags']
        parameter = data[server]['parameter']
        cURL = f'curl {flags} "{parameter}{file}" {srv}'
        cURL = shlex.split(cURL)
        out = subprocess.run(cURL, stdout=subprocess.PIPE)
        try:
            out = json.loads(out.stdout)
        except json.decoder.JSONDecodeError:
            out = out.stdout.decode('UTF-8').strip('\n')

        keyslist = {
            0: 'out',
            1: 'out[keys[0]]',
            2: 'out[keys[0]][keys[1]]',
            3: 'out[keys[0]][keys[1]][keys[2]]'
        }

        link = eval(keyslist[len(keys)])

        if server == 'oshi':
            link = out.split('\n')[1].replace('DL: ', '')

        return link

    def api_uploads(args, data: dict, responses: list, rfile: str):
        links_raw = []
        times = []
        for n, ((k, _), res) in enumerate(zip(data.items(), responses)):
            if args.number:
                if n == args.number:
                    break
            if res is False or k == 'mirroredto':
                continue
            try:
                signal.signal(signal.SIGALRM, lambda x, y: 1 / 0)
                start = time.time()
                if len(times) > 2:
                    signal.alarm(int(statistics.mean(times)) + 5)
                link = PyMirror.curl(data, k, rfile)
                if 'Bad Gateway' in link:
                    raise Exception
                console.print('[[#50fa7b]OK[/#50fa7b]]', link)
                logger.info(f'[OK] {link}')
                links_raw.append(link)
                times.append(time.time() - start)
            except ZeroDivisionError:
                if args.verbose is True:
                    console.print(
                        f'[[#ff5555]ERROR![/#ff5555]] {k} Timed out! Skipping...'
                    )
                if args.log:
                    logger.error(f'{k} Timed out!')
            except Exception as e:
                if args.verbose is True:
                    error_class = sys.exc_info()[0].__name__
                    console.print(f'[[#ff5555]ERROR![/#ff5555]] Error in {k}:'
                                  f' {error_class}. Skipping...')
                    PyMirror.custom_error_traceback(
                        e, f'[ERROR!] Error in {k}...', log=args.log)
            signal.alarm(0)

        return links_raw

    def match_links(links_raw: list):
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

    def download_ublock():
        latest = 'https://addons.mozilla.org/firefox/downloads/file/3806442'
        out = os.popen(f'curl -sLo {Config.PROJECT_PATH}/ublock_latest.xpi {latest}'
                 ).read()
        console.print('\nYou\'re running the "--mirroredto" flag '
            'for the first time. Please wait until everything is ready. '
            'This is a one-time thing.\n', style='#f1fa8c')
        time.sleep(10)

    def mirroredto(file: str):
        check_ublock = [x for x in glob(Config.PROJECT_PATH) if Path(x).name == 'ublock_latest.xpi']
        if not check_ublock:
            PyMirror.download_ublock()
            

        first_batch = [
            'GoFileIo', 'TusFiles', 'OneFichier', 'ZippyShare', 'UsersDrive',
            'BayFiles', 'AnonFiles', 'ClicknUpload'
        ]
        second_batch = [
            'GoFileIo', 'DownloadGG', 'TurboBit', 'Uptobox', 'SolidFiles',
            'DailyUploads', 'UploadEe', 'DropApk', 'MixdropCo', 'FilesIm',
            'MegaupNet', 'dlupload', 'file-upload', 'catboxmoe'
        ]

        URLs = []

        options = Options()
        options.headless = True

        try:
            driver = webdriver.Firefox(options=options,
                                       service_log_path=os.path.devnull)
        except WebDriverException:
            os.environ['WDM_LOG_LEVEL'] = '0'
            os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
            os.environ['WDM_LOCAL'] = '1'
            driver = webdriver.Firefox(
                executable_path=GeckoDriverManager().install(), options=options, service_log_path=os.path.devnull)
        except Exception as e:
            SeleniumExceptionInfo(e)
            sys.exit(1)

        driver.install_addon(Config.UBLOCK, temporary=True)

        for ls in [first_batch, second_batch]:
            try:
                driver.get('https://www.mirrored.to/')
                time.sleep(5)
                html = driver.find_element_by_tag_name('html')
                _ = [html.send_keys(Keys.ARROW_DOWN) for _ in range(3)]

                for x in ls:
                    try:
                        driver.find_element_by_id(x.lower()).click()
                    except Exception as e:
                        PyMirror.SeleniumExceptionInfo(e)
                        sys.exit(1)

                time.sleep(2)
                driver.find_element_by_css_selector(
                    '#uploadifive-html_file_upload > input[type=file]:nth-child(3)'
                ).send_keys(file)

                time.sleep(1)

                driver.find_element_by_id('upload_button').click()
                time.sleep(5)

                while True:
                    if driver.current_url != 'https://www.mirrored.to/':
                        time.sleep(1)
                        break

                link = driver.find_element_by_class_name('mlink').text
                driver.get(link)
                time.sleep(2)
                driver.find_element_by_class_name('secondary').click()
                time.sleep(2)

                start = time.time()

                while True:
                    time.sleep(5)
                    status = [
                        x.text for x in driver.find_elements_by_class_name(
                            'id_Success')
                    ]
                    if len(status) >= 8 or time.time() - start > 60:
                        break

                for x in driver.find_elements_by_class_name('get_btn'):
                    try:
                        x.click()
                    except:
                        continue

                current_window = driver.current_window_handle
                for handle in driver.window_handles:
                    driver.switch_to.window(handle)
                    try:
                        LINK = driver.find_element_by_class_name(
                            'code_wrap').text
                        URLs.append(LINK)
                        console.print(f'[[#50fa7b]OK[/#50fa7b]] {LINK}')
                        logger.info(f'[OK] {LINK}')
                        if handle != current_window:
                            driver.close()
                    except:
                        continue

                time.sleep(2)
                driver.switch_to.window(current_window)

            except Exception as e:
                PyMirror.SeleniumExceptionInfo(e)
                driver.quit()
                break

        driver.quit()
        return URLs

    def style_output(args, links: list, data: dict):
        style = args.style
        if style == 'list':
            output = '\n'.join(links)
        elif style == 'markdown':
            output = '\n'.join([
                f'- [{name}]({link})'
                for name, link in zip([k for k, _ in data.items()], links)
            ])
        elif style == 'reddit':
            output = ' | '.join(
                [f'[Mirror {n + 1}]({link})' for n, link in enumerate(links)])
        else:
            output = '\n'.join(links)
        return output

    def uploader(self, args):
        signal.signal(signal.SIGINT,
                      KeyboardInterruptHandler.keyboardInterruptHandler)

        with open(Config.DATA) as j:
            data = json.load(j)

        if args.log:
            logger.remove()
            logger.add(Config.LOG_FILE, level='DEBUG')
            logger.add(sys.stderr, level='ERROR')

        if args.mirroredto is True:
            data['mirroredto'] = {'server': 'https://mirrored.to'}

        console.print('Press `CTRL+C` at any time to quit.', style='#f1fa8c')

        if args.check_status is True:
            console.rule('Checking servers status...')
            ips = PyMirror.return_ips(data)
            cpus = mp.cpu_count() - 1
            with mp.Pool(cpus, initializer=PyMirror.initializer) as p:
                responses = p.map(PyMirror.ping, ips)
        else:
            responses = []

        console.rule('Uploading...')

        file = args.input
        if Path(file).is_dir():
            file = PyMirror.tgz(file)

        rfile = PyMirror.clean_filename(file)

        if len(responses) == 0:
            responses = [True] * len(data.keys())

        links_raw = PyMirror.api_uploads(args, data, responses, rfile)
        links = PyMirror.match_links(links_raw)

        if args.mirroredto is True:
            try:
                urls = PyMirror.mirroredto(str(Path(rfile).resolve()))
            except WebDriverException as e:
                PyMirror.SeleniumExceptionInfo(e)
                urls = []
            links = links + urls

        output = PyMirror.style_output(args, links, data)

        if args.delete:
            if Path(args.input).is_dir():
                shutil.rmtree(PyMirror.clean_filename(args.input))
            else:
                os.remove(rfile)
        if Path(file).suffixes == ['.tar', '.gz']:
            os.remove(file)
        console.rule('Results')
        print(output)
        for x in links:
            logger.info(x)
        console.rule('END')
