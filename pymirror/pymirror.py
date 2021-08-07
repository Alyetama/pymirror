#!/usr/bin/env python3
# coding: utf-8

import argparse
import concurrent.futures
from glob import glob
import importlib.util
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

from rich.console import Console
from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

from .config import Config

console = Console()
logger.remove()

all_links = []


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


class StartDrive:
    def __init__(self):
        pass

    def start_driver(headless=True):
        check_ublock = [
            x for x in glob(f'{Config.PROJECT_PATH}/*')
            if Path(x).name == 'ublock_latest.xpi'
        ]
        if not check_ublock:
            PyMirror.download_ublock()

        options = Options()
        profile = webdriver.FirefoxProfile()
        profile.set_preference('media.volume_scale', '0.0')
        if headless:
            options.headless = True
        try:
            driver = webdriver.Firefox(options=options,
                                       firefox_profile=profile,
                                       service_log_path=os.path.devnull)
            driver.install_addon(Config.UBLOCK, temporary=True)
            return driver
        except WebDriverException:
            os.environ['WDM_LOG_LEVEL'] = '0'
            os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
            os.environ['WDM_LOCAL'] = '1'
            driver = webdriver.Firefox(
                executable_path=GeckoDriverManager().install(),
                options=options,
                firefox_profile=profile,
                service_log_path=os.path.devnull)
            driver.install_addon(Config.UBLOCK, temporary=True)
            return driver

        except Exception as e:
            SeleniumExceptionInfo(e)
            console.print('[#ff5555]Something is wrong with Selenium! '
                          'Try again or remove the `--more-links` flag')


class MoreLinks:
    def __init__(self, file, headless=True):
        self.file = file
        self.driver = StartDrive.start_driver(headless)

    def usaupload(self):
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
                    break
            except:
                continue
        return link

    def filesharego(self):
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
            except:
                continue
        return link

    def filepizza(self):
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

    def expirebox(self):
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
            except:
                continue
        return link

    def filepost(self):
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
            except:
                continue
        return link

    @staticmethod
    def process(fun):
        try:
            link = fun()
            all_links.append(link)
            console.print('[[#50fa7b] OK [/#50fa7b]]', link)
            return link
        except Exception:
            return


class PyMirror:
    def __init__(self):
        pass

    def custom_error_traceback(exception: Exception,
                               error_msg: str,
                               log: bool = False):
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
        tb = traceback.format_exception(None, exception,
                                        exception.__traceback__)
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
                f'[[#50fa7b] OK [/#50fa7b]] [#8be9fd]{ip[1]}[/#8be9fd] is online!'
            )
            logger.info(f'{ip[1]} is online!')
            return True
        else:
            console.print(
                f'[[#ff5555] ERROR! [/#ff5555]] [#8be9fd]{ip[1]}[/#8be9fd] is down!'
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
        times = []
        for n, ((k, _), res) in enumerate(zip(data.items(), responses)):
            if args.number:
                if n == args.number:
                    break
            if res is False:
                continue
            try:
                signal.signal(signal.SIGALRM, lambda x, y: 1 / 0)
                start = time.time()
                if len(times) > 2:
                    signal.alarm(int(statistics.mean(times)) + 5)
                link = PyMirror.curl(data, k, rfile)
                if 'bad gateway' in link.lower() or 'error' in link.lower():
                    raise Exception
                console.print('[[#50fa7b] OK [/#50fa7b]]', link)
                all_links.append(link)
                logger.info(f'[ OK ] {link}')
                times.append(time.time() - start)
            except ZeroDivisionError:
                if args.log:
                    logger.error(f'{k} Timed out!')
            except Exception as e:
                error_class = sys.exc_info()[0].__name__
                PyMirror.custom_error_traceback(e,
                                                f'[ ERROR! ] Error in {k}...',
                                                log=args.log)
            finally:
                signal.alarm(0)

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
        out = os.popen(
            f'curl -sLo {Config.PROJECT_PATH}/ublock_latest.xpi {latest}'
        ).read()
        console.print(
            '\nYou\'re running the "--more-links" flag '
            'for the first time. Please wait until everything is ready. '
            'This is a one-time thing.\n',
            style='#f1fa8c')

    def more_links(file: str):
        def mirror_services(driver, batch):
            def mirroredto(driver, batch):
                try:
                    time.sleep(2)
                    driver.get('https://www.mirrored.to/')
                    time.sleep(5)
                    html = driver.find_element_by_tag_name('html')
                    _ = [html.send_keys(Keys.ARROW_DOWN) for _ in range(3)]

                    for x in batch:
                        try:
                            driver.find_element_by_id(x.lower()).click()
                        except Exception as e:
                            PyMirror.SeleniumExceptionInfo(e)
                            continue

                    time.sleep(2)
                    send_file = lambda selector: driver.find_element_by_css_selector(
                        selector).send_keys(file)
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
                        except Exception:
                            continue

                    current_window = driver.current_window_handle
                    for handle in driver.window_handles:
                        driver.switch_to.window(handle)
                        try:
                            LINK = driver.find_element_by_class_name(
                                'code_wrap').text
                            all_links.append(LINK)
                            console.print(f'[[#50fa7b] OK [/#50fa7b]] {LINK}')
                            logger.info(f'[ OK ] {LINK}')
                            if handle != current_window:
                                driver.close()
                        except Exception:
                            pass

                except Exception as e:
                    PyMirror.SeleniumExceptionInfo(e)

                finally:
                    driver.quit()

            def multiup(driver, batch):
                def cURL_request(url):
                    cURL = shlex.split(url)
                    out = subprocess.run(cURL, stdout=subprocess.PIPE)
                    res = out.stdout.decode('UTF-8').replace('\\', '')
                    try:
                        res = json.loads(res)
                    except JSONDecodeError:
                        res = None
                    return res

                server = cURL_request(
                    'curl -s https://www.multiup.org/api/get-fastest-server'
                )['server']
                selected_hosts_lst = [
                    'filerio.in', 'drop.download', 'download.gg', 'uppit.com',
                    'uploadbox.io'
                ]
                selected_hosts = ' '.join(
                    [f'-F {x}=true' for x in selected_hosts_lst])
                upload = cURL_request(
                    f'curl -sF files[]=@{file} {selected_hosts} {server}')
                link = upload['files'][0]['url'].replace(
                    'download', 'en/mirror')
                driver.get(link)

                i = 0
                j = 0

                while True:
                    time.sleep(1)
                    if i != 0:
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
                        all_links.append(link)
                        console.print('[[#50fa7b] OK [/#50fa7b]]', link)

                driver.quit()

            if batch:
                mirroredto(driver, batch)
            else:
                multiup(driver, batch)

        first_batch = [
            'GoFileIo', 'TusFiles', 'OneFichier', 'ZippyShare', 'UsersDrive',
            'BayFiles', 'AnonFiles', 'ClicknUpload'
        ]
        second_batch = [
            'GoFileIo', 'DownloadGG', 'TurboBit', 'Uptobox', 'SolidFiles',
            'DailyUploads', 'UploadEe', 'DropApk', 'MixdropCo', 'FilesIm',
            'MegaupNet', 'dlupload', 'file-upload'
        ]

        start_driver = StartDrive.start_driver
        drivers = [start_driver(), start_driver(), start_driver()]
        if False in drivers:
            return
        batches = [first_batch, second_batch, None]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            results = [
                executor.submit(mirror_services, driver, batch)
                for driver, batch in zip(drivers, batches)
            ]
            for future in concurrent.futures.as_completed(results):
                futures.append(future.result())

    def style_output(args, LINKs: dict):
        names = list(LINKs.keys())
        links = list(LINKs.values())
        style = args.style
        if style == 'list':
            output = '\n'.join(links)
        elif style == 'markdown':
            output = '\n'.join(
                [f'- [{name}]({link})' for name, link in zip(names, links)])
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
        # links = PyMirror.match_links(links_raw)

        if args.more_links is True:
            file_resolved = str(Path(rfile).resolve())
            try:
                urls = PyMirror.more_links(file_resolved)
            except WebDriverException as e:
                PyMirror.SeleniumExceptionInfo(e)

            hosts = [
                MoreLinks(file_resolved).filepizza,
                MoreLinks(file_resolved).usaupload,
                MoreLinks(file_resolved).filesharego,
                MoreLinks(file_resolved).expirebox,
                MoreLinks(file_resolved).filepost
            ]

            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                results = [
                    executor.submit(MoreLinks(file_resolved).process, fun)
                    for fun in hosts
                ]
                for future in concurrent.futures.as_completed(results):
                    futures.append(future.result())

        LINKs = {}

        for link in all_links:
            domain = link.split('/')[:-1][2].replace('www.', '')
            name = '.'.join(domain.split('.')[0:])
            if len(name) == 1:
                name = '.'.join(domain.split('.')[1:])
            elif len(name.split('.')) == 3:
                name = '.'.join(domain.split('.')[1:])
            LINKs.update({name: link})

        output = PyMirror.style_output(args, LINKs)

        if args.delete:
            if Path(args.input).is_dir():
                shutil.rmtree(PyMirror.clean_filename(args.input))
            else:
                os.remove(rfile)
        if Path(file).suffixes == ['.tar', '.gz']:
            os.remove(file)
        console.rule(f'Results: {len(all_links)}')
        print(output)
        os.rename(rfile, file)
        for x in all_links:
            logger.info(x)
        console.rule('END')
