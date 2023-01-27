import argparse
import os
import re
import signal
from functools import partial
from typing import Tuple

import docker
from docker import types
import logging
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).absolute().parent.parent/'openfold'))
from utils.logger import setup_logging

_RE_DASHES = re.compile(r'^-*')
_ROOT_MOUNT_DIRECTORY = '/mnt/'


def _parse_mount_spec(spec: str) -> types.Mount:
    writeable = spec[0] == '*'
    if writeable:
        spec = spec[1:]
    source_path, target_path = spec.split(':')
    if not os.path.exists(source_path):
        raise ValueError(f'Failed to find source directory "{source_path}" to '
                         'mount in Docker container.')
    logging.info('Mounting %s -> %s', source_path, target_path)
    mount = types.Mount(target_path, source_path, type='bind', read_only=not writeable)
    return mount

def parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default="openfold", help="Name of docker image to run")
    parser.add_argument("--user", default=f'{os.geteuid()}:{os.getegid()}',
                 help="UID:GID with which to run the Docker container. The output directories "
                      "will be owned by this user:group. By default, this is the current user. "
                      "Valid options are: uid or uid:gid, non-numeric values are not recognised "
                      "by Docker unless that user has been created within the container.")
    parser.add_argument("--gpus", help="Gpu devices to use in the docker container. "
                                       "Either a comma separated list of CUDA devices, such as 'cuda:0,cuda:1', "
                                       "or 'all'. If not specified, GPUs will not be used.")
    parser.add_argument("--mounts", nargs='*',
                 help="A list of mount specifications, formatted as '[*]<host_dir>:<docker_dir>'. "
                      "The optional star at the beginning indicates writeable mount "
                      "(i.e. the mount is read only by default). "
                      "<host_dir> is a path to mount source; it can be relative. "
                      "<docker_dir> is an absolute path to mount target in the docker container; must be absolute."
                      "Example: '--mounts /data/alignments:/mnt/alignments */data/openfold/output:/mnt/openfold/out'.")
    parser.add_argument("--env", nargs='*',
                 help="A list of environment specifications, <name>=<value>, to pass to the docker container."
                      "Example: '--env NAME1=VALUE1 NAME2=VALUE2'")
    # add_argument("docker_cmd_line", action='store_true', required=True)
    parser.add_argument("--cmd", nargs=argparse.REMAINDER,
                 help="openfold script to run in docker container, with arguments")
    args = parser.parse_args(args)
    return args

def _build_mounts(mount_specs):
    mounts = []
    if mount_specs is not None:
        for spec in mount_specs:
            mounts.append(_parse_mount_spec(spec))
    return mounts

def _build_env(env_specs):
    env = {}
    if env_specs is not None:
        for spec in env_specs:
            k, v = spec.split('=')
            logging.info(f"Environment {k}={v}")
            env[k] = v
    return env

def main():
    setup_logging()
    args = parse_args()
    logging.info(f"Args = {args}")
    mounts = _build_mounts(args.mounts)
    client = docker.from_env()
    env = {}
    if args.gpus:
        env['NVIDIA_VISIBLE_DEVICES'] = args.gpus
    env.update(_build_env(args.env))
    container = client.containers.run(
        image=args.image,
        command=['python'] + args.cmd,
        runtime='nvidia' if args.gpus else None,
        remove=True,
        detach=True,
        mounts=mounts,
        user=args.user,
        environment=env)

    # Add signal handler to ensure CTRL+C also stops the running container.
    signal.signal(signal.SIGINT,
                  lambda unused_sig, unused_frame: container.kill())

    for line in container.logs(stream=True):
        logging.info(line.strip().decode('utf-8'))


def test_args():
    args = parse_args(["--mounts", "*/data/openfold/cameo:/mnt/cameo", "/data/alphafold_data:/mnt/alignments",
        "/data/openfold/cache:/mnt/openfold/cache",
    "--env", "SLURM_JOB_NUM_NODES=2", "SLURM_NODEID=0",
    "--cmd", "scripts/precompute_alignments.py",
        "/mnt/cameo/fasta_dir", 
        "/mnt/cameo/alignments", 
        "--uniref90_database_path", "/mnt/alignments/uniref90/uniref90.fasta", 
        "--mgnify_database_path", "/mnt/alignments/mgnify/mgy_clusters_2018_12.fa", 
        "--pdb70_database_path", "/mnt/alignments/pdb70/pdb70", 
        "--uniclust30_database_path", "/mnt/alignments/uniclust30/uniclust30_2018_08/uniclust30_2018_08", 
        "--bfd_database_path", "/mnt/alignments/bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt", 
        "--mmcif_cache", "/mnt/openfold/cache/mmcif_cache.json", 
        "--cpus_per_task", "8", 
        "--no_tasks", "4"])
    print(args)

if __name__ == '__main__':
    main()
    # test_args()