#!/usr/bin/env bash
. ~/.bashrc
module load gcc/8.2.0
conda activate openfold
rm -rf /data/openfold/out/log/*
python train_openfold.py \
	/data/openfold/roda/data \
	/data/openfold/roda/alignments \
	/data/alphafold_data/pdb_mmcif/mmcif_files \
	/data/openfold/out \
	2021-10-10 \
	--gpus 4 \
	--deepspeed_config_path ./deepspeed_config.json \
	--template_release_dates_cache_path /data/openfold/roda/mmcif_cache.json \
	--precision bf16 \
	--replace_sampler_ddp True \
	--checkpoint_every_epoch \
	--train_chain_data_cache_path /data/openfold/roda/chain_data_cache.json \
	--obsolete_pdbs_file_path /data/alphafold_data/pdb_mmcif/obsolete.dat \
	--seed 42 \
	--log_every_n_steps 1\
	--logger True \
#	--debug \
#	--debug_host ld-mjeste2 \
#	--debug_port 12345
