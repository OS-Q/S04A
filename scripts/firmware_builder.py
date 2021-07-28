#!/usr/bin/python3.8

"""
Bootstraps PlatformIO default environment
sets environment for the specified Model/Board
"""

from os import environ, chdir, makedirs
from subprocess import run
from pathlib import Path
from shutil import copytree, copyfile
from datetime import datetime


def extract_values(file, value, token, redundant):
    """
    Extracts values from files
    and removes redundant parts of them
    token ensures that the correct line is matched
    """
    with open(file, 'r') as text:
        return [line.strip().split()[-1].replace(redundant, '')
                for line in text if value in line and token in line][0]


BRANCH = environ["MARLIN_GIT_BRANCH"]
PROJECT_DIR = Path(environ["WORK_DIR"])
MARLIN_FW = Path(f'{PROJECT_DIR}/Marlin-{BRANCH}/')
MARLIN_CONFIGS = \
    Path(f'{PROJECT_DIR}/Configurations-'
         f'{environ["LATEST_RELEASE"] if BRANCH == "2.0.x" else BRANCH}')
###############################################################################
# Copy Configurations to Marlin PIO Project
###############################################################################
MARLIN_PRINTER_CONFIG = \
    Path(f'{MARLIN_CONFIGS}/config/examples/'
         f'{environ["MANUFACTURER"]}/{environ["MODEL"]}/{environ["BOARD"]}/')
PIO_CONFIGS = Path(f'{MARLIN_FW}/Marlin/')

copytree(MARLIN_PRINTER_CONFIG, PIO_CONFIGS,
         dirs_exist_ok=True)

###############################################################################
# Custom Config
###############################################################################
if "CUSTOM_FIRMWARE_SETTINGS" in environ and \
        environ["CUSTOM_FIRMWARE_SETTINGS"]:
    run('config-calibrator.sh', check=True)

###############################################################################
# Platform IO Environment
###############################################################################
CONFIG_H = Path(f'{MARLIN_PRINTER_CONFIG}/Configuration.h')
PINS_H = Path(f'{MARLIN_FW}/Marlin/src/pins/pins.h')

MOTHERBOARD = extract_values(CONFIG_H, 'MOTHERBOARD', '#define', 'BOARD_')
PIO_ENV = extract_values(PINS_H, MOTHERBOARD, '#include', 'env:')

print(f'{"#" * 79}\n'
      f'# {environ["MANUFACTURER"]} {environ["MODEL"]}:{environ["BOARD"]} #\n'
      f'| {MOTHERBOARD} | {PIO_ENV} |\n'
      f'{"#" * 79}\n')

###############################################################################
# Build and deliver
###############################################################################
chdir(MARLIN_FW)
run(['pio', 'run', '-e', f'{PIO_ENV}'], check=True)

###############################################################################
# Copy to firmware folder
###############################################################################
COMPILED_FW = \
    sorted(Path(f'{MARLIN_FW}/.pio/build/{PIO_ENV}/').glob('firmware*'))
FW_FILE_NAME = \
    f'{environ["MODEL"].replace(" ", "")}-{MOTHERBOARD}.' \
    f'{BRANCH}-{datetime.now().strftime("%d-%b-%y_%H%M%S")}'

makedirs(f'{environ["FIRMWARE_BIN_DIR"]}/'
         f'{environ["MANUFACTURER"]}/{environ["MODEL"]}/',
         exist_ok=True)

for firmware in COMPILED_FW:
    fw_extension = str(firmware).split('.')[-1]
    copyfile(firmware,
             Path(f'{environ["FIRMWARE_BIN_DIR"]}/'
                  f'{environ["MANUFACTURER"]}/{environ["MODEL"]}/'
                  f'{FW_FILE_NAME}.{fw_extension}'))

###############################################################################
