#!/usr/bin/env bash
. ~/.bashrc
conda activate openfold
python run_docker.py \
    --data.cameo.root /data/openfold/cameo/ \
    --data.roda.root /data/openfold/roda_flat/ \
    --data.pdb.root /data/openfold/rcsb_mmcif/ \
    --openfold.output_dir /data/openfold/out/ \
    --openfold.deepseed_dir /data/openfold/deepseed/ \
    --openfold.cache_dir /data/openfold/cache/ \
    --docker.gpus all \
    python train_openfold.py \
        /mnt/roda/pdb/data \
        /mnt/roda/pdb/alignments \
        /mnt/pdb/structures/all/mmCIF \
        /mnt/openfold/out \
        2021-10-10 \
        --gpus 4 \
        --deepspeed_config_path /mnt/openfold/deepseed/deepspeed_config.json \
        --template_release_dates_cache_path /mnt/openfold/cache/mmcif_cache.json \
        --train_chain_data_cache_path /mnt/openfold/cache/chain_data_cache.json \
        --precision bf16 \
        --replace_sampler_ddp True \
        --checkpoint_every_epoch \
        --obsolete_pdbs_file_path /mnt/pdb/status/obsolete.dat \
        --seed 42 \
        --log_every_n_steps 1\
        --logger True \
#	--debug \
#	--debug_host ld-mjeste2 \
#	--debug_port 12345
