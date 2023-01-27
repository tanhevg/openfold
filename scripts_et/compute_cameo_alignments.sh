#!/usr/bin/env bash
. ~/.bashrc
conda activate openfold
python ../scripts/precompute_alignments.py \
        /data/openfold/cameo/fasta_dir \
        /data/openfold/cameo/alignments \
        --uniref90_database_path /data/alphafold_data/uniref90/uniref90.fasta \
        --mgnify_database_path /data/alphafold_data/mgnify/mgy_clusters_2018_12.fa \
        --pdb70_database_path /data/alphafold_data/pdb70/pdb70 \
        --uniclust30_database_path /data/alphafold_data/uniclust30/uniclust30_2018_08/uniclust30_2018_08 \
        --bfd_database_path /data/alphafold_data/bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt \
        --mmcif_cache /data/openfold/cache/mmcif_cache.json \
        --max_seq_len 300 \
        --cpus_per_task 8 \
        --no_tasks 4