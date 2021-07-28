from docker import DockerClient, errors
from os import listdir, path
from pathlib import Path
import yaml

WORK_DIR = str(Path('/home/b0bby/code/Marlin-Firmware-Builder/'))
PROJECT = 'Marlin-Firmware-Builder'
MAINTAINER = 'B0bbyD1g1tal'
MARLIN_GIT_BRANCH = 'bugfix-2.0.x'  # '2.0.x'
CONF = Path(f'{WORK_DIR}/Configurations/config/examples/')
IMAGE = f'{MAINTAINER}/{PROJECT}'.lower()
TAG = 'stable' if MARLIN_GIT_BRANCH == '2.0.x' else 'latest'
PRINTERS_YAML = './PRINTERS.yml'


def generate_printer_list(yaml_file=PRINTERS_YAML):
    """
    Generates PRINTERS.yml
    """

    PRINTERS = {}
    manufacturers = listdir(CONF)
    manufacturers.sort()

    for manufacturer in manufacturers:
        PRINTERS[f'{manufacturer}'] = {}

        printers = [printer for printer in
                    listdir(Path(f'{CONF}/{manufacturer}')) if
                    Path(f'{CONF}/{manufacturer}/{printer}').is_dir()]
        printers.sort()

        for printer in printers:
            boards = [board for board in
                      listdir(Path(f'{CONF}/{manufacturer}/{printer}')) if
                      Path(
                          f'{CONF}/{manufacturer}/{printer}/{board}').is_dir()]
            boards.sort()

            PRINTERS[f'{manufacturer}'][f'{printer}'] = boards if boards \
                else []

    with open(yaml_file, 'w+') as printer_list:
        printer_list.write(yaml.dump(PRINTERS))


def build_image():
    """
    Builds docker image
    """
    args = {'MARLIN_GIT_BRANCH': '2.0.x'} if MARLIN_GIT_BRANCH == '2.0.x' \
        else {}
    print(f'Building {IMAGE}:{TAG} ...\nMarlin branch:{MARLIN_GIT_BRANCH}\n')
    try:
        image, output = docker_py.images.build(path=WORK_DIR,
                                               tag=f'{IMAGE}:{TAG}',
                                               buildargs=args,
                                               pull=True,
                                               nocache=True,
                                               rm=True,
                                               encoding='gzip')

        print('\n'.join([str(line) for line in output]))

    except errors.BuildError as build_error:
        raise Exception(build_error)
    except errors.APIError as api_error:
        raise Exception(api_error)


def push_image():
    """
    Pushes to registry
    """

    def dockerhub_auth(token_file='./ACCESS_TOKEN'):
        """
        Authentication against hub.docker.com
        """
        with open(token_file, 'r') as token:
            access_token = token.read().strip()

        return {'username': MAINTAINER.lower(),
                'password': f'{access_token}'}

    print(f'Pushing {IMAGE}:{TAG} ...\n')
    try:
        output = docker_py.images.push(repository=IMAGE,
                                       tag=TAG,
                                       auth_config=dockerhub_auth())
        print(output)
    except errors.APIError as api_error:
        raise Exception(api_error)


def build_matrix(yaml_file=PRINTERS_YAML, readme_file='./firmware/README.md'):
    with open(yaml_file, 'r') as yml:
        firmware = yaml.load(yml, Loader=yaml.FullLoader)

    with open(readme_file, 'w+') as readme:
        readme.write('# Marlin Firmware Printers\n')

        for manufacturer in firmware.keys():
            readme.write(f'## {manufacturer}\n')

            for printer in firmware[manufacturer]:
                readme.write(f'### {printer}\n')

                envs = {'MANUFACTURER': f'{manufacturer}',
                        'MODEL': f'{printer}',
                        'BOARD': ''}

                vols = {str(Path(f'{WORK_DIR}/firmware/')): {
                    'bind': '/firmware/',
                    'mode': 'rw'}}

                boards = firmware[manufacturer][printer]
                if boards:
                    for board in boards:
                        readme.write(f' * {board}')

                        envs.update({'BOARD': f'{board}'})

                        docker_py.containers.run(
                            f'{IMAGE}:{TAG}',
                            environment=envs,
                            volumes=vols,
                            auto_remove=True,
                            # shm_size='2G',
                            # mem_limit='1g',
                            tty=True,
                            remove=True)

                else:
                    docker_py.containers.run(
                        f'{IMAGE}:{TAG}',
                        environment=envs,
                        volumes=vols,
                        auto_remove=True,
                        # shm_size='2G',
                        # mem_limit='1g',
                        tty=True,
                        remove=True)


docker_py = DockerClient.from_env()

build_image()
push_image()

generate_printer_list()
build_matrix()
