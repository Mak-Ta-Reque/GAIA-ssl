# standard lib
import os
import sys
import os.path as osp
import argparse
import json
import time
import shutil
import hashlib
import pdb
from collections.abc import Sequence
from copy import deepcopy
from pprint import pprint

# 3rd party lib
import torch
import torch.distributed as dist
from tqdm import tqdm

# mm lib
import mmcv
from mmcv import Config
from mmcv.runner import get_dist_info, init_dist, save_checkpoint, load_state_dict
from openselfsup.models import build_model

# gaia lib
import gaiavision
import gaiassl
from gaiavision.model_space import build_model_sampler, fold_dict


def parse_args():
    parser = argparse.ArgumentParser(description='Conduct surgury on a model checkpoint.')
    parser.add_argument('src_ckpt', help='source checkpoint file path')
    parser.add_argument('out_ckpt', help='output checkpoint file path')
    parser.add_argument('config', help='train config file path')
    parser.add_argument(
        '--launcher',
        choices=['none', 'pytorch', 'slurm', 'mpi'],
        default='none',
        help='job launcher')
    parser.add_argument('--local_rank', type=int, default=0)


    args = parser.parse_args()
    assert os.path.exists(args.src_ckpt), f'`{args.src_ckpt}` not existed.'
    # assert os.path.exists(args.label_mapping_path), f'`{args.label_mapping_path}` not existed.'
    return args


def prepare_cfg(cfg):
    # substitute dyn_bn for dyn_sync_bn
    model = cfg['model']
    for name in ('backbone', 'neck', 'rpn_head', 'roi_head'):
        m = model.get(name, None)
        if m is not None:
            if 'norm_cfg' in m.keys():
                m['norm_cfg'] = dict(type='DynBN')
    return cfg


def main():
    args = parse_args()
    print('-- Args:')
    pprint(args)
    ckpt = torch.load(args.src_ckpt, map_location='cpu')
    if 'LOCAL_RANK' not in os.environ:
        os.environ['LOCAL_RANK'] = str(args.local_rank)

    # abandon sync bn
    cfg = Config.fromfile(args.config)
    cfg = prepare_cfg(cfg)

    # init distributed env first.
    if args.launcher == 'none':
        distributed = False
    else:
        distributed = True
        init_dist(args.launcher, **cfg.dist_params)
        # re-set gpu_ids with distributed training mode
        rank, world_size = get_dist_info()
        cfg.gpu_ids = range(world_size)

    # prepare model
    model = build_model(cfg.model)
    if torch.cuda.is_available():
        model.cuda()
    # load weights from supernet
    load_state_dict(model, ckpt['state_dict'])

    model.eval()
    model.deploy() 

    # prepare model sampler
    model_sampler = build_model_sampler(cfg.train_sampler)
    model_sampler.set_mode('traverse')
    all_metas = list(model_sampler.traverse())
    metas_per_rank = all_metas[rank::world_size]

    if rank == 0:
        pbar = tqdm(total=len(metas_per_rank))
        interval = min(max(len(metas_per_rank) // 100, 1), 10)
    for n, model_meta in enumerate(metas_per_rank):
        print(model_meta)
        model_meta = fold_dict(model_meta)
        arch_meta = model_meta['arch']
        data_meta = model_meta.get('data',{'input_sahpe':224})
        model.manipulate_arch(arch_meta)
        deployed_model = deepcopy(model)

        input_shape = data_meta['input_shape']
        if not isinstance(input_shape, Sequence):
            input_shape = (3, input_shape, input_shape)
        elif isinstance(input_shape, str):
            input_shape = [int(v) for v in input_shape.strip().split(',')]

        img1 = torch.ones(()).new_empty(
            (*input_shape),
            dtype=next(deployed_model.parameters()).dtype,
            device=next(deployed_model.parameters()).device)
        img2 = torch.ones(()).new_empty(
            (*input_shape),
            dtype=next(deployed_model.parameters()).dtype,
            device=next(deployed_model.parameters()).device)
        img_cat = torch.cat((img1.unsqueeze(0), img2.unsqueeze(0)), dim=0)
        batch = img_cat.unsqueeze(0)
        
        _ = deployed_model(batch)
        
        # model_name = hashlib.md5(json.dumps(model_meta).encode('utf-8')).hexdigest()[:8]
        print(model_meta)
        dir_name = osp.dirname(args.out_ckpt[:-4])
        os.makedirs(dir_name, exist_ok=True)
        save_checkpoint(deployed_model, args.out_ckpt[:-4]+"_"+str(n)+".pth")

        if rank == 0:
            if n % interval == 0:
                pbar.update(interval)

        if n > 0:
            raise NotImplementedError

    dist.barrier()
    time.sleep(2)
    print('Done.')


if __name__ == '__main__':
    main()
