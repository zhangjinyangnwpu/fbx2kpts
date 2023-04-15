# Run as blender python script. Command: blender3 --background -P tools/get_fbx_all_connection.py
import bpy
import os
import time
import sys
import json
import glob
import numpy as np
from pprint import pprint


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

if __name__ == '__main__':
    fbx_name = './data/fbx/Crouch To Standing.fbx'
    clear_scene_and_import_fbx(fbx_name)
    posebones = bpy.data.objects['Armature'].pose.bones
    num = 0
    conns = []
    for bone in posebones:
        if bone.parent:
            # print(f"{num} conn info:", bone.name,bone.parent.name)
            c1 = bone.parent.name.split(':')[-1]
            c2 = bone.name.split(':')[-1]
            num += 1
            conns.append([c1,c2])
    pprint(conns)