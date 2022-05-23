#!/bin/bash
CUDA_VISIBLE_DEVICES=0,1

DONEFILE="/tmp/install_done_${SLURM_JOBID}]"
if [[ $SLURM_LOCALID == 0 ]]; then
	# put your install commands here:
	apt update
  	pip install mmcv-full -f https://download.openmmlab.com/mmcv/dist/cu111/torch1.8.0/index.html
  	cd /netscratch/kadir/GAIA-cv
  	pip install -r requirements.txt
  	pip install -e .
  	cd /home/kadir/IML/GAIA-ssl
  	touch "${DONEFILE}"
else
	 while [[ ! -f "${DONEFILE}" ]]; do sleep 1; done
fi
