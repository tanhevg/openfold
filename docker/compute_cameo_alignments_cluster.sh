#!/usr/bin/env bash
ssh gpu1 "cd ~/code/openfold/docker; nohup ./compute_cameo_alignments.sh 2 0 >~/data/openfold/log/cameo_alignments_1.log 2>&1 &"
ssh gpu2 "cd ~/code/openfold/docker; nohup ./compute_cameo_alignments.sh 2 1 >~/data/openfold/log/cameo_alignments_2.log 2>&1 &"
