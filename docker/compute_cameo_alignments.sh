#!/usr/bin/env bash
. ~/.bashrc
conda activate openfold
if [[ $# -eq 0 ]]; then
    SLURM_JOB_NUM_NODES=0
    SLURM_NODEID=0
elif [[ $# -eq 2 ]]
    SLURM_JOB_NUM_NODES=$1
    SLURM_NODEID=$2
else
    echo "Expecting either 0 or 2 arguments; got $#"
    exit 1
fi

python run_docker.py \
    --mounts */data/openfold/cameo:/mnt/cameo /data/alphafold_data:/mnt/alignments \
        /data/openfold/cache:/mnt/openfold/cache \
    --env "SLURM_JOB_NUM_NODES=${SLURM_JOB_NUM_NODES}" "SLURM_NODEID=${SLURM_NODEID}" \
    --cmd scripts/precompute_alignments.py \
        /mnt/cameo/fasta_dir \
        /mnt/cameo/alignments \
        --uniref90_database_path /mnt/alignments/uniref90/uniref90.fasta \
        --mgnify_database_path /mnt/alignments/mgnify/mgy_clusters.fa \
        --pdb70_database_path /mnt/alignments/pdb70/pdb70 \
        --uniclust30_database_path /mnt/alignments/uniclust30/uniclust30_2018_08/uniclust30_2018_08 \
        --bfd_database_path /mnt/alignments/bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt \
        --mmcif_cache /mnt/openfold/cache/mmcif_cache.json \
        --max_seq_len 300 \
        --cpus_per_task 8 \
        --no_tasks 4