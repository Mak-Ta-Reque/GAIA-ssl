srun \
  --container-image=/netscratch/duynguyen/Docker-Image/vissl_A100.sqsh -v\
  -p RTXA6000 --ntasks=1 --gpus-per-task=2 --cpus-per-gpu=8 --mem-per-cpu=16G\
  --container-mounts=/netscratch/software:/netscratch/software:ro,/netscratch/$USER:/netscratch/$USER,/ds:/ds:ro,"`pwd`":"`pwd`" \
  --container-workdir="`pwd`" \
  --time=04:00:00 \
  bash
