#!/usr/bin/python3

"""
Clones Marlin Firmware and Configurations repositories
"""

import sys
from os import environ, chdir
from subprocess import run
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from requests import get

###############################################################################
# Marlin GitHub Repositories
###############################################################################
MARLIN_GITHUB_URL = 'https://github.com/MarlinFirmware/'
MARLIN_BRANCHES = ['2.0.x', 'bugfix-2.0.x']

LATEST_RELEASE = get(f'{MARLIN_GITHUB_URL}Marlin/releases/latest',
                     allow_redirects=True).url.split('/')[-1]
with open('/latest-release', 'w+') as latest_release:
    latest_release.write(LATEST_RELEASE)
###############################################################################
if 'MARLIN_GIT_BRANCH' in environ and \
        'WORK_DIR' in environ and \
        'FIRMWARE_BIN_DIR' in environ and \
        'MAINTAINER' in environ and \
        environ['MARLIN_GIT_BRANCH'] in MARLIN_BRANCHES:
    PROJECT_DIR = Path(environ['WORK_DIR'])
    FIRMWARE_DIR = Path(environ['FIRMWARE_BIN_DIR'])

    BRANCH = environ['MARLIN_GIT_BRANCH']
    CONFIG_BRANCH = LATEST_RELEASE if BRANCH == "2.0.x" \
        else BRANCH  # bugfix-2.0.x

    MARLIN_FIRMWARE_ZIP = f'{MARLIN_GITHUB_URL}Marlin/archive/{BRANCH}.zip'
    MARLIN_CONFIG_ZIP = \
        f'{MARLIN_GITHUB_URL}Configurations/archive/{CONFIG_BRANCH}.zip'

    fw_repo = get(MARLIN_FIRMWARE_ZIP)
    with ZipFile(BytesIO(fw_repo.content)) as fw_zip:
        fw_zip.extractall(PROJECT_DIR)

    conf_repo = get(MARLIN_CONFIG_ZIP)
    with ZipFile(BytesIO(conf_repo.content)) as conf_zip:
        conf_zip.extractall(PROJECT_DIR)

    with open(f'{FIRMWARE_DIR}/README.md', 'w+') as readme:
        readme.write(f'# Marlin Firmware: "{CONFIG_BRANCH}"\n')

    # Bootstrap PIO for most 32bit boards using STM32, Atmel AVR
    chdir(Path(f'{PROJECT_DIR}/Marlin-{BRANCH}/'))
    run(['pio', 'platform', 'install',
         'ststm32',
         'atmelavr',
         'atmelmegaavr'],
        check=True)

else:
    sys.exit('!!! ENVs FAILED !!!')
