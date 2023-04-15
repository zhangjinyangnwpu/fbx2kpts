# python tools/kpts_pairs_video_gen.py
import pickle
import os
import cv2
import numpy as np
from PIL import Image
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from units import draw3d_kpts,draw2d_kpts
import tqdm
from joblib.parallel import Parallel,delayed

def draw_single_view(name_id,cam_name,cam_id,cam_data,output_data_dir):
    print(name_id,cam_name,cam_id)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    cap3d_writer = cv2.VideoWriter(os.path.join(output_data_dir,f"{name_id}_3d_{cam_name}_{cam_id}.mp4"), fourcc, 30.0, (640,480))
    cap2d_writer = cv2.VideoWriter(os.path.join(output_data_dir,f"{name_id}_2d_{cam_name}_{cam_id}.mp4"), fourcc, 30.0, (1920,1080))
    kpts_3d = cam_data['3d']
    kpts_2d = cam_data['2d']
    start_idx = 0
    end_idx = kpts_3d.shape[2]
    print(f"{name_id} cam:{cam_name}, cam id:{cam_id}",kpts_3d.shape,kpts_2d.shape)
    print(f"start {start_idx}, end {end_idx}")
    
    for idx in tqdm.tqdm(range(start_idx,end_idx)):
        img_3d_cur = draw3d_kpts(kpts_3d[:,:,idx],get_img=True)
        img_2d_cur = draw2d_kpts(kpts_2d[:,:,idx],get_img=True)
        cap3d_writer.write(img_3d_cur)
        cap2d_writer.write(img_2d_cur)
        # break
    cap3d_writer.release()
    cap2d_writer.release()

if __name__ == '__main__':
    data_froot = "./data/result"
    data_names = os.listdir(data_froot)
    pos_fname_pickles = []
    for data_name in data_names:
        if data_name.startswith('.'):# 过滤系统缓存文件夹
            continue
        pos_fname_pickle = os.path.join(data_froot,data_name,f"{data_name}_pairs.pickle")
        pos_fname_pickles.append(pos_fname_pickle)
    
    cam_dict_all = {}
    for vertify_data_fname in pos_fname_pickles:
        base_name = vertify_data_fname.split('/')[-2]
        with open(vertify_data_fname,'rb') as input_file:
            pos_dict = pickle.load(input_file)
        data_show_dict = {}
        for cam_name,cam_list in pos_dict.items():
            if cam_name == 'world_3d':
                continue
            if cam_name not in data_show_dict.keys():
                data_show_dict[cam_name] = [{} for _ in range(len(cam_list))]
            for cam_id,cam_data in enumerate(cam_list):
                data_show_dict[cam_name][cam_id] = {}
                data_show_dict[cam_name][cam_id]['3d'] = cam_data["3d"]
                data_show_dict[cam_name][cam_id]['2d'] = cam_data["2d"]
                # print(base_name,cam_name,cam_id,data_show_dict[cam_name][cam_id]['3d'].shape)
        cam_dict_all[base_name] = data_show_dict
    
    
    tasks = []
    for name_id,cam_dict in cam_dict_all.items():
        if name_id == 'Crouch To Standing':
            continue
        output_data_dir = os.path.join(data_froot,name_id,"videos")
        os.makedirs(output_data_dir,exist_ok=True)
        # show cam 2d and 3d
        for cam_name,cam_list in cam_dict.items():
            for cam_id,cam_data in enumerate(cam_list):
                tasks.append(delayed(draw_single_view)(name_id,cam_name,cam_id,cam_data,output_data_dir))
        Parallel(n_jobs=7, verbose=1)(tasks)
