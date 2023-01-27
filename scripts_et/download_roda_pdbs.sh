#!/bin/bash

# Downloads .cif files matching the RODA alignments. Outputs a list of 
# RODA alignments for which .cif files could not be found..
if [[ $# != 3 ]]; then
    echo "usage: ./download_roda_pdbs.sh /bmm/data/rcsb/data/structures/all/mmCIF <roda_data_dir> <roda_pdb_alignment_dir>"
    exit 1
fi

PDB_DIR=$1
RODA_DATA_DIR=$2
RODA_ALIGNMENT_DIR=$3


for d in $(find $RODA_ALIGNMENT_DIR -mindepth 1 -maxdepth 1 -type d); do
    BASENAME=$(basename $d)
    PDB_ID=$(echo $BASENAME | cut -d '_' -f 1)
    CIF_PATH="${PDB_DIR}/${PDB_ID}.cif.gz"
    if [[ -f $CIF_PATH ]]; then
        OUT_PATH="${RODA_DATA_DIR}/${PDB_ID}.cif"
        if [[ ! -f $OUT_PATH ]]; then
            gunzip -c ${CIF_PATH} > ${OUT_PATH}
        fi
    else
        echo $d
    fi
done
