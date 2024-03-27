# 「3Dビュー」エリア → ポーズモード → Ctrl+A (ポーズ → 適用)
import bpy
import mathutils
from . import common
from . import compat


# メニュー等に項目追加
def menu_func(self, context):
    self.layout.separator()
    self.layout.operator("pose.apply_prime_field", icon_value=common.kiss_icon())
    self.layout.operator("pose.copy_prime_field", icon_value=common.kiss_icon())


@compat.BlRegister()
class CNV_OT_copy_prime_field(bpy.types.Operator):
    bl_idname = "pose.copy_prime_field"
    bl_label = "Copy Prime Field"
    bl_description = "Copies the visual pose of the selected object to the prime field of the active object"
    bl_options = {"REGISTER", "UNDO"}

    # is_apply_armature_modifier = bpy.props.BoolProperty(name="Apply Armature Modifier", default=True )
    # is_deform_preserve_volume  = bpy.props.BoolProperty(name="Preserve Volume"        , default=True )
    # is_keep_original           = bpy.props.BoolProperty(name="Keep Original"          , default=True )
    # is_swap_prime_field        = bpy.props.BoolProperty(name="Swap Prime Field"       , default=False)
    # is_bake_drivers            = bpy.props.BoolProperty(name="Bake Drivers"           , default=False, description="Enable keyframing of driven properties, locking sliders and twist bones for final apply")

    is_only_selected = bpy.props.BoolProperty(name="Only Selected", default=True)
    is_key_location = bpy.props.BoolProperty(name="Key Location", default=True)
    is_key_rotation = bpy.props.BoolProperty(name="Key Rotation", default=True)
    is_key_scale = bpy.props.BoolProperty(name="Key Scale", default=True)
    is_apply_prime = bpy.props.BoolProperty(
        name="Apply Prime", default=False, options={"HIDDEN"}
    )

    @classmethod
    def poll(cls, context):
        target_ob, source_ob = common.get_target_and_source_ob(context)
        if target_ob and source_ob:
            return True
        else:
            return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "is_only_selected")
        self.layout.prop(self, "is_key_location")
        self.layout.prop(self, "is_key_rotation")
        self.layout.prop(self, "is_key_scale")

    def execute(self, context):
        target_ob, source_ob = common.get_target_and_source_ob(context)
        pose = target_ob.pose
        arm = target_ob.data

        pre_selected_pose_bones = context.selected_pose_bones
        pre_mode = target_ob.mode

        bpy.ops.object.mode_set(mode="POSE")
        bpy.ops.pose.select_all(action="SELECT")
        bpy.ops.pose.constraints_clear()

        if not target_ob.pose_library:
            bpy.ops.poselib.new()
            poselib = target_ob.pose_library

        consts = []
        bones = pre_selected_pose_bones if self.is_only_selected else pose.bones
        for bone in bones:
            source_bone = source_ob.pose.bones.get(bone.name)
            if source_bone:
                if self.is_key_location or self.is_key_rotation:
                    const = bone.constraints.new("COPY_TRANSFORMS")
                    const.target = source_ob
                    const.subtarget = source_bone.name
                    consts.append(const)
                if self.is_key_scale:
                    const = bone.constraints.new("LIMIT_SCALE")
                    const.owner_space = "LOCAL"
                    const.use_transform_limit = True
                    const.use_min_x = True
                    const.use_min_y = True
                    const.use_min_z = True
                    const.use_max_x = True
                    const.use_max_y = True
                    const.use_max_z = True
                    const.min_x = source_bone.scale.x
                    const.min_y = source_bone.scale.y
                    const.min_z = source_bone.scale.z
                    if source_ob.data.get("is T Stance"):
                        source_prime_scale = mathutils.Vector(
                            source_bone.get("prime_scale", (1, 1, 1))
                        )
                        const.min_x *= source_prime_scale.x
                        const.min_y *= source_prime_scale.y
                        const.min_z *= source_prime_scale.x
                    if arm.get("is T Stance"):
                        target_prime_scale = mathutils.Vector(
                            bone.get("prime_scale", (1, 1, 1))
                        )
                        const.min_x /= target_prime_scale.x
                        const.min_y /= target_prime_scale.y
                        const.min_z /= target_prime_scale.z
                    const.max_x = const.min_x
                    const.max_y = const.min_y
                    const.max_z = const.min_z
                    consts.append(const)

        # if True:
        #    return {'CANCELLED'}

        for i in range(2):
            is_prime_frame = not bool(i % 2) if arm.get("is T Stance") else bool(i % 2)
            pose_name = "__prime_field_pose" if is_prime_frame else "__base_field_pose"
            if self.is_apply_prime:
                is_prime_frame = not is_prime_frame

            # if self.is_key_scale and is_prime_frame:
            #    for const in consts:
            #        if const.type == 'LIMIT_SCALE':
            #            const.mute = not is_prime_frame
            #    bpy.ops.pose.visual_transform_apply()
            #    for bone in pose.bones:
            #        bone.keyframe_insert(data_path='scale', frame=i, group=bone.name)
            #    for const in consts:
            #        if const.type == 'LIMIT_SCALE':
            #            const.mute = is_prime_frame

            for const in consts:
                const.mute = not is_prime_frame
            if is_prime_frame:
                bpy.ops.pose.visual_transform_apply()
            else:
                bpy.ops.pose.transforms_clear()
            for bone in pose.bones:
                if self.is_key_location:
                    bone.keyframe_insert(data_path="location", frame=i, group=bone.name)
                if self.is_key_rotation:
                    bone.keyframe_insert(
                        data_path="rotation_euler", frame=i, group=bone.name
                    )
                    bone.keyframe_insert(
                        data_path="rotation_quaternion", frame=i, group=bone.name
                    )
                if self.is_key_scale:  # and not is_prime_frame:
                    bone.keyframe_insert(data_path="scale", frame=i, group=bone.name)
                bpy.ops.poselib.pose_add(frame=i, name=pose_name)

        bpy.ops.pose.constraints_clear()
        bpy.ops.pose.transforms_clear()
        target_ob.animation_data_clear()

        bpy.ops.pose.select_all(action="DESELECT")
        if pre_selected_pose_bones:
            for bone in pre_selected_pose_bones:
                arm.bones[bone.name].select = True

        if pre_mode:
            bpy.ops.object.mode_set(mode=pre_mode)

        return {"FINISHED"}
