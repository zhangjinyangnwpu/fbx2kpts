# blender3 --background -P tools/cam_parm_gen.py
import bpy
import numpy as np
import math
import os
import pickle
from mathutils import Vector,Matrix

#---------------------------------------------------------------
# 3x4 P matrix from Blender camera
#---------------------------------------------------------------

# BKE_camera_sensor_size
def get_sensor_size(sensor_fit, sensor_x, sensor_y):
    if sensor_fit == 'VERTICAL':
        return sensor_y
    return sensor_x

# BKE_camera_sensor_fit
def get_sensor_fit(sensor_fit, size_x, size_y):
    if sensor_fit == 'AUTO':
        if size_x >= size_y:
            return 'HORIZONTAL'
        else:
            return 'VERTICAL'
    return sensor_fit

# Build intrinsic camera parameters from Blender camera data
#
# See notes on this in 
# blender.stackexchange.com/questions/15102/what-is-blenders-camera-projection-matrix-model
# as well as
# https://blender.stackexchange.com/a/120063/3581
def get_calibration_matrix_K_from_blender(camd):
    if camd.type != 'PERSP':
        raise ValueError('Non-perspective cameras not supported')
    scene = bpy.context.scene
    f_in_mm = camd.lens
    scale = scene.render.resolution_percentage / 100
    resolution_x_in_px = scale * scene.render.resolution_x
    resolution_y_in_px = scale * scene.render.resolution_y
    sensor_size_in_mm = get_sensor_size(camd.sensor_fit, camd.sensor_width, camd.sensor_height)
    sensor_fit = get_sensor_fit(
        camd.sensor_fit,
        scene.render.pixel_aspect_x * resolution_x_in_px,
        scene.render.pixel_aspect_y * resolution_y_in_px
    )
    pixel_aspect_ratio = scene.render.pixel_aspect_y / scene.render.pixel_aspect_x
    if sensor_fit == 'HORIZONTAL':
        view_fac_in_px = resolution_x_in_px
    else:
        view_fac_in_px = pixel_aspect_ratio * resolution_y_in_px
    pixel_size_mm_per_px = sensor_size_in_mm / f_in_mm / view_fac_in_px
    s_u = 1 / pixel_size_mm_per_px
    s_v = 1 / pixel_size_mm_per_px / pixel_aspect_ratio

    # Parameters of intrinsic calibration matrix K
    u_0 = resolution_x_in_px / 2 - camd.shift_x * view_fac_in_px
    v_0 = resolution_y_in_px / 2 + camd.shift_y * view_fac_in_px / pixel_aspect_ratio
    skew = 0 # only use rectangular pixels

    K = Matrix(
        ((s_u, skew, u_0),
        (   0,  s_v, v_0),
        (   0,    0,   1)))
    return K

# Returns camera rotation and translation matrices from Blender.
# 
# There are 3 coordinate systems involved:
#    1. The World coordinates: "world"
#       - right-handed
#    2. The Blender camera coordinates: "bcam"
#       - x is horizontal
#       - y is up
#       - right-handed: negative z look-at direction
#    3. The desired computer vision camera coordinates: "cv"
#       - x is horizontal
#       - y is down (to align to the actual pixel coordinates 
#         used in digital images)
#       - right-handed: positive z look-at direction
def get_3x4_RT_matrix_from_blender(cam):
    # bcam stands for blender camera
    R_bcam2cv = Matrix(
        ((1, 0,  0),
        (0, -1, 0),
        (0, 0, -1)))

    # Transpose since the rotation is object rotation, 
    # and we want coordinate rotation
    # R_world2bcam = cam.rotation_euler.to_matrix().transposed()
    # T_world2bcam = -1*R_world2bcam @ location
    #
    # Use matrix_world instead to account for all constraints
    location, rotation = cam.matrix_world.decompose()[0:2]
    R_world2bcam = rotation.to_matrix().transposed()

    # Convert camera location to translation vector used in coordinate changes
    # T_world2bcam = -1*R_world2bcam @ cam.location
    # Use location from matrix_world to account for constraints:     
    T_world2bcam = -1*R_world2bcam @ location

    # Build the coordinate transform matrix from world to computer vision camera
    R_world2cv = R_bcam2cv@R_world2bcam
    T_world2cv = R_bcam2cv@T_world2bcam

    #print(R_world2cv)
    #print(T_world2cv)
    
    # put into 3x4 matrix
    RT = Matrix((
        R_world2cv[0][:] + (T_world2cv[0],),
        R_world2cv[1][:] + (T_world2cv[1],),
        R_world2cv[2][:] + (T_world2cv[2],)
        ))
    return RT

def point_cloud(ob_name, coords, edges=[], faces=[]):
    # Create new mesh and a new object
    me = bpy.data.meshes.new(ob_name)
    ob = bpy.data.objects.new(ob_name, me)
    # Make a mesh from a list of vertices/edges/faces
    me.from_pydata(coords, edges, faces)

    # Display name and update the mesh
    ob.show_name = True
    me.update()
    return ob

def look_at(obj_camera, point):
    loc_camera = obj_camera.location
    # loc_camera = obj_camera.matrix_world.to_translation()

    direction = point - loc_camera
    # point the cameras '-Z' and use its 'Y' as up
    rot_quat = direction.to_track_quat('-Z', 'Y')

    # assume we're using euler rotation
    obj_camera.rotation_euler = rot_quat.to_euler()

def get_around_RT():
    # 确定场地信息
    x_range = [-10, 10] # -10m to 10m
    y_range = [-8, 8]# -8m to 8m
    pos_dict = {}
    if 'cam_around' not in pos_dict.keys():
        pos_dict['cam_around'] = []
    view_count = 0
    for z in [1.2]: # z 的高度不变
        for _,x in enumerate(np.linspace(x_range[0],x_range[1],20)):
            y = (1 - x**2/(abs(x_range[0])**2)) * (abs(y_range[0])**2)
            y = math.sqrt(y)
            pos_x = x * 1000 / div
            pos_y = y * 1000 / div
            pos_z = z * 1000 / div
            view_count += 1
            cam_dict_cur = {'x':pos_x,'y':pos_y,'z':pos_z,'view_id':view_count}
            pos_dict['cam_around'].append(cam_dict_cur.copy())
            print(view_count)
            
        for _,x in enumerate(np.linspace(x_range[1],x_range[0],20)):
            y = (1 - x**2/(abs(x_range[0])**2)) * (abs(y_range[0])**2)
            y = math.sqrt(y)
            pos_x = x * 1000 / div
            pos_y = -y * 1000 / div
            pos_z = z * 1000 / div
            view_count += 1
            
            cam_dict_cur = {'x':pos_x,'y':pos_y,'z':pos_z,'view_id':view_count}
            pos_dict['cam_around'].append(cam_dict_cur.copy())
            print(view_count)
    print(f"total view num:{view_count}")
    return pos_dict

def get_3x4_P_matrix_from_blender(cam):
    K = get_calibration_matrix_K_from_blender(cam.data)
    RT = get_3x4_RT_matrix_from_blender(cam)
    return K@RT, K, RT

if __name__ == '__main__':
    div = 1
    cube = bpy.data.objects['Cube']
    target = cube.location
    target[0] = 0 / div
    target[1] = 0 / div
    target[2] = 1200 / div # 在原点高 1.2 米处设置标识
    cam_dict = get_around_RT()
    cam_dict_save = {}
    for cam_name,cam_list in cam_dict.items():
        if cam_name not in cam_dict_save.keys():
            cam_dict_save[cam_name] = []
        for cam_id,cam_data in enumerate(cam_list):
            camera_data = bpy.data.cameras.new(name=f'{cam_name}_{cam_id}')
            camera_data.lens = 30
            cam = bpy.data.objects.new(f'{cam_name}_{cam_id}', camera_data)
            bpy.context.scene.collection.objects.link(cam)
            cam.location = (cam_data['x'], cam_data['y'], cam_data['z'])
            look_at(cam, target)
            bpy.context.view_layer.update()
            P, K, RT = get_3x4_P_matrix_from_blender(cam)
            P = np.asarray(P)
            K = np.asarray(K)
            RT = np.asarray(RT)
            cur_cam_info = {'P':P,'K':K,'RT':RT,'cam_name':cam_name,'cam_id':cam_id,'cam_data':cam_data}
            cam_dict_save[cam_name].append(cur_cam_info)
    with open('./data/cam_parm/around_cam_parm.pickle','wb') as output:
        pickle.dump(cam_dict_save,output)