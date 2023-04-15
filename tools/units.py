
import numpy as np
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import math
from math import sin,cos

from kpts_config import (
    config_kpts_index_name,
    config_kpts_name_index,
    connection_info_kpts,
)
import cv2
import io
from PIL import Image

def draw3d_kpts(kpts_data,get_img=False):
    center = kpts_data[0,:] 
    kpts_data = kpts_data - center[None,:]
    gs = gridspec.GridSpec(1, 1)
    ax = plt.subplot(gs[0], projection='3d')
    len_v = 1000
    ax.set_xlim3d(-len_v, len_v)
    ax.set_xlabel('x')
    ax.set_ylim3d(-len_v, len_v)
    ax.set_ylabel('y')
    ax.set_zlim3d(-len_v, len_v)
    ax.set_zlabel('z')
    kpts_num = kpts_data.shape[0]
    
    for i in range(kpts_num):
        if 'Left' in config_kpts_index_name[i]:
            color = 'blue'
        elif 'Right' in config_kpts_index_name[i]:
            color = 'red'
        else:
            color = 'green'
        ax.scatter3D(*kpts_data[i], color=color,s=2)
        # ax.text(*kpts_data[i], i, color='r')
    for conn in connection_info_kpts:
        start = conn[0]
        end = conn[1]
        start_point = kpts_data[config_kpts_name_index[start]]
        end_point = kpts_data[config_kpts_name_index[end]]
        x = np.array([start_point[0],end_point[0]])
        y = np.array([start_point[1],end_point[1]])
        z = np.array([start_point[2],end_point[2]])
        if 'Left' in start:
            color = 'blue'
        elif 'Right' in start:
            color = 'red'
        else:
            color = 'green'
        ax.plot(x, y, z, lw=1, color = color)
    ax.set_aspect('auto')
    ax.view_init(azim=-90,elev=-90)
    if not get_img:
        plt.show()
    else:
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        canve = np.frombuffer(buf.getvalue(), dtype=np.uint8)
        buf.close()
        canve = cv2.imdecode(canve, 1)
        return canve

def draw2d_kpts(kpts_data,get_img=False):
    kpts_data = np.asarray(kpts_data,dtype=np.int32)
    h = 1080
    w = 1920
    img = np.zeros(shape=(h,w,3),dtype=np.uint8)
    lcolor = (255,0,0) # Blue in bgr
    rcolor = (0,0,255) # Red in bgr
    mcolor = (0,255,0) # Green in bgr
    kpts_num = kpts_data.shape[0]
    for i in range(kpts_num):
        if 'Left' in config_kpts_index_name[i]:
            color = lcolor
        elif 'Right' in config_kpts_index_name[i]:
            color = rcolor
        else:
            color = mcolor
        cv2.circle(img,kpts_data[i],radius=2,color=color,thickness=-1)
        # cv2.putText(img,str(i),kpts_data[i],1, 1, (0,255,0), 4)
    for conn in connection_info_kpts:
        start = conn[0]
        end = conn[1]
        start_point = kpts_data[config_kpts_name_index[start]]
        end_point = kpts_data[config_kpts_name_index[end]]
        if 'Left' in start:
            color = lcolor
        elif 'Right' in start:
            color = rcolor
        else:
            color = mcolor
        cv2.line(img,start_point,end_point,color=color,thickness=1)
    if not get_img:
        img_show = Image.fromarray(img)
        img_show.show()
    else:
        canve = img
        return canve