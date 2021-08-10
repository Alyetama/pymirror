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
from typing import Union, NoReturn
from pathlib import Path

from dracula import DraculaPalette as dp
import psutil
from rich.console import Console
from rich.panel import Panel
from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

try:
    from .config import Config
except ImportError:
    from config import Config

console = Console()
logger.remove()

all_links = []
pids = []


class FirefoxInterrupt:
    def __init__(self) -> None:
        pass

    @staticmethod
    def firefoxInterrupt(pids) -> None:
        if pids:
            for pid in pids:
                try:
                    p = psutil.Process(pid)
                    p.terminate()
                except psutil.NoSuchProcess:
                    continue


class KeyboardInterruptHandler:
    def __init__(self) -> None:
        pass

    @staticmethod
    def keyboardInterruptHandler(*args):
        sys.tracebacklimit = 0
        print('', end='\r')
        time.sleep(0.5)
        console.print(f'[{dp.y}]Quitting...')
        FirefoxInterrupt.firefoxInterrupt(pids)
        logger.info('Interrupted by the user.')
        sys.exit(0)


class StartDrive:
    def __init__(self) -> None:
        pass

    @staticmethod
    def start_driver(headless: bool = True):
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
        except Exception as e:
            SeleniumExceptionInfo(e)
            console.print(f'[{dp.y}]Something is wrong with Selenium! '
                          'Try again or remove the `--more-links` flag')

        driver.install_addon(Config.UBLOCK, temporary=True)
        capabilities = driver.capabilities
        pids.append(capabilities['moz:processID'])
        return driver


class MoreLinks:
    def __init__(self, file: str, headless: bool = True) -> None:
        self.file = file
        self.file_size = Path(file).stat().st_size / 1e+6
        self.driver = StartDrive.start_driver(headless)

    def usaupload(self) -> str:
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
                    break
            except:
                continue
        return link

    def filesharego(self) -> str:
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
            except:
                continue
        return link

    def filepizza(self) -> str:
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

    def expirebox(self) -> str:
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
            except:
                continue
        return link

    def filepost(self) -> str:
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
            except:
                continue
        return link

    @staticmethod
    def process(fun):
        try:
            link = fun()
            all_links.append(link)
            console.print(f'[[{dp.g}] OK [/{dp.g}]]', link)
            return link
        except Exception:
            return


class PyMirror:
    def __init__(self) -> None:
        pass

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

    def tgz(input_folder: str) -> str:
        out_file = f'{Path(input_folder).parent}/{Path(input_folder).name}.tar.gz'
        with tarfile.open(out_file, 'w:gz') as t:
            t.add(input_folder, arcname=Path(input_folder).name)
        return out_file

    def clean_filename(file: str) -> str:
        rfile = ''.join([
            Path(x).stem.replace(x, "_") if x in string.punctuation +
            ' ' else x for x in Path(Path(file).stem).stem
        ])
        rfile = f'{rfile}{"".join(Path(file).suffixes)}'
        rfile = f'{Path(file).parent}/{rfile}'
        os.rename(file, rfile)
        return rfile

    def initializer() -> NoReturn:
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def SeleniumExceptionInfo(exception: Exception) -> str:
        tb = traceback.format_exception(None, exception,
                                        exception.__traceback__)
        tb = ''.join(tb).rstrip()
        logger.error(f'Selenium encountered an error:\n{tb}')
        return tb

    def return_ips(data: dict) -> list:
        ips = []
        for k, v in data.items():
            try:
                server = data[k]['server'].split('/')[2]
            except IndexError:
                server = data[k]['server']
            ip = socket.gethostbyname(server)
            ips.append((ip, k))
        return ips

    def ping(ip: str) -> bool:
        if platform.system() == 'Windows':
            response = os.system(f'ping -n 1 {ip[0]} > /dev/null 2>&1')
        else:
            response = os.system(f'ping -c 1 {ip[0]} > /dev/null 2>&1')
        if response in [0, 256, 512]:
            console.print(
                f'[[{dp.g}] OK [/{dp.g}]] [{dp.c}]{ip[1]}[/{dp.c}] is online!')
            logger.info(f'{ip[1]} is online!')
            return True
        else:
            console.print(
                f'[[{dp.r}] ERROR! [/{dp.r}]] [{dp.c}]{ip[1]}[/{dp.c}] is down!'
            )
            logger.warning(f'{ip[1]} is offline!')
            return False

    def curl(data: dict, server: str, file: str) -> str:
        file_size = Path(file).stat().st_size / 1e+6
        size_limit = data[server]['limit']
        if file_size > size_limit:
            return
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

    def api_uploads(args, data: dict, responses: list, rfile: str) -> list:
        times = []
        api_uploads_links = []
        for n, ((k, _), res) in enumerate(zip(data.items(), responses)):
            if args.number:
                if n == int(args.number):
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
                console.print(f'[[{dp.g}] OK [/{dp.g}]]', link)
                all_links.append(link)
                api_uploads_links.append(link)
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
        return api_uploads_links

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

    def download_ublock() -> None:
        latest = 'https://addons.mozilla.org/firefox/downloads/file/3806442'
        out = os.popen(
            f'curl -sLo {Config.PROJECT_PATH}/ublock_latest.xpi {latest}'
        ).read()
        console.print(
            '\nYou\'re running the "--more-links" flag '
            'for the first time. Please wait until everything is ready. '
            'This is a one-time thing.\n',
            style='#f1fa8c')
        assert Path(f'{Config.PROJECT_PATH}/ublock_latest.xpi').exists()

    def more_links(args, file: str) -> list:
        file_size = Path(file).stat().st_size / 1e+6
        with open(f'{Config.DATA_PATH}/more_links.json') as j:
            more_links = json.load(j)

        def mirror_services(driver, batch: list) -> list:
            local_limit = len(all_links)

            def mirroredto(driver, batch: list) -> list:
                mirroredto_links = []
                try:
                    if args.number:
                        if local_limit >= int(args.number):
                            return
                        else:
                            local_limit += 1
                    time.sleep(2)
                    driver.get('https://www.mirrored.to/')
                    time.sleep(5)
                    html = driver.find_element_by_tag_name('html')
                    _ = [html.send_keys(Keys.ARROW_DOWN) for _ in range(3)]

                    for x in batch:
                        try:
                            if len(batch) > 8 and x == 'GoFileIo':
                                driver.find_element_by_id(x.lower()).click()
                            elif more_links['mirroredto'][x][
                                    'limit'] > file_size:
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
                            mirroredto_links.append(LINK)
                            console.print(f'[[{dp.g}] OK [/{dp.g}]] {LINK}')
                            logger.info(f'[ OK ] {LINK}')
                            if handle != current_window:
                                driver.close()
                        except Exception:
                            pass

                except Exception as e:
                    PyMirror.SeleniumExceptionInfo(e)

                finally:
                    driver.quit()

                return mirroredto_links

            def multiup(driver, batch: None) -> list:
                def cURL_request(url: str) -> Union[None, dict]:
                    cURL = shlex.split(url)
                    out = subprocess.run(cURL, stdout=subprocess.PIPE)
                    res = out.stdout.decode('UTF-8').replace('\\', '')
                    try:
                        res = json.loads(res)
                    except JSONDecodeError:
                        res = None
                    return res

                multiup_links = []

                server = cURL_request(
                    'curl -s https://www.multiup.org/api/get-fastest-server'
                )['server']
                selected_hosts_lst = [
                    'filerio.in', 'drop.download', 'download.gg', 'uppit.com',
                    'uploadbox.io'
                ]
                limit_n = len(all_links)
                for x in selected_hosts_lst:
                    if args.number:
                        if int(args.number) <= limit_n:
                            selected_hosts_lst.remove(x)
                            continue
                    if file_size > more_links['multiup'][x]['limit']:
                        selected_hosts_lst.remove(x)
                    else:
                        limit_n += 1
                if not selected_hosts_lst:
                    return

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
                        multiup_links.append(link)
                        console.print(f'[[{dp.g}] OK [/{dp.g}]]', link)

                driver.quit()

                return multiup_links

            if batch:
                batch_links = mirroredto(driver, batch)
            else:
                batch_links = multiup(driver, batch)

            return batch_links

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

        return results

    def style_output(args, LINKs: dict) -> Union[list, str]:
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

    def uploader(self, args) -> Union[list, str]:
        start_time = time.time()
        signal.signal(signal.SIGINT,
                      KeyboardInterruptHandler.keyboardInterruptHandler)

        with open(f'{Config.DATA_PATH}/servers_data.json') as j:
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
        # links = PyMirror._match_links(links_raw)

        if args.more_links is True:
            file_resolved = str(Path(rfile).resolve())
            try:
                urls = PyMirror.more_links(args, file_resolved)
            except WebDriverException as e:
                PyMirror.SeleniumExceptionInfo(e)

            hosts = [
                MoreLinks(file_resolved).filepizza,
                MoreLinks(file_resolved).usaupload,
                MoreLinks(file_resolved).filesharego,
                MoreLinks(file_resolved).expirebox,
                MoreLinks(file_resolved).filepost
            ]

            if args.number:
                if int(args.number) < len(all_links) + 5:
                    left = int(args.number) - len(all_links)
                    hosts = hosts[:left]

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
        print()
        run_time = time.strftime('%H:%M:%S', time.gmtime(time.time() - start_time))
        h, m, s = [int(_) for _ in run_time.split(':')]
        console.print(Panel.fit(f'[{dp.k}]Process took[{dp.k}] [{dp.y}]{h}h {m}m {s}s'))
        console.rule('END')

        return output
