# 为了输出一个拼接的视频片段 python tools/vidoe_cat.py 
import glob
import os
import cv2
import numpy as np

if __name__ == '__main__':
    video_dir= './data/result/Crouch To Standing/videos'
    vidoes_names = glob.glob(os.path.join(video_dir,'*.mp4'))
    vidoes_names_2d = [x for x in vidoes_names if '2d' in x]
    vidoes_names_3d = [x for x in vidoes_names if '3d' in x]
    assert len(vidoes_names_2d) == len(vidoes_names_3d)
    vidoes_names_2d.sort(key=lambda x:int(os.path.basename(x).split('_')[-1].split('.')[0]))
    vidoes_names_3d.sort(key=lambda x:int(os.path.basename(x).split('_')[-1].split('.')[0]))
    shape_2d = [1080,1920]
    shape_3d = [480,640]
    scale = 2
    shape_2d_small = [x//scale for x in shape_2d]
    shape_3d_small = [x//scale for x in shape_3d]
    cap_2d_list = []
    cap_3d_list = []
    for name_2d,name_3d in zip(vidoes_names_2d,vidoes_names_3d):
        cap2d = cv2.VideoCapture(name_2d)
        cap3d = cv2.VideoCapture(name_3d)
        cap_2d_list.append(cap2d)
        cap_3d_list.append(cap3d)
        frame_count = int(cap2d.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_count_3d = int(cap3d.get(cv2.CAP_PROP_FRAME_COUNT))
        assert frame_count == frame_count_3d
    os.makedirs('./img',exist_ok=True)
    os.makedirs('./video',exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out3d = cv2.VideoWriter(os.path.join('./video','3d_demo.mp4'), fourcc, 30, (1600,1920))
    out2d = cv2.VideoWriter(os.path.join('./video','2d_demo.mp4'), fourcc, 30, (4800,4320))
    
    for frame_idx in range(frame_count):
        img_combine_3d = np.zeros(shape=(shape_3d_small[0]*8,shape_3d_small[1]*5,3),dtype=np.uint8)
        img_combine_2d = np.zeros(shape=(shape_2d_small[0]*8,shape_2d_small[1]*5,3),dtype=np.uint8)
        print(img_combine_2d.shape,img_combine_3d.shape)
        for cam_id in range(len(cap_2d_list)):
            ret_2d, frame2d = cap_2d_list[cam_id].read()
            ret_3d, frame3d = cap_3d_list[cam_id].read()
            if not ret_2d:
                continue
            if not ret_3d:
                continue
            frame2d = cv2.resize(frame2d,(shape_2d_small[1],shape_2d_small[0]))
            frame3d = cv2.resize(frame3d,(shape_3d_small[1],shape_3d_small[0]))
            x_i = cam_id % 5
            y_i = cam_id // 5
            x_start_2d = x_i * shape_2d_small[1]
            x_end_2d = (x_i+1)*shape_2d_small[1]
            y_start_2d = y_i * shape_2d_small[0] 
            y_end_2d = (y_i+1)*shape_2d_small[0]
            img_combine_2d[y_start_2d:y_end_2d,x_start_2d:x_end_2d,:] = frame2d
            
            x_start_3d = x_i * shape_3d_small[1]
            x_end_3d = (x_i+1)*shape_3d_small[1]
            y_start_3d = y_i * shape_3d_small[0] 
            y_end_3d = (y_i+1)*shape_3d_small[0]
            img_combine_3d[y_start_3d:y_end_3d,x_start_3d:x_end_3d,:] = frame3d
        
        cv2.imwrite(f'./img/around_2d_{frame_idx}.png',img_combine_2d)
        cv2.imwrite(f'./img/around_3d_{frame_idx}.png',img_combine_3d)
        out3d.write(img_combine_3d)
        out2d.write(img_combine_2d)
        # break
    out3d.release()
    out2d.release()
            
            