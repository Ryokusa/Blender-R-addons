# 「3Dビュー」エリア → ポーズモード → Ctrl+A (ポーズ → 適用)
import bpy
import mathutils
from bpy_extras import anim_utils
from . import common
from . import compat


PRIME_FIELD_POSE_NAME = "__prime_field_pose"
BASE_FIELD_POSE_NAME = "__base_field_pose"


def _pose_action_name_at_index(arm, index: int) -> str:
    is_t_stance = bool(arm.get("is T Stance"))
    is_prime_frame = (not bool(index % 2)) if is_t_stance else bool(index % 2)
    return PRIME_FIELD_POSE_NAME if is_prime_frame else BASE_FIELD_POSE_NAME


def _replace_action(name: str) -> bpy.types.Action:
    existing = bpy.data.actions.get(name)
    if existing is not None:
        bpy.data.actions.remove(existing)
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    return action


def _assign_action(ob: bpy.types.Object, action: bpy.types.Action | None) -> None:
    if action is None:
        if ob.animation_data:
            ob.animation_data.action = None
        return

    anim = ob.animation_data_create()
    anim.action = action
    slot = None
    if hasattr(action, "slots") and len(action.slots) == 0:
        slot = action.slots.new(id_type="OBJECT", name=ob.name)
    elif hasattr(anim, "action_suitable_slots") and anim.action_suitable_slots:
        slot = anim.action_suitable_slots[0]
    if slot is not None and hasattr(anim, "action_slot"):
        anim.action_slot = slot
        anim_utils.action_ensure_channelbag_for_slot(action, slot)


def _store_current_pose(
    ob: bpy.types.Object,
    action_name: str,
    *,
    key_location: bool,
    key_rotation: bool,
    key_scale: bool,
    frame: int,
) -> bpy.types.Action:
    action = _replace_action(action_name)
    _assign_action(ob, action)
    for bone in ob.pose.bones:
        if key_location:
            bone.keyframe_insert(data_path="location", frame=frame, group=bone.name)
        if key_rotation:
            bone.keyframe_insert(
                data_path="rotation_euler", frame=frame, group=bone.name
            )
            bone.keyframe_insert(
                data_path="rotation_quaternion", frame=frame, group=bone.name
            )
        if key_scale:
            bone.keyframe_insert(data_path="scale", frame=frame, group=bone.name)
    if hasattr(action, "asset_mark"):
        action.asset_mark()
    _assign_action(ob, None)
    return action


def _apply_named_pose(ob: bpy.types.Object, action_name: str) -> bool:
    action = bpy.data.actions.get(action_name)
    if action is None:
        return False
    ob.pose.apply_pose_from_action(action)
    return True


def _restore_pose_selection(pose, bone_names: list[str]) -> None:
    bpy.ops.pose.select_all(action="DESELECT")
    for name in bone_names:
        pose_bone = pose.bones.get(name)
        if pose_bone is not None:
            pose_bone.select = True


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

        pre_selected_names = [bone.name for bone in (context.selected_pose_bones or [])]
        pre_mode = target_ob.mode

        bpy.ops.object.mode_set(mode="POSE")
        bpy.ops.pose.select_all(action="SELECT")
        bpy.ops.pose.constraints_clear()

        consts = []
        bones = (
            [pose.bones[name] for name in pre_selected_names if name in pose.bones]
            if self.is_only_selected
            else pose.bones
        )
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

        for i in range(2):
            is_prime_frame = not bool(i % 2) if arm.get("is T Stance") else bool(i % 2)
            pose_name = (
                PRIME_FIELD_POSE_NAME if is_prime_frame else BASE_FIELD_POSE_NAME
            )
            if self.is_apply_prime:
                is_prime_frame = not is_prime_frame

            for const in consts:
                const.mute = not is_prime_frame
            if is_prime_frame:
                bpy.ops.pose.visual_transform_apply()
            else:
                bpy.ops.pose.transforms_clear()

            _store_current_pose(
                target_ob,
                pose_name,
                key_location=self.is_key_location,
                key_rotation=self.is_key_rotation,
                key_scale=self.is_key_scale,
                frame=i,
            )

        bpy.ops.pose.constraints_clear()
        bpy.ops.pose.transforms_clear()
        target_ob.animation_data_clear()

        _restore_pose_selection(pose, pre_selected_names)

        if pre_mode:
            bpy.ops.object.mode_set(mode=pre_mode)

        return {"FINISHED"}


@compat.BlRegister()
class CNV_OT_apply_prime_field(bpy.types.Operator):
    bl_idname = "pose.apply_prime_field"
    bl_label = "現在のポーズで素体化"
    bl_description = "現在のポーズで衣装をモデリングしやすくする素体を作成します"
    bl_options = {"REGISTER", "UNDO"}

    is_apply_armature_modifier = bpy.props.BoolProperty(
        name="関係するメッシュのアーマチュアを適用", default=True
    )
    is_preserve_shape_key_values = bpy.props.BoolProperty(
        name="Preserve Shape Key Values",
        default=True,
        description="Ensure shape key values of child mesh objects are not changed",
    )
    is_deform_preserve_volume = bpy.props.BoolProperty(
        name="アーマチュア適用は体積を維持", default=True
    )
    is_keep_original = bpy.props.BoolProperty(
        name="Keep Original",
        default=True,
        description="If the armature is already primed, don't replace the base pose with the current rest pose",
    )
    is_swap_prime_field = bpy.props.BoolProperty(
        name="Swap Prime Field", default=False, options={"HIDDEN"}
    )

    was_t_stance = False

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return bool(ob and ob.type == "ARMATURE")

    def invoke(self, context, event):
        self.was_t_stance = bool(context.object.data.get("is T Stance"))
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "is_apply_armature_modifier")

        col = self.layout.column()
        col.enabled = self.is_apply_armature_modifier
        col.prop(self, "is_preserve_shape_key_values")
        col.prop(self, "is_deform_preserve_volume")
        if self.was_t_stance:
            self.layout.prop(self, "is_keep_original")

    def execute(self, context):
        ob = context.active_object
        arm = ob.data
        pose = ob.pose
        progress = 0

        pre_selected_objects = list(context.selected_objects)
        pre_selected_names = [bone.name for bone in (context.selected_pose_bones or [])]
        pre_mode = ob.mode
        pre_frame = context.scene.frame_current

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        compat.set_select(ob, True)

        if self.is_swap_prime_field:
            bpy.ops.object.mode_set(mode="POSE")
            bpy.ops.pose.select_all(action="SELECT")
            _apply_named_pose(ob, _pose_action_name_at_index(arm, 1))
            context.view_layer.update()
            bpy.ops.object.mode_set(mode="OBJECT")

        if self.is_apply_armature_modifier and ob.children:
            context.window_manager.progress_begin(0, len(ob.children) + 1)
            for child in ob.children:
                if child.type != "MESH" or not child.modifiers:
                    progress += 1
                    context.window_manager.progress_update(progress)
                    continue

                armature_settings = []
                for mod in child.modifiers:
                    if mod.type != "ARMATURE":
                        continue
                    mod.use_deform_preserve_volume = self.is_deform_preserve_volume
                    if mod.object == ob:
                        armature_settings.append(
                            {
                                "name": mod.name,
                                "show_expanded": mod.show_expanded,
                                "show_in_editmode": mod.show_in_editmode,
                                "show_on_cage": mod.show_on_cage,
                                "show_render": mod.show_render,
                                "show_viewport": mod.show_viewport,
                                "use_apply_on_spline": mod.use_apply_on_spline,
                                "invert_vertex_group": mod.invert_vertex_group,
                                "use_bone_envelopes": mod.use_bone_envelopes,
                                "use_vertex_groups": mod.use_vertex_groups,
                                "vertex_group": mod.vertex_group,
                            }
                        )

                with compat.temp_override(
                    context,
                    object=child,
                    active_object=child,
                    selected_objects=[child],
                ):
                    if not bpy.ops.object.forced_modifier_apply.poll():
                        progress += 1
                        context.window_manager.progress_update(progress)
                        continue
                    apply_results = bpy.ops.object.forced_modifier_apply(
                        apply_viewport_visible=True,
                        is_preserve_shape_key_values=self.is_preserve_shape_key_values,
                        initial_progress=progress,
                    )

                if "FINISHED" in apply_results:
                    for settings in armature_settings:
                        new_mod = child.modifiers.new(
                            name=settings["name"], type="ARMATURE"
                        )
                        new_mod.object = ob
                        new_mod.use_deform_preserve_volume = (
                            self.is_deform_preserve_volume
                        )
                        new_mod.show_expanded = settings["show_expanded"]
                        new_mod.show_in_editmode = settings["show_in_editmode"]
                        new_mod.show_on_cage = settings["show_on_cage"]
                        new_mod.show_render = settings["show_render"]
                        new_mod.show_viewport = settings["show_viewport"]
                        new_mod.use_apply_on_spline = settings["use_apply_on_spline"]
                        new_mod.invert_vertex_group = settings["invert_vertex_group"]
                        new_mod.use_bone_envelopes = settings["use_bone_envelopes"]
                        new_mod.use_vertex_groups = settings["use_vertex_groups"]
                        new_mod.vertex_group = settings["vertex_group"]

                progress += 1
                context.window_manager.progress_update(progress)
        else:
            context.window_manager.progress_begin(0, 1)

        temp_ob = ob.copy()
        temp_arm = arm.copy()
        temp_ob.data = temp_arm
        compat.link(context.scene, temp_ob)

        compat.set_active(context, ob)
        bpy.ops.object.mode_set(mode="POSE")
        bpy.ops.pose.select_all(action="SELECT")
        for bone in ob.pose.bones:
            prime_scale = mathutils.Vector(bone.get("prime_scale", (1.0, 1.0, 1.0)))
            bone_scale = bone.scale
            prime_scale.x *= bone_scale.x
            prime_scale.y *= bone_scale.y
            prime_scale.z *= bone_scale.z
            bone["prime_scale"] = prime_scale
        bpy.ops.pose.armature_apply()
        bpy.ops.pose.constraints_clear()
        ob.animation_data_clear()

        if arm.get("is T Stance") and self.is_keep_original and not self.is_swap_prime_field:
            anim_data = temp_ob.animation_data
            if anim_data and anim_data.drivers:
                drivers = anim_data.drivers
                for driver in list(drivers):
                    drivers.remove(driver)
            bpy.ops.pose.user_transforms_clear()

            compat.set_active(context, temp_ob)
            bpy.ops.object.mode_set(mode="POSE")
            bpy.ops.pose.select_all(action="SELECT")
            _apply_named_pose(temp_ob, _pose_action_name_at_index(arm, 1))
            bpy.ops.pose.armature_apply()
            compat.set_active(context, ob)
        else:
            compat.set_active(context, temp_ob)
            bpy.ops.object.mode_set(mode="POSE")
            bpy.ops.pose.select_all(action="SELECT")
            temp_ob.animation_data_clear()
            bpy.ops.pose.transforms_clear()
            bpy.ops.object.mode_set(mode="OBJECT")
            compat.set_select(temp_ob, False)

        if self.is_swap_prime_field and arm.get("is T Stance"):
            arm["is T Stance"] = False
        else:
            arm["is T Stance"] = True

        compat.set_select(temp_ob, True)
        compat.set_active(context, ob)
        context.view_layer.update()
        response = bpy.ops.pose.copy_prime_field(
            is_only_selected=False,
            is_key_location=True,
            is_key_scale=True,
            is_apply_prime=(not self.is_swap_prime_field),
        )

        context.window_manager.progress_end()

        if "FINISHED" not in response:
            return response

        common.remove_data(temp_arm)
        try:
            common.remove_data(temp_ob)
        except Exception:
            pass

        bpy.ops.object.mode_set(mode="POSE")
        _restore_pose_selection(pose, pre_selected_names)

        if pre_selected_objects:
            for selected in pre_selected_objects:
                compat.set_select(selected, True)
        compat.set_active(context, ob)
        bpy.ops.object.mode_set(mode=pre_mode)

        context.scene.frame_set(pre_frame)

        return {"FINISHED"}
