CUDA_VISIBLE_DEVICES=0,1
git clone https://github.com/GAIA-vision/GAIA-cv
cd GAIA-cv
pip install -r requirements.txt
pip install -e .
pip install mmcv-full -f 
