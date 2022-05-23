import logging
import torch
logging.warning('cuda version: {}'.format(torch.version.cuda))
import os
print(torch.__version__)
logging.warning('CUDA_PATH: {}'.format(os.environ["CUDA_PATH"]))
logging.warning('CUDA_HOME: {}'.format(os.environ["CUDA_HOME"]))
