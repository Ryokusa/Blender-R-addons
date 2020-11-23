# 「プロパティ」エリア → 「モディファイア」タブ
import os
import re
import struct
import math
import unicodedata
import time
import bpy
import bmesh
import mathutils
from . import common
from . import compat


# メニュー等に項目追加
def menu_func(self, context):
    ob = context.active_object
    if ob:
        if ob.type == 'MESH':
            me = ob.data
            if len(ob.modifiers):
                self.layout.operator('object.forced_modifier_apply', icon_value=common.kiss_icon())


@compat.BlRegister()
class CNV_OT_forced_modifier_apply(bpy.types.Operator):
    bl_idname = 'object.forced_modifier_apply'
    bl_label = "Force Modifiers"
    bl_description = "Will force any modifiers if the mesh has shape keys."
    bl_options = {'REGISTER', 'UNDO'}
    
    is_applies = bpy.props.BoolVectorProperty(name="Apply Modifier", size=32, options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return len(ob.modifiers)

    def invoke(self, context, event):
        ob = context.active_object
        if len(ob.modifiers) == 0:
            return {'CANCELLED'}

        for index, mod in enumerate(ob.modifiers):
            if index >= 32: # luvoid : can only apply 32 modifiers at once.
                self.report(type={'WARNING'}, message="Can only apply the first 32 modifiers at once.")
                break
            if mod.show_viewport:
                self.is_applies[index] = True

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        prefs = common.preferences()
        self.layout.prop(prefs, 'custom_normal_blend', icon='SNAP_NORMAL', slider=True)
        self.layout.label(text="Apply")
        ob = context.active_object

        for index, mod in enumerate(ob.modifiers):
            if index >= 32: # luvoid : can only apply 32 modifiers at once.
                break
            icon = 'MOD_%s' % mod.type.replace('DECIMATE','DECIM').replace('SOFT_BODY','SOFT').replace('PARTICLE_SYSTEM','PARTICLES').replace('_SPLIT','SPLIT').replace('_PROJECT','PROJECT').replace('_DEFORM','DEFORM').replace('_SIMULATION','SIM').replace('_EDIT','').replace('_MIX','').replace('_PROXIMITY','').replace('_PAINT','PAINT')
            try:
                self.layout.prop(self, 'is_applies', text=mod.name, index=index, icon=icon)
            except:
                self.layout.prop(self, 'is_applies', text=mod.name, index=index, icon='MODIFIER')

    def execute(self, context):
        ob = context.active_object

        # 対象が一つも無い場合はキャンセル扱いとする
        if not any(self.is_applies):
            self.report(type={'INFO'}, message="There are no applicable modifiers, so cancel")
            return {'CANCELLED'}

        custom_normal_blend = common.preferences().custom_normal_blend
        bpy.ops.object.mode_set(mode='OBJECT')

        me = ob.data
        is_shaped = bool(me.shape_keys)

        pre_selected_objects = context.selected_objects[:]
        pre_mode = ob.mode

        if is_shaped:
            pre_relative_keys = [s.relative_key.name for s in me.shape_keys.key_blocks]
            pre_active_shape_key_index = ob.active_shape_key_index

            shape_names = [s.name for s in me.shape_keys.key_blocks]
            shape_deforms = []
            for shape in me.shape_keys.key_blocks:
                shape_deforms.append([shape.data[v.index].co.copy() for v in me.vertices])

            ob.active_shape_key_index = len(me.shape_keys.key_blocks) - 1
            for i in me.shape_keys.key_blocks[:]:
                ob.shape_key_remove(ob.active_shape_key)

            new_shape_deforms = []
            for shape_index, deforms in enumerate(shape_deforms):

                temp_ob = ob.copy()
                temp_me = me.copy()
                temp_ob.data = temp_me
                compat.link(context.scene, temp_ob)
                try:
                    for vert in temp_me.vertices:
                        vert.co = deforms[vert.index].copy()

                    override = context.copy()
                    override['object'] = temp_ob
                    for index, mod in enumerate(temp_ob.modifiers):
                        if self.is_applies[index]:
                            try:
                                bpy.ops.object.modifier_apply(override, modifier=mod.name)
                            except:
                                ob.modifiers.remove(mod)

                    new_shape_deforms.append([v.co.copy() for v in temp_me.vertices])
                finally:
                    common.remove_data(temp_ob)
                    common.remove_data(temp_me)

        if ob.active_shape_key_index != 0:
            ob.active_shape_key_index = 0
            me.update()

        copy_modifiers = ob.modifiers[:]

        for index, mod in enumerate(copy_modifiers):
            if index >= 32: # luvoid : can only apply 32 modifiers at once.
                break
            if self.is_applies[index] and mod.type != 'ARMATURE':

                if mod.type == 'MIRROR':
                    for vg in ob.vertex_groups[:]:
                        replace_list = ((r'\.L$', ".R"), (r'\.R$', ".L"), (r'\.l$', ".r"), (r'\.r$', ".l"), (r'_L$', "_R"), (r'_R$', "_L"), (r'_l$', "_r"), (r'_r$', "_l"))
                        for before, after in replace_list:
                            mirrored_name = re.sub(before, after, vg.name)
                            if mirrored_name not in ob.vertex_groups:
                                ob.vertex_groups.new(name=mirrored_name)

                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except:
                    #ob.modifiers.remove(mod)
                    self.report(type={'WARNING'}, message="Could not apply '%s' modifier \"%s\"" % (mod.type, mod.name) )
                    

        arm_ob = None
        for mod in ob.modifiers:
            if mod.type == "ARMATURE":
                arm_ob = mod.object

        if arm_ob:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.mode_set(mode='OBJECT')

            arm = arm_ob.data
            arm_pose = arm_ob.pose

            pose_quats = {}
            for bone in arm.bones:
                pose_bone = arm_pose.bones[bone.name]

                bone_quat = bone.matrix_local.to_quaternion()
                pose_quat = pose_bone.matrix.to_quaternion()
                result_quat = compat.mul(pose_quat, bone_quat.inverted())

                pose_quats[bone.name] = result_quat.copy()

            custom_normals = []
            for loop in me.loops:
                vert = me.vertices[loop.vertex_index]
                no = vert.normal.copy()

                total_weight = 0.0
                for vge in vert.groups:
                    vg = ob.vertex_groups[vge.group]
                    try:
                        pose_quats[vg.name]
                    except KeyError:
                        continue
                    total_weight += vge.weight

                total_quat = mathutils.Quaternion()
                for vge in vert.groups:
                    vg = ob.vertex_groups[vge.group]
                    try:
                        total_quat = total_quat.slerp(pose_quats[vg.name], vge.weight / total_weight)
                    except KeyError:
                        pass

                no.rotate(total_quat)
                custom_normals.append(no)

        for index, mod in enumerate(copy_modifiers):
            if index >= 32: # luvoid : can only apply 32 modifiers at once.
                break
            if self.is_applies[index] and mod.type == 'ARMATURE':
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except:
                    #ob.modifiers.remove(mod)
                    self.report(type={'WARNING'}, message="Could not apply '%s' modifier \"%s\"" % (mod.type, mod.name) )

        compat.set_active(context, ob)

        if is_shaped:

            for deforms in new_shape_deforms:
                if len(me.vertices) != len(deforms):
                    self.report(type={'ERROR'}, message="Since the number of vertices has changed due to mirror etc, The shape key can not be stored. Please undo with Ctrl + Z or other.")
                    return {'CANCELLED'}

            for shape_index, deforms in enumerate(new_shape_deforms):

                bpy.ops.object.shape_key_add(from_mix=False)
                shape = ob.active_shape_key
                shape.name = shape_names[shape_index]

                for vert in me.vertices:
                    shape.data[vert.index].co = deforms[vert.index].copy()

            for shape_index, shape in enumerate(me.shape_keys.key_blocks):
                shape.relative_key = me.shape_keys.key_blocks[pre_relative_keys[shape_index]]

            ob.active_shape_key_index = pre_active_shape_key_index

        for temp_ob in pre_selected_objects:
            compat.set_select(temp_ob, True)
        bpy.ops.object.mode_set(mode=pre_mode)

        if arm_ob:
            for i, loop in enumerate(me.loops):
                vert = me.vertices[loop.vertex_index]
                no = vert.normal.copy()

                try:
                    custom_rot = mathutils.Vector((0.0, 0.0, 1.0)).rotation_difference(custom_normals[i])
                except:
                    continue
                original_rot = mathutils.Vector((0.0, 0.0, 1.0)).rotation_difference(no)
                output_rot = original_rot.slerp(custom_rot, custom_normal_blend)

                output_no = mathutils.Vector((0.0, 0.0, 1.0))
                output_no.rotate(output_rot)

                custom_normals[i] = output_no
            me.use_auto_smooth = True
            me.normals_split_custom_set(custom_normals)

        return {'FINISHED'}
