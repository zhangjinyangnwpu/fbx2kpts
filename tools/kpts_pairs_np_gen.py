# python3 tools/kpts_pairs_np_gen.py
import numpy as np
import cv2
import os
import glob
import pickle

def posxyz2xy(points,cam_dict):
    P = cam_dict['P']
    RT = cam_dict['RT']
    RT_all = P
    kp3d = np.hstack((points[:, :3], np.ones((points.shape[0], 1))))
    kp2d = RT_all @ kp3d.T
    kp2d[:, :] /= kp2d[2, :]
    kp2d = kp2d.T[:,:2]
    kp2d = np.asarray(kp2d,dtype=np.int32)

    RT_w2c = RT.copy()
    kp3d_c = RT_w2c @ kp3d.T
    kp3d_c = kp3d_c.T
    return kp2d,kp3d_c



if __name__ == '__main__':
    # load cam parm
    with open('./data/cam_parm/around_cam_parm.pickle','rb') as input_file:
        cams_dict = pickle.load(input_file)
    pose_dir = './data/result'
    pose_names = os.listdir(pose_dir)
    loss_frame_num = 0
    total_frame = 0
    for pose_name in pose_names:
        if pose_name.startswith('.'):# 过滤系统缓存文件夹
            continue
        pos_3d_fname = os.path.join(pose_dir,pose_name,f"{pose_name}.npy")
        data_pair = {}
        print(f"{pos_3d_fname} processing")
        pos_3d = np.load(pos_3d_fname)
        pos_3d = pos_3d * 10 # blender 在生成是默认使用了 cm，所以这里将其转化成 mm
        data_pair['world_3d'] = pos_3d # 准备存储世界坐标系
        frame_num = pos_3d.shape[2]
        kpts_num = pos_3d.shape[0]
        cur_loss_frame_num = 0
        cur_total_frame = 0
        for cam_name,cam_list in cams_dict.items():
            if cam_name not in data_pair.keys():
                data_pair[cam_name] = []
            for cam_data_dict in cam_list:
                cur_cam_info = {}
                pos_3d_cam = []
                pos_2d_cam = []
                for frame_idx in range(frame_num):
                    kpts_3d = pos_3d[:,:,frame_idx]
                    kpts_2d,kpts_3d_c = posxyz2xy(kpts_3d,cam_data_dict)
                    if np.min(kpts_2d[:,0]) < 0 or np.max(kpts_2d[:,0]) > 1920:
                        cur_loss_frame_num += 1
                        continue
                    if np.min(kpts_2d[:,1]) < 0 or np.max(kpts_2d[:,1]) > 1080:
                        cur_loss_frame_num += 1
                        continue
                    pos_3d_cam.append(kpts_3d_c)
                    pos_2d_cam.append(kpts_2d)
                    cur_total_frame += 1
                if len(pos_3d_cam) == 0:
                    continue
                pos_3d_cam = np.asarray(pos_3d_cam,dtype=np.float32)
                pos_2d_cam = np.asarray(pos_2d_cam,dtype=np.float32)
                pos_3d_cam = pos_3d_cam.transpose(1,2,0)
                pos_2d_cam = pos_2d_cam.transpose(1,2,0)
                cur_cam_info['2d'] = pos_2d_cam.copy()
                cur_cam_info['3d'] = pos_3d_cam.copy()
                data_pair[cam_name].append(cur_cam_info)
        loss_frame_num += cur_loss_frame_num
        total_frame += cur_total_frame
        print(f"cur miss frame number:{cur_loss_frame_num}")
        print(f"cur total frame number:{cur_total_frame}")
        save_name = pos_3d_fname.replace('.npy','_pairs.pickle')
        with open(save_name,'wb') as input_file:
            pickle.dump(data_pair,input_file)
    print(f"total miss frame number:{loss_frame_num}")
    print(f"total frame number:{total_frame}")