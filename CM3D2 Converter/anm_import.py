import re
import struct
import math
import unicodedata
import time
import bpy
import bmesh
import mathutils
import os
from . import common
from . import compat


# メインオペレーター
@compat.BlRegister()
class CNV_OT_import_cm3d2_anm(bpy.types.Operator):
    bl_idname = 'import_anim.import_cm3d2_anm'
    bl_label = "CM3D2 Animation (.anm)"
    bl_description = "Loads a CM3D2 .anm file."
    bl_options = {'REGISTER'}

    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".anm"
    filter_glob = bpy.props.StringProperty(default="*.anm", options={'HIDDEN'})

    scale = bpy.props.FloatProperty(name="Scale", default=5, min=0.1, max=100, soft_min=0.1, soft_max=100, step=100, precision=1, description="The scale at the time of import.")
    set_frame_rate = bpy.props.BoolProperty(name="Set Framerate", default=True, description="Change the scene's render settings to 60 fps")

    remove_pre_animation = bpy.props.BoolProperty(name="Remove previous Animation", default=True)
    set_frame = bpy.props.BoolProperty(name="Set Frame", default=True)
    ignore_automatic_bone = bpy.props.BoolProperty(name="Exclude Twister Bones", default=True)

    is_location = bpy.props.BoolProperty(name="Position", default=True)
    is_rotation = bpy.props.BoolProperty(name="Rotation", default=True)
    is_scale = bpy.props.BoolProperty(name="Bigger/Smaller", default=False)

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob and ob.type == 'ARMATURE':
            return True
        return False

    def invoke(self, context, event):
        prefs = common.preferences()
        if prefs.anm_default_path:
            self.filepath = common.default_cm3d2_dir(prefs.anm_default_path, None, "anm")
        else:
            self.filepath = common.default_cm3d2_dir(prefs.anm_import_path, None, "anm")
        self.scale = prefs.scale
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):

        self.layout.prop(self, 'scale')
        self.layout.prop(self, 'set_frame_rate', icon='RENDER_ANIMATION')

        box = self.layout.box()
        box.prop(self, 'remove_pre_animation', icon='DISCLOSURE_TRI_DOWN')
        box.prop(self, 'set_frame', icon='NEXT_KEYFRAME')
        box.prop(self, 'ignore_automatic_bone', icon='X')

        box = self.layout.box()
        box.label(text="Animation data to load")
        column = box.column(align=True)
        column.prop(self, 'is_location', icon=compat.icon('CON_LOCLIKE'))
        column.prop(self, 'is_rotation', icon=compat.icon('CON_ROTLIKE'))
        row = column.row()
        row.prop(self, 'is_scale', icon=compat.icon('CON_SIZELIKE'))
        row.enabled = False

    def execute(self, context):
        common.preferences().anm_import_path = self.filepath

        try:
            file = open(self.filepath, 'rb')
        except:
            self.report(type={'ERROR'}, message="Failed to open the file. It's either inaccessible or the file does not exist")
            return {'CANCELLED'}

        # ヘッダー
        ext = common.read_str(file)
        if ext != 'CM3D2_ANIM':
            self.report(type={'ERROR'}, message="This is not a CM3D2 animation file.")
            return {'CANCELLED'}
        struct.unpack('<i', file.read(4))[0]

        global_flag = struct.unpack('<?', file.read(1))[0]

        anm_data = {}

        for anm_data_index in range(9**9):
            path = common.read_str(file)

            base_bone_name = path.split('/')[-1]
            if base_bone_name not in anm_data:
                anm_data[base_bone_name] = {'path': path}
                anm_data[base_bone_name]['channels'] = {}

            for channel_index in range(9**9):
                channel_id = struct.unpack('<B', file.read(1))[0]
                channel_id_str = channel_id
                if channel_id <= 1:
                    break
                anm_data[base_bone_name]['channels'][channel_id_str] = []
                channel_data_count = struct.unpack('<i', file.read(4))[0]
                for channel_data_index in range(channel_data_count):
                    frame = struct.unpack('<f', file.read(4))[0]
                    data = struct.unpack('<3f', file.read(4 * 3))

                    anm_data[base_bone_name]['channels'][channel_id_str].append({'frame': frame, 'f0': data[0], 'f1': data[1], 'f2': data[2]})

            if channel_id == 0:
                break
        
        if self.set_frame_rate:
            context.scene.render.fps = 60
        fps = context.scene.render.fps

        ob = context.active_object
        arm = ob.data
        pose = ob.pose

        if self.remove_pre_animation:
            anim = ob.animation_data
            if anim:
                if anim.action:
                    for fcurve in anim.action.fcurves:
                        anim.action.fcurves.remove(fcurve)

        max_frame = 0
        bpy.ops.object.mode_set(mode='OBJECT')
        for bone_name, bone_data in anm_data.items():

            if self.ignore_automatic_bone:
                if re.match(r"Kata_[RL]", bone_name):
                    continue
                if re.match(r"Uppertwist1_[RL]", bone_name):
                    continue
                if re.match(r"momoniku_[RL]", bone_name):
                    continue

            if bone_name not in pose.bones:
                bone_name = common.decode_bone_name(bone_name)
                if bone_name not in pose.bones:
                    continue
            bone = arm.bones[bone_name]
            pose_bone = pose.bones[bone_name]


            locs = {}
            quats = {}
            for channel_id, channel_data in bone_data['channels'].items():

                if channel_id in [100, 101, 102, 103]:
                    for data in channel_data:
                        frame = data['frame']
                        if frame not in quats:
                            quats[frame] = [None, None, None, None]

                        if channel_id == 103:
                            quats[frame][0] = data['f0']
                        elif channel_id == 100:
                            quats[frame][1] = data['f0']
                        elif channel_id == 101:
                            quats[frame][2] = data['f0']
                        elif channel_id == 102:
                            quats[frame][3] = data['f0']

                elif channel_id in [104, 105, 106]:
                    for data in channel_data:
                        frame = data['frame']
                        if frame not in locs:
                            locs[frame] = [None, None, None]

                        if channel_id == 104:
                            locs[frame][0] = data['f0']
                        elif channel_id == 105:
                            locs[frame][1] = data['f0']
                        elif channel_id == 106:
                            locs[frame][2] = data['f0']

            if self.is_location:
                for frame, loc in locs.items():
                    loc = mathutils.Vector(loc) * self.scale
                    bone_loc = bone.head_local.copy()

                    if bone.parent:
                        #loc.x, loc.y, loc.z = -loc.y, -loc.x, loc.z

                        #co.x, co.y, co.z = -co.y, co.z, co.x
                        #loc.x, loc.y, loc.z = loc.z, -loc.x, loc.y
                        mat = mathutils.Matrix(
                            [( 0,  0,  1,  0), 
                             (-1,  0,  0,  0), 
                             ( 0,  1,  0,  0),
                             ( 0,  0,  0,  1)]
                        )

                        loc = compat.mul(mat, loc)

                        bone_loc = bone_loc - bone.parent.head_local
                        bone_loc.rotate(bone.parent.matrix_local.to_quaternion().inverted())
                    else:
                        loc.x, loc.y, loc.z = loc.x, loc.z, loc.y

                    result_loc = loc - bone_loc
                    pose_bone.location = result_loc.copy()

                    pose_bone.keyframe_insert('location', frame=frame * fps, group=pose_bone.name)
                    if max_frame < frame * fps:
                        max_frame = frame * fps

            if self.is_rotation:
                for frame, quat in quats.items():
                    quat = mathutils.Quaternion(quat)
                    bone_quat = bone.matrix.to_quaternion()

                    if bone.parent:
                        #quat.w, quat.x, quat.y, quat.z = quat.w, quat.y, quat.x, -quat.z

                        ##rot.w, rot.y, -rot.z, -rot.x = rot.w, rot.x, rot.y, rot.z
                        quat.w, quat.x, quat.y, quat.z = quat.w, -quat.z, quat.x, -quat.y
                        
                        # (pq)^=q^p^
                        #pq = mathutils.Quaternion((quat.w, -quat.z, quat.x, -quat.y))
                        #I = pq.conjugated()
                        #I.identity()
                        #p = compat.mul(quat, pq.conjugated()).conjugated()
                        ##p = compat.mul(pq.conjugated(), quat).conjugated()
                        ##p = compat.mul(quat, pq.inverted()).inverted()
                        ##p = compat.mul(pq.inverted(), quat).inverted()
                        #p.make_compatible(I)
                        #print(p.to_euler())
                        #quat = pq

                        #quat = compat.convert_opengl_to_blend_quat(quat)

                        #quat = compat.mul(quat, mat.to_quaternion())
                    else:
                        #quat = compat.convert_opengl_y_up_to_blend_z_up_quat(quat)
                        quat.w, quat.x, quat.y, quat.z = quat.w, quat.y, quat.x, -quat.z
                        
                        #fix_quat = mathutils.Euler((math.radians(90), math.radians(90), 0.0), 'XYZ').to_quaternion()
                        #fix_quat2 = mathutils.Euler((0.0, math.radians(-90), 0.0), 'XYZ').to_quaternion()
                        fix_quat = mathutils.Euler((math.radians(90), math.radians(90), 0.0), 'XYZ').to_quaternion()
                        fix_quat2 = mathutils.Euler((0.0, 0.0, 0.0), 'XYZ').to_quaternion()
                        quat = compat.mul(fix_quat, quat)

                    result_quat = compat.mul(bone_quat.inverted(), quat)
                    pose_bone.rotation_quaternion = result_quat.copy()

                    pose_bone.keyframe_insert('rotation_quaternion', frame=frame * fps, group=pose_bone.name)
                    if max_frame < frame * fps:
                        max_frame = frame * fps

        if self.set_frame:
            context.scene.frame_start = 0
            context.scene.frame_end = max_frame
            context.scene.frame_set(0)

        return {'FINISHED'}


# メニューに登録する関数
def menu_func(self, context):
    self.layout.operator(CNV_OT_import_cm3d2_anm.bl_idname, icon_value=common.kiss_icon())
