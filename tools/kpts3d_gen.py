# Run as blender python script. Command: blender3 --background -P tools/kpts3d_gen.py
# 注意需要配置 blender 的环境
import bpy
import os
import time
import sys
import json
import glob
import numpy as np

def clear_scene_and_import_fbx(filepath):
    """
    Clear the whole scene and import fbx file into the empty scene.

    :param filepath: filepath for fbx file
    """
    # redirect blender output info
    logfile = 'blender_render.log'
    open(logfile, 'w').close()
    old = os.dup(1)
    sys.stdout.flush()
    os.close(1)
    os.open(logfile, os.O_WRONLY)
    
    bpy.ops.better_import.fbx(filepath=filepath)

    os.close(1)
    os.dup(old)
    os.close(old)

def get_joint3d_positions(frame_idx):
    """
    Get joint3d positions for current armature and given frame index.

    :param frame_idx: frame index
    :param joint_names: list of joint names
    :return: dict, {'kpts_3d': [x1, y1, z1, x2, y2, z2, ...]}
    """
    bpy.context.scene.frame_set(frame_idx)
    posebones = bpy.data.objects['Armature'].pose.bones
    out_dict = {'kpts_3d': []}
    index = 0
    kpts_name_index = {}
    for name in posebones.keys():
        name_base = name.split(':')[-1]
        val = list(posebones[name].head)
        out_dict['kpts_3d'].extend(val)
        kpts_name_index[name_base] = index
        index += 1
    out_dict['kpts_index'] = kpts_name_index
    return out_dict

def kpts3d_gen_from_fbx(fbx_name):
    if not fbx_name.endswith('.fbx'):
        print(f"{fbx_name} is not a standard fbx file, please it")
        return
    
    base_name = os.path.basename(fbx_name).replace('.fbx','')
    save_dir = os.path.join(f'./data/result/{base_name}/json')
    os.makedirs(save_dir,exist_ok=True)
    
    clear_scene_and_import_fbx(fbx_name)
    
    action_index = len(bpy.data.actions)-1
    frame_end = bpy.data.actions[action_index].frame_range[1]
    print("total frame:",frame_end,bpy.data.actions[action_index].frame_range)
    print(frame_end,bpy.data.actions.keys())
    
    for index in range(1,int(frame_end) + 1):
        kpts3d_dict = get_joint3d_positions(index)
        save_path = os.path.join(save_dir, '%08d.json' % index)
        with open(save_path, 'w') as file:
            json.dump(kpts3d_dict, file,indent=4)
    nr_files = glob.glob(os.path.join(save_dir,'*.json'))
    nr_files.sort(key=lambda x:int(os.path.basename(x).split('.')[0]))
    motion = []
    for index,json_name in enumerate(nr_files):
        with open(os.path.join(json_name),'r') as f:
            info = json.load(f)
            joint = np.array(info['kpts_3d']).reshape((-1, 3))
        motion.append(joint[:, :])
    motion = np.stack(motion, axis=2)
    
    save_fname_npy = os.path.join(f'./data/result/{base_name}/{base_name}.npy')
    np.save(save_fname_npy, motion)
    
    armature = bpy.data.objects['Armature']
    bpy.data.objects.remove(armature)
    bpy.context.view_layer.update()
    

def kpts3d_gen(fbx_dir='./data/fbx'):
    fbx_names = glob.glob(os.path.join(fbx_dir,'*.fbx'))
    for fbx_name in fbx_names:
        kpts3d_gen_from_fbx(fbx_name)

if __name__ == '__main__':
    kpts3d_gen()