# python scripts_et/generate_mmcif_cache.py
#       /bmm/data/rcsb/data/structures/all/mmCIF
#       mmcif_cache.json
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


def parse_file(f, args):
    file_ext = f.split('.')
    file_id = file_ext[0]
    cif_path = os.path.join(args.mmcif_dir, f)
    with gzip.open(cif_path, 'rt') if f.endswith('.cif.gz') else open(cif_path, "r") as cif_file:
        mmcif_string = cif_file.read()
    mmcif = parse(file_id=file_id, mmcif_string=mmcif_string)
    if mmcif.mmcif_object is None:
        logging.info(f"Could not parse {f}. Skipping...")
        return {}
    else:
        mmcif = mmcif.mmcif_object

    local_data = {}
    local_data["release_date"] = mmcif.header["release_date"]

    chain_ids, seqs = list(zip(*mmcif.chain_to_seqres.items()))
    local_data["chain_ids"] = chain_ids
    local_data["seqs"] = seqs
    local_data["no_chains"] = len(chain_ids)

    local_data["resolution"] = mmcif.header["resolution"]

    return {file_id: local_data}


def main(args):
    files = [f for f in os.listdir(args.mmcif_dir) if ".cif" in f]
    fn = partial(parse_file, args=args)
    data = {}
    with Pool(processes=args.no_workers) as p:
        with tqdm(total=len(files)) as pbar:
            for d in p.imap_unordered(fn, files, chunksize=args.chunksize):
                data.update(d)
                pbar.update()

    with open(args.output_path, "w") as fp:
        fp.write(json.dumps(data, indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mmcif_dir", type=str, help="Directory containing mmCIF files"
    )
    parser.add_argument(
        "output_path", type=str, help="Path for .json output"
    )
    parser.add_argument(
        "--no_workers", type=int, default=4,
        help="Number of workers to use for parsing"
    )
    parser.add_argument(
        "--chunksize", type=int, default=10,
        help="How many files should be distributed to each worker at a time"
    )

    args = parser.parse_args()

    main(args)
