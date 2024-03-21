# 「プロパティ」エリア → 「アーマチュアデータ」タブ
import bpy
import mathutils
from . import common
from . import compat
from .translations.pgettext_functions import *


# メニュー等に項目追加
def menu_func(self, context):
    import re

    ob = context.active_object
    if not ob or ob.type != "ARMATURE":
        return

    arm = ob.data
    is_boxed = False

    bone_data_count = 0
    if "BoneData:0" in arm and "LocalBoneData:0" in arm:
        for key in arm.keys():
            if re.search(r"^(Local)?BoneData:\d+$", key):
                bone_data_count += 1
    enabled_clipboard = False
    clipboard = context.window_manager.clipboard
    if "BoneData:" in clipboard and "LocalBoneData:" in clipboard:
        enabled_clipboard = True
    if bone_data_count or enabled_clipboard:
        if not is_boxed:
            box = self.layout.box()
            box.label(text="CM3D2用", icon_value=common.kiss_icon())
            is_boxed = True

        col = box.column(align=True)
        row = col.row(align=True)
        row.label(text="ボーン情報", icon="CONSTRAINT_BONE")
        sub_row = row.row()
        sub_row.alignment = "RIGHT"
        if bone_data_count:
            sub_row.label(text=str(bone_data_count), icon="CHECKBOX_HLT")
        else:
            sub_row.label(text="0", icon="CHECKBOX_DEHLT")
        row = col.row(align=True)
        row.operator(
            "object.copy_armature_bone_data_property", icon="COPYDOWN", text="コピー"
        )
        row.operator(
            "object.paste_armature_bone_data_property", icon="PASTEDOWN", text="貼付け"
        )
        row.operator("object.remove_armature_bone_data_property", icon="X", text="")

    flag = False
    for bone in arm.bones:
        if not flag and re.search(r"[_ ]([rRlL])[_ ]", bone.name):
            flag = True
        if not flag and bone.name.count("*") == 1:
            if re.search(r"\.([rRlL])$", bone.name):
                flag = True
        if flag:
            if not is_boxed:
                box = self.layout.box()
                box.label(text="CM3D2用", icon_value=common.kiss_icon())
                is_boxed = True

            col = box.column(align=True)
            col.label(text="ボーン名変換", icon="SORTALPHA")
            row = col.row(align=True)
            row.operator(
                "armature.decode_cm3d2_bone_names",
                text="CM3D2 → Blender",
                icon="BLENDER",
            )
            row.operator(
                "armature.encode_cm3d2_bone_names",
                text="Blender → CM3D2",
                icon_value=common.kiss_icon(),
            )
            break

    if bone_data_count:
        col = box.column(align=True)
        col.label(text="Armature Operators", icon=compat.icon("OUTLINER_OB_ARMATURE"))
        col.operator(
            "object.add_cm3d2_twist_bones",
            text="Connect Twist Bones",
            icon=compat.icon("CONSTRAINT_BONE"),
        )
        col.operator(
            "object.cleanup_scale_bones",
            text="Cleanup Scale Bones",
            icon=compat.icon("X"),
        )

    if "is T Stance" in arm:
        if not is_boxed:
            box = self.layout.box()
            box.label(text="CM3D2用", icon_value=common.kiss_icon())
            is_boxed = True

        col = box.column(align=True)
        if arm["is T Stance"]:
            pose_text = "Armature State: Primed"
        else:
            pose_text = "Armature State: Normal"
        col.label(text=pose_text, icon="POSE_HLT")
        col.enabled = bpy.ops.poselib.apply_pose.poll()

        row = col.row(align=True)

        sub_row = row.row(align=True)
        op = sub_row.operator(
            "poselib.apply_pose", icon="ARMATURE_DATA", text="Original"
        )  # , depress=(context.scene.frame_current % 2 == arm['is T Stance']))
        op.pose_index = arm["is T Stance"]
        # if context.scene.frame_current % 2 == op.value:
        #    sub_row.enabled = False

        sub_row = row.row(align=True)
        op = sub_row.operator(
            "poselib.apply_pose",
            icon=compat.icon("OUTLINER_DATA_ARMATURE"),
            text="Pose data",
        )  # , depress=(context.scene.frame_current % 2 != arm['is T Stance']))
        op.pose_index = not arm["is T Stance"]
        # if context.scene.frame_current % 2 == op.value:
        #    sub_row.enabled = False

        row = col.row(align=True)

        sub_row = row.row(align=True)
        sub_row.operator_context = "EXEC_DEFAULT"
        op = sub_row.operator(
            "pose.apply_prime_field",
            icon=compat.icon("FILE_REFRESH"),
            text="Swap Prime Field",
        )
        op.is_swap_prime_field = True


@compat.BlRegister()
class CNV_OT_copy_armature_bone_data_property(bpy.types.Operator):
    bl_idname = "object.copy_armature_bone_data_property"
    bl_label = "ボーン情報をコピー"
    bl_description = "カスタムプロパティのボーン情報をクリップボードにコピーします"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob:
            if ob.type == "ARMATURE":
                arm = ob.data
                if "BoneData:0" in arm and "LocalBoneData:0" in arm:
                    return True
        return False

    def execute(self, context):
        output_text = ""
        ob = context.active_object.data
        pass_count = 0
        if "BaseBone" in ob:
            output_text += "BaseBone:" + ob["BaseBone"] + "\n"
        for i in range(99999):
            name = "BoneData:" + str(i)
            if name in ob:
                output_text += "BoneData:" + ob[name] + "\n"
            else:
                pass_count += 1
            if 10 < pass_count:
                break
        pass_count = 0
        for i in range(99999):
            name = "LocalBoneData:" + str(i)
            if name in ob:
                output_text += "LocalBoneData:" + ob[name] + "\n"
            else:
                pass_count += 1
            if 10 < pass_count:
                break
        context.window_manager.clipboard = output_text
        self.report(type={"INFO"}, message="ボーン情報をクリップボードにコピーしました")
        return {"FINISHED"}


@compat.BlRegister()
class CNV_OT_paste_armature_bone_data_property(bpy.types.Operator):
    bl_idname = "object.paste_armature_bone_data_property"
    bl_label = "ボーン情報を貼付け"
    bl_description = "カスタムプロパティのボーン情報をクリップボードから貼付けます"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob:
            if ob.type == "ARMATURE":
                clipboard = context.window_manager.clipboard
                if "BoneData:" in clipboard and "LocalBoneData:" in clipboard:
                    return True
        return False

    def execute(self, context):
        ob = context.active_object.data
        pass_count = 0
        for i in range(99999):
            name = "BoneData:" + str(i)
            if name in ob:
                del ob[name]
            else:
                pass_count += 1
            if 10 < pass_count:
                break
        pass_count = 0
        for i in range(99999):
            name = "LocalBoneData:" + str(i)
            if name in ob:
                del ob[name]
            else:
                pass_count += 1
            if 10 < pass_count:
                break
        bone_data_count = 0
        local_bone_data_count = 0
        for line in context.window_manager.clipboard.split("\n"):
            if line.startswith("BaseBone:"):
                ob["BaseBone"] = line[9:]  # len('BaseData:') == 9
                continue

            if line.startswith("BoneData:"):
                if line.count(",") >= 4:
                    name = "BoneData:" + str(bone_data_count)
                    ob[name] = line[9:]  # len('BoneData:') == 9
                    bone_data_count += 1
                continue

            if line.startswith("LocalBoneData:"):
                if line.count(",") == 1:
                    name = "LocalBoneData:" + str(local_bone_data_count)
                    ob[name] = line[14:]  # len('LocalBoneData:') == 14
                    local_bone_data_count += 1

        self.report(type={"INFO"}, message="ボーン情報をクリップボードから貼付けました")
        return {"FINISHED"}


@compat.BlRegister()
class CNV_OT_remove_armature_bone_data_property(bpy.types.Operator):
    bl_idname = "object.remove_armature_bone_data_property"
    bl_label = "ボーン情報を削除"
    bl_description = "カスタムプロパティのボーン情報を全て削除します"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob:
            if ob.type == "ARMATURE":
                arm = ob.data
                if "BoneData:0" in arm and "LocalBoneData:0" in arm:
                    return True
        return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(
            text="カスタムプロパティのボーン情報を全て削除します", icon="CANCEL"
        )

    def execute(self, context):
        ob = context.active_object.data
        pass_count = 0
        if "BaseBone" in ob:
            del ob["BaseBone"]
        for i in range(99999):
            name = "BoneData:" + str(i)
            if name in ob:
                del ob[name]
            else:
                pass_count += 1
            if 10 < pass_count:
                break
        pass_count = 0
        for i in range(99999):
            name = "LocalBoneData:" + str(i)
            if name in ob:
                del ob[name]
            else:
                pass_count += 1
            if 10 < pass_count:
                break
        self.report(type={"INFO"}, message="ボーン情報を削除しました")
        return {"FINISHED"}


"""
- - - - - - For Bone Sliders - - - - - - 
"""


def get_axis_index_vector(axis_index, size=3):
    vec = mathutils.Vector.Fill(size)
    vec[axis_index] = 1
    return vec


def get_axis_order_matrix(axis_order):
    size = len(axis_order)
    mat = mathutils.Matrix.Diagonal([0] * size)
    for index, axis_index in enumerate(axis_order):
        mat[index][axis_index] = 1
    return mathutils.Matrix(mat)


def get_vector_axis_index(vec):
    length = len(vec)
    for axis_index, axis_value in enumerate(vec):
        if axis_index == length - 1:
            return axis_index
        else:
            axis_value = abs(axis_value)
            largest = True
            for i in range(axis_index + 1, length):
                if axis_value < abs(vec[i]):
                    largest = False
                    break
            if largest:
                return axis_index


def get_matrix_axis_order(mat):
    return [get_vector_axis_index(row) for row in mat]


@compat.BlRegister()
class CNV_OT_cleanup_scale_bones(bpy.types.Operator):
    bl_idname = "object.cleanup_scale_bones"
    bl_label = "Cleanup Scale Bones"
    bl_description = "Remove scale bones from the active armature object"
    bl_options = {"REGISTER", "UNDO"}

    scale = bpy.props.FloatProperty(
        name="Scale",
        default=5,
        min=0.1,
        max=100,
        soft_min=0.1,
        soft_max=100,
        step=100,
        precision=1,
        description="The amount by which the mesh is scaled when imported. Recommended that you use the same when at the time of export.",
    )

    is_keep_bones_with_children = bpy.props.BoolProperty(
        name="Keep bones with children",
        default=True,
        description="Will not remove scale bones that have children (for custom scale bones)",
    )

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob:
            arm = ob.data
        else:
            arm = None
        has_arm = arm and isinstance(arm, bpy.types.Armature)
        has_scl = False
        if has_arm:
            for bone in arm.edit_bones:
                if "_SCL_" in bone.name:
                    has_scl = True
                    break
        return has_arm and has_scl

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "is_keep_bones_with_children")

    def execute(self, context):
        ob = context.object
        arm = ob.data

        edit_bones = arm.edit_bones
        deleted_bones = {}
        for bone in edit_bones:
            if not "_SCL_" in bone.name:
                continue
            if self.is_keep_bones_with_children and len(bone.children) > 0:
                continue
            parent = edit_bones.get(bone.name.replace("_SCL_", "")) or bone.parent
            if parent:
                parent["cm3d2_scl_bone"] = True
                deleted_bones[bone.name] = parent.name
                edit_bones.remove(bone)

        for child in ob.children:
            vgroups = child.vertex_groups
            if vgroups and len(vgroups) > 0:
                for old_name, new_name in deleted_bones.items():
                    old_vgroup = vgroups.get(old_name)
                    if old_vgroup:
                        old_vgroup.name = new_name

        return {"FINISHED"}
