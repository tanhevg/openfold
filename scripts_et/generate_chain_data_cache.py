# python scripts_et/generate_chain_data_cache.py
#       /bmm/data/rcsb/data/structures/all/mmCIF/
#       chain_data_cache.json
#       --cluster_file clusters-by-entity-40-no-comp.txt
#       --no_workers 12

import argparse
import gzip
from functools import partial
import json
import logging
from multiprocessing import Pool
import os

import sys
sys.path.append(".") # an innocent hack to get this to run from the top level

from tqdm import tqdm

from openfold.data.mmcif_parsing import parse 
from openfold.np import protein, residue_constants


def parse_file(
    f, 
    args,
    chain_cluster_size_dict
):
    file_ext = f.split('.')
    file_id = file_ext[0]
    ext = '.' + '.'.join(file_ext[1:])
    out = {}
    cif_path = os.path.join(args.data_dir, f)
    with gzip.open(cif_path, 'rt') if ext == '.cif.gz' else open(cif_path, "r") as fp:
        mmcif_string = fp.read()
    mmcif = parse(file_id=file_id, mmcif_string=mmcif_string)
    if mmcif.mmcif_object is None:
        logging.info(f"Could not parse {f}. Skipping...")
        return {}
    else:
        mmcif = mmcif.mmcif_object

    for chain_id, seq in mmcif.chain_to_seqres.items():
        full_name = "_".join([file_id, chain_id])
        local_data = {}
        local_data["release_date"] = mmcif.header["release_date"]
        local_data["seq"] = seq
        local_data["resolution"] = mmcif.header["resolution"]

        if (chain_cluster_size_dict is not None):
            mmcif_chain_id = mmcif.author_to_entity_id[chain_id]
            cluster_key = f"{file_id.upper()}_{mmcif_chain_id}"
            cluster_size = chain_cluster_size_dict.get(cluster_key, -1)
            local_data["cluster_size"] = cluster_size
        out[full_name] = local_data

    return out


def main(args):
    chain_cluster_size_dict = None
    if(args.cluster_file is not None):
        chain_cluster_size_dict = {}
        with open(args.cluster_file, "r") as fp:
            clusters = [l.strip() for l in fp.readlines()]

        for cluster in clusters:
            chain_ids = cluster.split()
            cluster_len = len(chain_ids)
            for chain_id in chain_ids:
                chain_id = chain_id.upper()
                chain_cluster_size_dict[chain_id] = cluster_len
   
    files = list(os.listdir(args.data_dir))
    files = [f for f in files if '.cif' in f]
    fn = partial(
        parse_file, 
        args=args,
        chain_cluster_size_dict=chain_cluster_size_dict,
    )
    data = {}
    if args.no_workers > 0:
        with Pool(processes=args.no_workers) as p:
            with tqdm(total=len(files)) as pbar:
                for d in p.imap_unordered(fn, files, chunksize=args.chunksize):
                    data.update(d)
                    pbar.update()
    else:
        with tqdm(total=len(files)) as pbar:
            for d in map(fn, files):
                data.update(d)
                pbar.update()

    with open(args.output_path, "w") as fp:
        fp.write(json.dumps(data, indent=4))

    if args.dump_console:
        print(json.dumps(data, indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "data_dir", type=str, help="Directory containing mmCIF or PDB files"
    )
    parser.add_argument(
        "output_path", type=str, help="Path for .json output"
    )
    parser.add_argument(
        "--cluster_file", type=str, default=None,
        help=(
            "Path to a cluster file (e.g. PDB40), one cluster "
            "({PROT1_ID}_{CHAIN_ID} {PROT2_ID}_{CHAIN_ID} ...) per line. "
            "Chains not in this cluster file will NOT be filtered by cluster "
            "size."
        )
    )
    parser.add_argument(
        "--no_workers", type=int, default=0,
        help="Number of workers to use for parsing"
    )
    parser.add_argument(
        "--chunksize", type=int, default=10,
        help="How many files should be distributed to each worker at a time"
    )
    parser.add_argument('--dump_console', action='store_true', default=False, help="Dump output to console")

    args = parser.parse_args()

    main(args)

