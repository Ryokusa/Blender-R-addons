# 「プロパティ」エリア → 「メッシュデータ」タブ → 「シェイプキー」パネル → ▼ボタン
import time
import bpy
import bmesh
import mathutils
from . import common
from . import compat


# メニュー等に項目追加
def menu_func(self, context):
    icon_id = common.kiss_icon()
    self.layout.separator()
    self.layout.operator('object.quick_shape_key_transfer', icon_value=icon_id)
    self.layout.operator('object.precision_shape_key_transfer', icon_value=icon_id)
    self.layout.separator()
    self.layout.operator('object.multiply_shape_key', icon_value=icon_id)
    self.layout.separator()
    self.layout.operator('object.blur_shape_key', icon_value=icon_id)
    self.layout.separator()
    self.layout.operator('object.change_base_shape_key', icon_value=icon_id)


@compat.BlRegister()
class CNV_OT_quick_shape_key_transfer(bpy.types.Operator):
    bl_idname = 'object.quick_shape_key_transfer'
    bl_label = "Quick shape key transfer"
    bl_description = "Fast transfer of other selected mesh's shape keys to active mesh"
    bl_options = {'REGISTER', 'UNDO'}

    is_first_remove_all = bpy.props.BoolProperty(name="First delete all shape keys", default=True)
    subdivide_number = bpy.props.IntProperty(name="Split referrer", default=1, min=0, max=10, soft_min=0, soft_max=10)
    is_remove_empty = bpy.props.BoolProperty(name="Remove shape key without deformation", default=True)

    @classmethod
    def poll(cls, context):
        obs = context.selected_objects
        if len(obs) == 2:
            active_ob = context.active_object
            for ob in obs:
                if ob.type != 'MESH':
                    return False
                if ob.data.shape_keys and ob.name != active_ob.name:
                    return True
        return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'is_first_remove_all', icon='ERROR')
        self.layout.prop(self, 'subdivide_number', icon='LATTICE_DATA')
        self.layout.prop(self, 'is_remove_empty', icon='X')

    def execute(self, context):
        start_time = time.time()

        target_ob = context.active_object
        target_me = target_ob.data

        pre_mode = target_ob.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        for ob in context.selected_objects:
            if ob.name != target_ob.name:
                source_original_ob = ob
                break
        source_ob = source_original_ob.copy()
        source_me = source_original_ob.data.copy()
        source_ob.data = source_me
        try:
            compat.link(context.scene, source_ob)
            compat.set_active(context, source_ob)
            compat.set_select(source_original_ob, False)
            compat.set_select(target_ob, False)

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.reveal()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.subdivide(number_cuts=self.subdivide_number, smoothness=0.0, quadcorner='STRAIGHT_CUT', fractal=0.0, fractal_along_normal=0.0, seed=0)
            source_ob.active_shape_key_index = 0
            bpy.ops.object.mode_set(mode='OBJECT')

            if self.is_first_remove_all:
                try:
                    target_ob.active_shape_key_index = 1
                    bpy.ops.object.shape_key_remove(all=True)
                except:
                    pass

            kd = mathutils.kdtree.KDTree(len(source_me.vertices))
            for vert in source_me.vertices:
                co = compat.mul(source_ob.matrix_world, vert.co)
                kd.insert(co, vert.index)
            kd.balance()

            near_vert_indexs = [kd.find(compat.mul(target_ob.matrix_world, v.co))[1] for v in target_me.vertices]

            is_shapeds = {}
            relative_keys = set()
            context.window_manager.progress_begin(0, len(source_me.shape_keys.key_blocks))
            context.window_manager.progress_update(0)
            for source_shape_key_index, source_shape_key in enumerate(source_me.shape_keys.key_blocks):

                if target_me.shape_keys:
                    target_shape_key = target_me.shape_keys.key_blocks.get(source_shape_key.name)
                    if target_shape_key is None:
                        target_shape_key = target_ob.shape_key_add(name=source_shape_key.name, from_mix=False)
                else:
                    target_shape_key = target_ob.shape_key_add(name=source_shape_key.name, from_mix=False)

                relative_key_name = source_shape_key.relative_key.name
                relative_keys.add(relative_key_name)
                is_shapeds[source_shape_key.name] = False

                rel_key = target_me.shape_keys.key_blocks.get(relative_key_name)
                if rel_key:
                    target_shape_key.relative_key = rel_key

                mat1, mat2 = source_ob.matrix_world, target_ob.matrix_world
                source_shape_keys = [compat.mul3(mat1, source_shape_key.data[v.index].co, mat2) - compat.mul3(mat1, source_me.vertices[v.index].co, mat2) for v in source_me.vertices]

                for target_vert in target_me.vertices:

                    near_vert_index = near_vert_indexs[target_vert.index]
                    near_shape_co = source_shape_keys[near_vert_index]

                    target_shape_key.data[target_vert.index].co = target_me.vertices[target_vert.index].co + near_shape_co
                    if 0.01 < near_shape_co.length:
                        is_shapeds[source_shape_key.name] = True

                context.window_manager.progress_update(source_shape_key_index)
            context.window_manager.progress_end()

            if self.is_remove_empty:
                for source_shape_key_name, is_shaped in is_shapeds.items():
                    if source_shape_key_name not in relative_keys and not is_shaped:
                        target_shape_key = target_me.shape_keys.key_blocks[source_shape_key_name]
                        target_ob.shape_key_remove(target_shape_key)

            target_ob.active_shape_key_index = 0

        finally:
            common.remove_data([source_ob, source_me])

            compat.set_select(source_original_ob, True)
            compat.set_select(target_ob, True)
            compat.set_active(context, target_ob)
            bpy.ops.object.mode_set(mode=pre_mode)

        diff_time = time.time() - start_time
        self.report(type={'INFO'}, message="%.2f Seconds" % diff_time)
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_precision_shape_key_transfer(bpy.types.Operator):
    bl_idname = 'object.precision_shape_key_transfer'
    bl_label = "Space blur/shape key transfer"
    bl_description = "Transfers the shape keys of other selected meshes to the active mesh, blurring them further"
    bl_options = {'REGISTER', 'UNDO'}

    is_first_remove_all = bpy.props.BoolProperty(name="First delete all shape keys", default=True)
    subdivide_number = bpy.props.IntProperty(name="Split referrer", default=1, min=0, max=10, soft_min=0, soft_max=10)
    extend_range = bpy.props.FloatProperty(name="Range magnification", default=1.1, min=1.0001, max=5.0, soft_min=1.0001, soft_max=5.0, step=10, precision=2)
    is_remove_empty = bpy.props.BoolProperty(name="Remove shape key without deformation", default=True)

    @classmethod
    def poll(cls, context):
        obs = context.selected_objects
        if len(obs) == 2:
            active_ob = context.active_object
            for ob in obs:
                if ob.type != 'MESH':
                    return False
                if ob.data.shape_keys and ob.name != active_ob.name:
                    return True
        return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'is_first_remove_all', icon='ERROR')
        self.layout.prop(self, 'subdivide_number', icon='LATTICE_DATA')
        self.layout.prop(self, 'extend_range', icon='PROP_ON')
        self.layout.prop(self, 'is_remove_empty', icon='X')

    def execute(self, context):
        start_time = time.time()

        target_ob = context.active_object
        target_me = target_ob.data

        pre_mode = target_ob.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        for ob in context.selected_objects:
            if ob.name != target_ob.name:
                source_original_ob = ob
                break
        source_ob = source_original_ob.copy()
        source_me = source_original_ob.data.copy()
        source_ob.data = source_me

        try:
            compat.link(context.scene, source_ob)
            compat.set_active(context, source_ob)
            compat.set_select(source_original_ob, False)
            compat.set_select(target_ob, False)

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.reveal()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.subdivide(number_cuts=self.subdivide_number, smoothness=0.0, quadcorner='STRAIGHT_CUT', fractal=0.0, fractal_along_normal=0.0, seed=0)
            source_ob.active_shape_key_index = 0
            bpy.ops.object.mode_set(mode='OBJECT')

            if self.is_first_remove_all:
                try:
                    target_ob.active_shape_key_index = 1
                    bpy.ops.object.shape_key_remove(all=True)
                except:
                    pass

            kd = mathutils.kdtree.KDTree(len(source_me.vertices))
            for vert in source_me.vertices:
                co = compat.mul(source_ob.matrix_world, vert.co)
                kd.insert(co, vert.index)
            kd.balance()

            context.window_manager.progress_begin(0, len(target_me.vertices))
            progress_reduce = len(target_me.vertices) // 200 + 1
            near_vert_data = []
            near_vert_multi_total = []
            near_vert_multi_total_append = near_vert_multi_total.append
            for vert in target_me.vertices:
                new_vert_data = []
                near_vert_data.append(new_vert_data)
                near_vert_data_append = new_vert_data.append

                target_co = compat.mul(target_ob.matrix_world, vert.co)
                mini_co, mini_index, mini_dist = kd.find(target_co)
                radius = mini_dist * self.extend_range
                diff_radius = radius - mini_dist

                multi_total = 0.0
                for co, index, dist in kd.find_range(target_co, radius):
                    if 0 < diff_radius:
                        multi = (diff_radius - (dist - mini_dist)) / diff_radius
                    else:
                        multi = 1.0
                    near_vert_data_append((index, multi))
                    multi_total += multi
                near_vert_multi_total_append(multi_total)

                if vert.index % progress_reduce == 0:
                    context.window_manager.progress_update(vert.index)
            context.window_manager.progress_end()

            is_shapeds = {}
            relative_keys = set()
            context.window_manager.progress_begin(0, len(source_me.shape_keys.key_blocks))
            context.window_manager.progress_update(0)
            for source_shape_key_index, source_shape_key in enumerate(source_me.shape_keys.key_blocks):

                if target_me.shape_keys:
                    if source_shape_key.name in target_me.shape_keys.key_blocks:
                        target_shape_key = target_me.shape_keys.key_blocks[source_shape_key.name]
                    else:
                        target_shape_key = target_ob.shape_key_add(name=source_shape_key.name, from_mix=False)
                else:
                    target_shape_key = target_ob.shape_key_add(name=source_shape_key.name, from_mix=False)

                relative_key_name = source_shape_key.relative_key.name
                relative_keys.add(relative_key_name)
                is_shapeds[source_shape_key.name] = False

                rel_key = target_me.shape_keys.key_blocks.get(relative_key_name)
                if rel_key:
                    target_shape_key.relative_key = rel_key

                mat1, mat2 = source_ob.matrix_world, target_ob.matrix_world
                source_shape_keys = [compat.mul3(mat1, source_shape_key.data[v.index].co, mat2) - compat.mul3(mat1, source_me.vertices[v.index].co, mat2) for v in source_me.vertices]

                for target_vert in target_me.vertices:

                    if 0 < near_vert_multi_total[target_vert.index]:

                        total_diff_co = mathutils.Vector((0, 0, 0))

                        for near_index, near_multi in near_vert_data[target_vert.index]:
                            total_diff_co += source_shape_keys[near_index] * near_multi

                        average_diff_co = total_diff_co / near_vert_multi_total[target_vert.index]

                    else:
                        average_diff_co = mathutils.Vector((0, 0, 0))

                    target_shape_key.data[target_vert.index].co = target_me.vertices[target_vert.index].co + average_diff_co
                    if 0.01 < average_diff_co.length:
                        is_shapeds[source_shape_key.name] = True

                context.window_manager.progress_update(source_shape_key_index)
            context.window_manager.progress_end()

            if self.is_remove_empty:
                for source_shape_key_name, is_shaped in is_shapeds.items():
                    if source_shape_key_name not in relative_keys and not is_shaped:
                        target_shape_key = target_me.shape_keys.key_blocks[source_shape_key_name]
                        target_ob.shape_key_remove(target_shape_key)

            target_ob.active_shape_key_index = 0

        finally:
            common.remove_data([source_ob, source_me])

            compat.set_select(source_original_ob, True)
            compat.set_select(target_ob, True)
            compat.set_active(context, target_ob)
            bpy.ops.object.mode_set(mode=pre_mode)

        diff_time = time.time() - start_time
        self.report(type={'INFO'}, message="%.2f Seconds" % diff_time)
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_multiply_shape_key(bpy.types.Operator):
    bl_idname = 'object.multiply_shape_key'
    bl_label = "Multiply shape key variants"
    bl_description = "Multiply the shape key deformation by a number to increase or decrease the strength of the deformation"
    bl_options = {'REGISTER', 'UNDO'}

    multi = bpy.props.FloatProperty(name="Magnification", description="Shape key expansion rate", default=1.1, min=-10, max=10, soft_min=-10, soft_max=10, step=10, precision=2)
    items = [
        ('ACTIVE', "Active only", "", 'HAND', 1),
        ('UP', "Above active", "", 'TRIA_UP_BAR', 2),
        ('DOWN', "Below active", "", 'TRIA_DOWN_BAR', 3),
        ('ALL', "All", "", 'ARROW_LEFTRIGHT', 4),
    ]
    mode = bpy.props.EnumProperty(items=items, name="対象", default='ACTIVE')

    @classmethod
    def poll(cls, context):
        if context.active_object:
            ob = context.active_object
            if ob.type == 'MESH':
                return ob.active_shape_key
        return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'multi', icon='ARROW_LEFTRIGHT')
        self.layout.prop(self, 'mode', icon='VIEWZOOM')

    def execute(self, context):
        ob = context.active_object
        me = ob.data
        shape_keys = me.shape_keys
        pre_mode = ob.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        target_shapes = []
        if self.mode == 'ACTIVE':
            target_shapes.append(ob.active_shape_key)
        elif self.mode == 'UP':
            for index, key_block in enumerate(shape_keys.key_blocks):
                if index <= ob.active_shape_key_index:
                    target_shapes.append(key_block)
        elif self.mode == 'UP':
            for index, key_block in enumerate(shape_keys.key_blocks):
                if ob.active_shape_key_index <= index:
                    target_shapes.append(key_block)
        elif self.mode == 'ALL':
            for key_block in shape_keys.key_blocks:
                target_shapes.append(key_block)

        for shape in target_shapes:
            data = shape.data
            for i, vert in enumerate(me.vertices):
                diff = data[i].co - vert.co
                diff *= self.multi
                data[i].co = vert.co + diff
        bpy.ops.object.mode_set(mode=pre_mode)
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_blur_shape_key(bpy.types.Operator):
    bl_idname = 'object.blur_shape_key'
    bl_label = "Shape key blur"
    bl_description = "Blur active or all shape keys"
    bl_options = {'REGISTER', 'UNDO'}

    items = [
        ('ACTIVE', "Active only", "", 'HAND', 1),
        ('UP', "Above active", "", 'TRIA_UP_BAR', 2),
        ('DOWN', "Below active", "", 'TRIA_DOWN_BAR', 3),
        ('ALL', "All", "", 'ARROW_LEFTRIGHT', 4),
    ]
    target = bpy.props.EnumProperty(items=items, name="Target", default='ACTIVE')
    radius = bpy.props.FloatProperty(name="Range magnification", default=3, min=0.1, max=50, soft_min=0.1, soft_max=50, step=50, precision=2)
    strength = bpy.props.IntProperty(name="Strength", default=1, min=1, max=10, soft_min=1, soft_max=10)
    items = [
        ('BOTH', "Both increase and decrease", "", 'AUTOMERGE_ON', 1),
        ('ADD', "Increase only", "", 'TRIA_UP', 2),
        ('SUB', "Decrease only", "", 'TRIA_DOWN', 3),
    ]
    effect = bpy.props.EnumProperty(items=items, name="Blur effect", default='BOTH')
    items = [
        ('LINER', "Linear", "", 'LINCURVE', 1),
        ('SMOOTH1', "Smooth 1", "", 'SMOOTHCURVE', 2),
        ('SMOOTH2', "Smooth 2", "", 'SMOOTHCURVE', 3),
    ]
    blend = bpy.props.EnumProperty(items=items, name="Attenuation type", default='LINER')

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob and ob.type == 'MESH':
            me = ob.data
            return me.shape_keys
        return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'target', icon='VIEWZOOM')
        self.layout.prop(self, 'radius', icon='RADIOBUT_OFF')
        self.layout.prop(self, 'strength', icon='ARROW_LEFTRIGHT')
        self.layout.prop(self, 'effect', icon='BRUSH_BLUR')
        self.layout.prop(self, 'blend', icon='IPO_SINE')

    def execute(self, context):
        ob = context.active_object
        me = ob.data

        pre_mode = ob.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        bm = bmesh.new()
        bm.from_mesh(me)
        edge_lengths = [e.calc_length() for e in bm.edges]
        bm.free()

        edge_lengths.sort()
        average_edge_length = sum(edge_lengths) / len(edge_lengths)
        center_index = int((len(edge_lengths) - 1) / 2.0)
        average_edge_length = (average_edge_length + edge_lengths[center_index]) / 2
        radius = average_edge_length * self.radius

        context.window_manager.progress_begin(0, len(me.vertices))
        progress_reduce = len(me.vertices) // 200 + 1
        near_vert_data = []
        kd = mathutils.kdtree.KDTree(len(me.vertices))
        for vert in me.vertices:
            kd.insert(vert.co.copy(), vert.index)
        kd.balance()
        for vert in me.vertices:
            near_vert_data.append([])
            near_vert_data_append = near_vert_data[-1].append
            for co, index, dist in kd.find_range(vert.co, radius):
                multi = (radius - dist) / radius
                if self.blend == 'SMOOTH1':
                    multi = common.in_out_quad_blend(multi)
                elif self.blend == 'SMOOTH2':
                    multi = common.bezier_blend(multi)
                near_vert_data_append((index, multi))
            if vert.index % progress_reduce == 0:
                context.window_manager.progress_update(vert.index)
        context.window_manager.progress_end()

        target_shape_keys = []
        if self.target == 'ACTIVE':
            target_shape_keys.append(ob.active_shape_key)
        elif self.target == 'UP':
            for index, shape_key in enumerate(me.shape_keys.key_blocks):
                if index <= ob.active_shape_key_index:
                    target_shape_keys.append(shape_key)
        elif self.target == 'DOWN':
            for index, shape_key in enumerate(me.shape_keys.key_blocks):
                if ob.active_shape_key_index <= index:
                    target_shape_keys.append(shape_key)
        elif self.target == 'ALL':
            for index, shape_key in enumerate(me.shape_keys.key_blocks):
                target_shape_keys.append(shape_key)

        progress_total = len(target_shape_keys) * self.strength * len(me.vertices)
        context.window_manager.progress_begin(0, progress_total)
        progress_reduce = progress_total // 200 + 1
        progress_count = 0
        for strength_count in range(self.strength):
            for shape_key in target_shape_keys:

                shapes = []
                shapes_append = shapes.append
                for index, vert in enumerate(me.vertices):
                    co = shape_key.data[index].co - vert.co
                    shapes_append(co)

                for vert in me.vertices:

                    target_shape = shapes[vert.index]

                    total_shape = mathutils.Vector()
                    total_multi = 0.0
                    for index, multi in near_vert_data[vert.index]:
                        co = shapes[index]
                        if self.effect == 'ADD':
                            if target_shape.length <= co.length:
                                total_shape += co * multi
                                total_multi += multi
                        elif self.effect == 'SUB':
                            if co.length <= target_shape.length:
                                total_shape += co * multi
                                total_multi += multi
                        else:
                            total_shape += co * multi
                            total_multi += multi

                    if 0 < total_multi:
                        average_shape = total_shape / total_multi
                    else:
                        average_shape = mathutils.Vector()

                    shape_key.data[vert.index].co = vert.co + average_shape

                    progress_count += 1
                    if progress_count % progress_reduce == 0:
                        context.window_manager.progress_update(progress_count)

        context.window_manager.progress_end()
        bpy.ops.object.mode_set(mode=pre_mode)
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_change_base_shape_key(bpy.types.Operator):
    bl_idname = 'object.change_base_shape_key'
    bl_label = "Based on this shape key"
    bl_description = "Base active shape key on other shape keys"
    bl_options = {'REGISTER', 'UNDO'}

    is_deform_mesh = bpy.props.BoolProperty(name="Adjust the raw mesh", default=True)
    is_deform_other_shape = bpy.props.BoolProperty(name="Adjust other shapes", default=True)

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'MESH' and 1 <= ob.active_shape_key_index

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'is_deform_mesh', icon='MESH_DATA')
        self.layout.prop(self, 'is_deform_other_shape', icon='SHAPEKEY_DATA')

    def execute(self, context):
        ob = context.active_object
        me = ob.data

        pre_mode = ob.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        target_shape_key = ob.active_shape_key
        old_shape_key = me.shape_keys.key_blocks[0]

        # TOP指定でindex=1になるケースは、さらにもう一度UP
        bpy.ops.object.shape_key_move(type='TOP')
        if ob.active_shape_key_index == 1:
            bpy.ops.object.shape_key_move(type='UP')

        target_shape_key.relative_key = target_shape_key
        old_shape_key.relative_key = target_shape_key

        if self.is_deform_mesh:
            for vert in me.vertices:
                vert.co = target_shape_key.data[vert.index].co.copy()

        if self.is_deform_other_shape:
            for shape_key in me.shape_keys.key_blocks:
                if shape_key.name == target_shape_key.name or shape_key.name == old_shape_key.name:
                    continue
                if shape_key.relative_key.name == old_shape_key.name:
                    shape_key.relative_key = target_shape_key
                    for vert in me.vertices:
                        diff_co = target_shape_key.data[vert.index].co - old_shape_key.data[vert.index].co
                        shape_key.data[vert.index].co = shape_key.data[vert.index].co + diff_co

        bpy.ops.object.mode_set(mode=pre_mode)
        return {'FINISHED'}
