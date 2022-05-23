srun \
  --container-image=/netscratch/duynguyen/Docker-Image/vissl_A100.sqsh -v\
  -p RTXA6000 --ntasks=1 --gpus-per-task=2 --cpus-per-gpu=8 --mem-per-cpu=16G\
  --container-mounts=/netscratch/software:/netscratch/software:ro,/netscratch/$USER:/netscratch/$USER,/ds:/ds:ro,"`pwd`":"`pwd`" \
  --container-workdir="`pwd`" \
  --time=04:00:00 \
  CUDA_VISIBLE_DEVICES=0,1 bash tools/dist_train.sh app/dynmoco/configs/local/ar50to101_10pc_bs64_200_epoch.py 2
