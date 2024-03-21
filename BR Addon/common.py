import os
import re
import math
import struct
import shutil
from typing import Any
import bpy
import bmesh
import mathutils
from . import fileutil
from . import compat

# アドオン情報
bl_info = {}
ADDON_NAME = "BR Addon"
BASE_PATH_TEX = "Assets/texture/texture/"
BRANCH = "bl_28"
URL_REPOS = "https://github.com/Ryokusa/Blender-R-addons"
URL_ATOM = URL_REPOS + "commits/{branch}.atom"
URL_MODULE = URL_REPOS + "archive/{branch}.zip"
KISS_ICON = None
PREFS = None
preview_collections = {}
texpath_dict = {}


re_png = re.compile(r"\.[Pp][Nn][Gg](\.\d{3})?$")
re_serial = re.compile(r"(\.\d{3})$")
re_prefix = re.compile(r"^[\/\.]*")
re_path_prefix = re.compile(r"^assets/", re.I)
re_ext_png = re.compile(r"\.png$", re.I)
re_bone1 = re.compile(r"([_ ])\*([_ ].*)\.([rRlL])$")
re_bone2 = re.compile(r"([_ ])([rRlL])([_ ].*)$")


# このアドオンの設定値群を呼び出す
def preferences():
    global PREFS
    if PREFS is None:
        try:
            PREFS = compat.get_prefs(bpy.context).addons[__package__].preferences
        except KeyError:
            # This can happen when using Blender-as-a-Module
            # which is how the unit-tests work
            from . import AddonPreferences

            _props = {}
            for k, v in AddonPreferences.__dict__.items():
                if str(type(v)) == "<class '_PropertyDeferred'>":
                    kw: dict = v.keywords
                    default = kw["default"] if "default" in kw.keys() else None
                    _props[k] = default

            class FakeAddonPreferences:
                def __getattribute__(self, name: str) -> Any:
                    return _props[name]

                def __setattr__(self, name: str, value: Any) -> None:
                    if name not in _props.keys():
                        raise AttributeError(self, name)
                    _props[name] = value

            PREFS = FakeAddonPreferences()
    return PREFS


def kiss_icon():
    global KISS_ICON
    if KISS_ICON is None:
        KISS_ICON = preview_collections["main"]["KISS"].icon_id
    return KISS_ICON


# データ名末尾の「.001」などを削除
def remove_serial_number(name, enable=True):
    return re_serial.sub("", name) if enable else name


# データ名末尾の「.001」などが含まれるか判定
def has_serial_number(name):
    return re_serial.search(name) is not None


# 文字列の左右端から空白を削除
def line_trim(line, enable=True):
    return line.strip(" 　\t\r\n") if enable else line


# 画像のおおよその平均色を取得
def get_image_average_color(img, sample_count=10):
    if not len(img.pixels):
        return mathutils.Color([0, 0, 0])

    pixel_count = img.size[0] * img.size[1]
    channels = img.channels

    max_s = 0.0
    max_s_color, average_color = mathutils.Color([0, 0, 0]), mathutils.Color([0, 0, 0])
    seek_interval = pixel_count / sample_count
    for sample_index in range(sample_count):
        index = int(seek_interval * sample_index) * channels
        color = mathutils.Color(img.pixels[index : index + 3])
        average_color += color
        if max_s < color.s:
            max_s_color, max_s = color, color.s

    average_color /= sample_count
    output_color = (average_color + max_s_color) / 2
    output_color.s *= 1.5
    return max_s_color


# 画像のおおよその平均色を取得 (UV版)
def get_image_average_color_uv(img, me=None, mate_index=-1, sample_count=10):
    if not len(img.pixels):
        return mathutils.Color([0, 0, 0])

    img_width, img_height, img_channel = img.size[0], img.size[1], img.channels

    bm = bmesh.new()
    bm.from_mesh(me)
    uv_lay = bm.loops.layers.uv.active
    uvs = [
        l[uv_lay].uv[:]
        for f in bm.faces
        if f.material_index == mate_index
        for l in f.loops
    ]
    bm.free()

    if len(uvs) <= sample_count:
        return get_image_average_color(img)

    average_color = mathutils.Color([0, 0, 0])
    max_s = 0.0
    max_s_color = mathutils.Color([0, 0, 0])
    seek_interval = len(uvs) / sample_count
    for sample_index in range(sample_count):
        uv_index = int(seek_interval * sample_index)
        x, y = uvs[uv_index]

        x = math.modf(x)[0]
        if x < 0.0:
            x += 1.0
        y = math.modf(y)[0]
        if y < 0.0:
            y += 1.0

        x, y = int(x * img_width), int(y * img_height)

        pixel_index = ((y * img_width) + x) * img_channel
        color = mathutils.Color(img.pixels[pixel_index : pixel_index + 3])

        average_color += color
        if max_s < color.s:
            max_s_color, max_s = color, color.s

    average_color /= sample_count
    output_color = (average_color + max_s_color) / 2
    output_color.s *= 1.5
    return output_color


# 一時ファイル書き込みと自動バックアップを行うファイルオブジェクトを返す
def open_temporary(filepath, mode, is_backup=False):
    backup_ext = preferences().backup_ext
    if is_backup and backup_ext:
        backup_filepath = filepath + "." + backup_ext
    else:
        backup_filepath = None
    return fileutil.TemporaryFileWriter(filepath, mode, backup_filepath=backup_filepath)


# ファイルを上書きするならバックアップ処理
def file_backup(filepath, enable=True):
    backup_ext = preferences().backup_ext
    if enable and backup_ext and os.path.exists(filepath):
        shutil.copyfile(filepath, filepath + "." + backup_ext)


def reload_png(img, texpath_dict, png_name):
    png_path = texpath_dict.get(png_name)
    if png_path:
        img.filepath = png_path
        img.reload()
        return True
    return False


def create_col(context, mate, node_name, color, slot_index=-1):
    if isinstance(context, bpy.types.Context):
        context = context.copy()

    if compat.IS_LEGACY:
        if slot_index >= 0:
            mate.use_textures[slot_index] = False
        node = mate.texture_slots.create(slot_index)
        node.color = color[:3]
        node.diffuse_color_factor = color[3]
        node.use_rgb_to_intensity = True
        tex = context["blend_data"].textures.new(node_name, "BLEND")
        node.texture = tex
        node.use = False
    else:
        node = mate.node_tree.nodes.get(node_name)
        if node is None:
            node = mate.node_tree.nodes.new(type="ShaderNodeRGB")
            node.name = node.label = node_name
        node.outputs[0].default_value = color

    return node


def create_float(context, mate, node_name, value, slot_index=-1):
    if isinstance(context, bpy.types.Context):
        context = context.copy()

    if compat.IS_LEGACY:
        if slot_index >= 0:
            mate.use_textures[slot_index] = False
        node = mate.texture_slots.create(slot_index)
        node.diffuse_color_factor = value
        node.use_rgb_to_intensity = False
        tex = context["blend_data"].textures.new(node_name, "BLEND")
        node.texture = tex
        node.use = False
    else:
        node = mate.node_tree.nodes.get(node_name)
        if node is None:
            node = mate.node_tree.nodes.new(type="ShaderNodeValue")
            node.name = node.label = node_name
        node.outputs[0].default_value = value

    return node


def setup_image_name(img):
    """イメージの名前から拡張子を除外する"""
    # consider case with serial number. ex) sample.png.001
    img.name = re_png.sub(r"\1", img.name)


# col f タイプの設定値を値に合わせて着色
def set_texture_color(slot):
    if not slot or not slot.texture or slot.use:
        return

    slot_type = "col" if slot.use_rgb_to_intensity else "f"
    tex = slot.texture
    base_name = remove_serial_number(tex.name)
    tex.type = "BLEND"

    if hasattr(tex, "progression"):
        tex.progression = "DIAGONAL"
    tex.use_color_ramp = True
    tex.use_preview_alpha = True
    elements = tex.color_ramp.elements

    element_count = 4
    if element_count < len(elements):
        for i in range(len(elements) - element_count):
            elements.remove(elements[-1])
    elif len(elements) < element_count:
        for i in range(element_count - len(elements)):
            elements.new(1.0)

    (
        elements[0].position,
        elements[1].position,
        elements[2].position,
        elements[3].position,
    ) = 0.2, 0.21, 0.25, 0.26

    if slot_type == "col":
        elements[0].color = [0.2, 1, 0.2, 1]
        elements[-1].color = slot.color[:] + (slot.diffuse_color_factor,)
        if 0.3 < mathutils.Color(slot.color[:3]).v:
            elements[1].color, elements[2].color = [0, 0, 0, 1], [0, 0, 0, 1]
        else:
            elements[1].color, elements[2].color = [1, 1, 1, 1], [1, 1, 1, 1]

    elif slot_type == "f":
        elements[0].color = [0.2, 0.2, 1, 1]
        multi = 1.0
        if base_name == "_OutlineWidth":
            multi = 200
        elif base_name == "_RimPower":
            multi = 1.0 / 30.0
        value = slot.diffuse_color_factor * multi
        elements[-1].color = [value, value, value, 1]
        if 0.3 < value:
            elements[1].color, elements[2].color = [0, 0, 0, 1], [0, 0, 0, 1]
        else:
            elements[1].color, elements[2].color = [1, 1, 1, 1], [1, 1, 1, 1]


# 必要なエリアタイプを設定を変更してでも取得
def get_request_area(context, request_type, except_types=None):
    if except_types is None:
        except_types = ["VIEW_3D", "PROPERTIES", "INFO", compat.pref_type()]

    request_areas = [
        (a, a.width * a.height) for a in context.screen.areas if a.type == request_type
    ]
    candidate_areas = [
        (a, a.width * a.height)
        for a in context.screen.areas
        if a.type not in except_types
    ]

    return_areas = request_areas[:] if len(request_areas) else candidate_areas
    if not len(return_areas):
        return None

    return_areas.sort(key=lambda i: i[1])
    return_area = return_areas[-1][0]
    return_area.type = request_type
    return return_area


# 複数のデータを完全に削除
def remove_data(target_data):
    try:
        target_data = target_data[:]
    except:
        target_data = [target_data]

    if compat.IS_LEGACY:
        for data in target_data:
            if data.__class__.__name__ == "Object":
                if data.name in bpy.context.scene.objects:
                    bpy.context.scene.objects.unlink(data)
    else:
        for data in target_data:
            if data.__class__.__name__ == "Object":
                if data.name in bpy.context.scene.collection.objects:
                    bpy.context.scene.collection.objects.unlink(data)

    # https://developer.blender.org/T49837
    # によると、xxx.remove(data, do_unlink=True)で十分
    #
    # for data in target_data:
    # 	users = getattr(data, 'users')
    # 	if users and 'user_clear' in dir(data):
    # 		data.user_clear()

    # for data in target_data:
    #    for data_str in dir(bpy.data):
    #        if not data_str.endswith('s'):
    #            continue
    #        try:
    #            data_collection = getattr(bpy.data.actions, data_str)
    #            if data.__class__.__name__ == data_collection[0].__class__.__name__:
    #                data_collection.remove(data, do_unlink=True)
    #                break
    #        except:
    #            pass

    for data in target_data:
        for data_str in dir(bpy.data):
            if not data_str.endswith("s"):
                continue
            try:
                if data.__class__.__name__ == eval(
                    "bpy.data.%s[0].__class__.__name__" % data_str
                ):
                    exec("bpy.data.%s.remove(data, do_unlink=True)" % data_str)
                    break
            except:
                pass


# オブジェクトのマテリアルを削除/復元するクラス
class material_restore:
    def __init__(self, ob):
        override = bpy.context.copy()
        override["object"] = ob
        self.object = ob

        self.slots = [
            slot.material if slot.material else None for slot in ob.material_slots
        ]

        self.mesh_data = []
        for index, slot in enumerate(ob.material_slots):
            mesh_datum = []
            for face in ob.data.polygons:
                if face.material_index == index:
                    mesh_datum.append(face.index)
            self.mesh_data.append(mesh_datum)

        for slot in ob.material_slots[:]:
            bpy.ops.object.material_slot_remove(override)

    def restore(self):
        override = bpy.context.copy()
        override["object"] = self.object

        for slot in self.object.material_slots[:]:
            bpy.ops.object.material_slot_remove(override)

        for index, mate in enumerate(self.slots):
            bpy.ops.object.material_slot_add(override)
            slot = self.object.material_slots[index]
            if slot:
                slot.material = mate
            for face_index in self.mesh_data[index]:
                self.object.data.polygons[face_index].material_index = index


# 現在のレイヤー内のオブジェクトをレンダリングしなくする/戻す
class hide_render_restore:
    def __init__(self, render_objects=[]):
        try:
            render_objects = render_objects[:]
        except:
            render_objects = [render_objects]

        if not len(render_objects):
            render_objects = bpy.context.selected_objects[:]

        self.render_objects = render_objects[:]
        self.render_object_names = [ob.name for ob in render_objects]

        self.rendered_objects = []
        for ob in render_objects:
            if ob.hide_render:
                self.rendered_objects.append(ob)
                ob.hide_render = False

        self.hide_rendered_objects = []
        if compat.IS_LEGACY:
            for ob in bpy.data.objects:
                for layer_index, is_used in enumerate(bpy.context.scene.layers):
                    if not is_used:
                        continue
                    if (
                        ob.layers[layer_index]
                        and is_used
                        and ob.name not in self.render_object_names
                        and not ob.hide_render
                    ):
                        self.hide_rendered_objects.append(ob)
                        ob.hide_render = True
                        break
        else:
            clct_children = bpy.context.scene.collection.children
            for ob in bpy.data.objects:
                if ob.name not in self.render_object_names and not ob.hide_render:
                    # ble-2.8ではlayerではなく、collectionからのリンクで判断
                    for clct in bpy.context.window.view_layer.layer_collection.children:
                        if (
                            clct.exclude is False
                            and ob.name in clct_children[clct.name].objects.keys()
                        ):
                            self.hide_rendered_objects.append(ob)
                            ob.hide_render = True
                            break

    def restore(self):
        for ob in self.rendered_objects:
            ob.hide_render = True
        for ob in self.hide_rendered_objects:
            ob.hide_render = False


# 指定エリアに変数をセット
def set_area_space_attr(area, attr_name, value):
    if not area:
        return
    for space in area.spaces:
        if space.type == area.type:
            space.__setattr__(attr_name, value)
            break


# スムーズなグラフを返す1
def in_out_quad_blend(f):
    if f <= 0.5:
        return 2.0 * math.sqrt(f)
    f -= 0.5
    return 2.0 * f * (1.0 - f) + 0.5


# スムーズなグラフを返す2
def bezier_blend(f):
    return math.sqrt(f) * (3.0 - 2.0 * f)


# 三角関数でスムーズなグラフを返す
def trigonometric_smooth(x):
    return math.sin((x - 0.5) * math.pi) * 0.5 + 0.5


# ノード取得クラス
class NodeHandler:
    node_name = bpy.props.StringProperty(name="NodeName")

    def get_node(self, context):
        mate = context.material
        if mate and mate.use_nodes:
            return mate.node_tree.nodes.get(self.node_name)

            # if node is None:
            # # 見つからない場合は、シリアル番号付きのノードを探す
            # prefix = self.node_name + '.'
            # for n in nodes:
            # 	if n.name.startwith(prefix):
            # 		node = n
            # 		break

        return None


# @compat.BlRegister()
class CNV_UL_generic_selector(bpy.types.UIList):
    bl_label = "CNV_UL_generic_selector"
    bl_options = {"DEFAULT_CLOSED"}
    bl_region_type = "WINDOW"
    bl_space_type = "PROPERTIES"

    # Constants (flags)
    # Be careful not to shadow FILTER_ITEM!
    # bitflag_soft_filter = 1073741824 >> 0
    bitflag_soft_filter = 1073741824 >> 3

    bitflag_forced_value = 1073741824 >> 10
    bitflag_forced_true = 1073741824 >> 11
    bitflag_forced_false = 1073741824 >> 12

    cached_values = {}
    expanded_layout = False

    # Custom properties, saved with .blend file.
    use_filter_name_reverse = bpy.props.BoolProperty(
        name="Reverse Name",
        default=False,
        options=set(),
        description="Reverse name filtering",
    )
    # use_filter_deform = bpy.props.BoolProperty(
    #    name="Only Deform",
    #    default=True,
    #    options=set(),
    #    description="Only show deforming vertex groups",
    # )
    # use_filter_deform_reverse = bpy.props.BoolProperty(
    #    name="Other",
    #    default=False,
    #    options=set(),
    #    description="Only show non-deforming vertex groups",
    # )
    # use_filter_empty = bpy.props.BoolProperty(
    #    name="Filter Empty",
    #    default=False,
    #    options=set(),
    #    description="Whether to filter empty vertex groups",
    # )
    # use_filter_empty_reverse = bpy.props.BoolProperty(
    #    name="Reverse Empty",
    #    default=False,
    #    options=set(),
    #    description="Reverse empty filtering",
    # )

    # This allows us to have mutually exclusive options, which are also all disable-able!
    def _gen_order_update(name1, name2):
        def _u(self, ctxt):
            if getattr(self, name1):
                setattr(self, name2, False)

        return _u

    use_order_name = bpy.props.BoolProperty(
        name="Name",
        default=False,
        options=set(),
        description="Sort groups by their name (case-insensitive)",
        update=_gen_order_update("use_order_name", "use_order_importance"),
    )
    use_filter_orderby_invert = bpy.props.BoolProperty(
        name="Order by Invert",
        default=False,
        options=set(),
        description="Invert the sort by order",
    )
    # use_order_importance = bpy.props.BoolProperty(
    #    name="Importance",
    #    default=False,
    #    options=set(),
    #    description="Sort groups by their average weight in the mesh",
    #    update=_gen_order_update("use_order_importance", "use_order_name"),
    # )

    # Usual draw item function.
    def draw_item(
        self,
        context,
        layout,
        data,
        item,
        icon_value,
        active_data,
        active_propname,
        index,
        flt_flag,
    ):
        # Just in case, we do not use it here!
        self.use_filter_invert = False

        # assert(isinstance(item, bpy.types.VertexGroup)
        # vgroup = getattr(data, 'matched_vgroups')[item.index]
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            # Here we use one feature of new filtering feature: it can pass data to draw_item, through flt_flag
            # parameter, which contains exactly what filter_items set in its filter list for this item!
            # In this case, we show empty groups grayed out.
            cached_value = self.cached_values.get(item.name, None)
            if (cached_value != None) and (cached_value != item.value):
                item.preferred = item.value

            force_values = flt_flag & self.bitflag_forced_value
            print("GET force_values =", force_values)
            if force_values:
                print("FORCE VALUES")
                if flt_flag & self.bitflag_forced_true:
                    item.value = True
                elif flt_flag & self.bitflag_forced_false:
                    item.value = False
                else:
                    item.value = item.preferred

            self.cached_values[item.name] = item.value

            if flt_flag & self.bitflag_soft_filter:
                row = layout.row()
                row.enabled = False
                # row.alignment = 'LEFT'
                row.prop(item, "value", text=item.name, icon=item.icon)
            else:
                layout.prop(item, "value", text=item.name, icon=item.icon)

            # layout.prop(item, "value", text=item.name, icon=item.icon)
            icon = "RADIOBUT_ON" if item.preferred else "RADIOBUT_OFF"
            layout.prop(
                item, "preferred", text="", icon=compat.icon(icon), emboss=False
            )

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            if flt_flag & self.VGROUP_EMPTY:
                layout.enabled = False
            layout.label(text="", icon_value=icon)

    def draw_filter(self, context, layout):
        # Nothing much to say here, it's usual UI code...
        row = layout.row()
        if not self.expanded_layout:
            layout.active = True
            layout.enabled = True
            row.active = True
            row.enabled = True
            self.expanded_layout = True

        subrow = row.row(align=True)
        subrow.prop(self, "filter_name", text="")
        icon = "ZOOM_OUT" if self.use_filter_name_reverse else "ZOOM_IN"
        subrow.prop(self, "use_filter_name_reverse", text="", icon=icon)

        # subrow = row.row(align=True)
        # subrow.prop(self, "use_filter_deform", toggle=True)
        # icon = 'ZOOM_OUT' if self.use_filter_deform_reverse else 'ZOOM_IN'
        # subrow.prop(self, "use_filter_deform_reverse", text="", icon=icon)

        # subrow = row.row(align=True)
        # subrow.prop(self, "use_filter_empty", toggle=True)
        # icon = 'ZOOM_OUT' if self.use_filter_empty_reverse else 'ZOOM_IN'
        # subrow.prop(self, "use_filter_empty_reverse", text="", icon=icon)

        row = layout.row(align=True)
        row.label(text="Order by:")
        row.prop(self, "use_order_name", toggle=True)
        # row.prop(self, "use_order_importance", toggle=True)
        icon = "TRIA_UP" if self.use_filter_orderby_invert else "TRIA_DOWN"
        row.prop(self, "use_filter_orderby_invert", text="", icon=icon)

    def filter_items(self, context, data, propname):
        # This function gets the collection property (as the usual tuple (data, propname)), and must return two lists:
        # * The first one is for filtering, it must contain 32bit integers were self.bitflag_filter_item marks the
        #   matching item as filtered (i.e. to be shown), and 31 other bits are free for custom needs. Here we use the
        #   first one to mark VGROUP_EMPTY.
        # * The second one is for reordering, it must return a list containing the new indices of the items (which
        #   gives us a mapping org_idx -> new_idx).
        # Please note that the default UI_UL_list defines helper functions for common tasks (see its doc for more info).
        # If you do not make filtering and/or ordering, return empty list(s) (this will be more efficient than
        # returning full lists doing nothing!).
        items = getattr(data, propname)

        # if self.armature == None:
        #    target_ob, source_ob = common.get_target_and_source_ob(context)
        #    armature_ob = target_ob.find_armature() or source_ob.find_armature()
        #    self.armature = armature_ob and armature_ob.data or False
        #
        # if not self.local_bone_names:
        #    target_ob, source_ob = common.get_target_and_source_ob(context)
        #    bone_data_ob = (target_ob.get("LocalBoneData:0") and target_ob) or (source_ob.get("LocalBoneData:0") and source_ob) or None
        #    if bone_data_ob:
        #        local_bone_data = model_export.CNV_OT_export_cm3d2_model.local_bone_data_parser(model_export.CNV_OT_export_cm3d2_model.indexed_data_generator(bone_data_ob, prefix="LocalBoneData:"))
        #        self.local_bone_names = [ bone['name'] for bone in local_bone_data ]

        if not self.cached_values:
            self.cached_values = {item.name: item.value for item in items}
        # vgroups = [ getattr(data, 'matched_vgroups')[item.index][0]   for item in items ]
        helper_funcs = bpy.types.UI_UL_list

        # Default return values.
        flt_flags = []
        flt_neworder = []

        # Pre-compute of vgroups data, CPU-intensive. :/
        # vgroups_empty = self.filter_items_empty_vgroups(context, vgroups)

        # Filtering by name
        if self.filter_name:
            flt_flags = helper_funcs.filter_items_by_name(
                self.filter_name,
                self.bitflag_filter_item,
                items,
                "name",
                reverse=self.use_filter_name_reverse,
            )
        if not flt_flags:
            flt_flags = [self.bitflag_filter_item] * len(items)

        # for idx, vg in enumerate(items):
        #    # Filter by deform.
        #    if self.use_filter_deform:
        #        flt_flags[idx] |= self.VGROUP_DEFORM
        #        if self.use_filter_deform:
        #            if self.armature and self.armature.get(vg.name):
        #                if not self.use_filter_deform_reverse:
        #                    flt_flags[idx] &= ~self.VGROUP_DEFORM
        #            elif bone_data_ob and (vg.name in self.local_bone_names):
        #                if not self.use_filter_deform_reverse:
        #                    flt_flags[idx] &= ~self.VGROUP_DEFORM
        #            elif self.use_filter_deform_reverse or (not self.armature and not self.local_bone_names):
        #                flt_flags[idx] &= ~self.VGROUP_DEFORM
        #    else:
        #        flt_flags[idx] &= ~self.VGROUP_DEFORM
        #
        #    # Filter by emptiness.
        #    #if vgroups_empty[vg.index][0]:
        #    #    flt_flags[idx] |= self.VGROUP_EMPTY
        #    #    if self.use_filter_empty and self.use_filter_empty_reverse:
        #    #        flt_flags[idx] &= ~self.bitflag_filter_item
        #    #elif self.use_filter_empty and not self.use_filter_empty_reverse:
        #    #    flt_flags[idx] &= ~self.bitflag_filter_item

        # Reorder by name or average weight.
        if self.use_order_name:
            flt_neworder = helper_funcs.sort_items_by_name(items, "name")
        # elif self.use_order_importance:
        #    _sort = [(idx, vgroups_empty[vg.index][1]) for idx, vg in enumerate(vgroups)]
        #    flt_neworder = helper_funcs.sort_items_helper(_sort, lambda e: e[1], True)

        return flt_flags, flt_neworder


@compat.BlRegister()
class CNV_SelectorItem(bpy.types.PropertyGroup):
    bl_label = "CNV_SelectorItem"
    bl_region_type = "WINDOW"
    bl_space_type = "PROPERTIES"

    name = bpy.props.StringProperty(name="Name", default="Unknown")
    value = bpy.props.BoolProperty(name="Value", default=True)
    index = bpy.props.IntProperty(name="Index", default=-1)
    preferred = bpy.props.BoolProperty(name="Prefered", default=True)
    icon = bpy.props.StringProperty(name="Icon", default="NONE")

    filter0 = bpy.props.BoolProperty(name="Filter 0", default=False)
    filter1 = bpy.props.BoolProperty(name="Filter 1", default=False)
    filter2 = bpy.props.BoolProperty(name="Filter 2", default=False)
    filter3 = bpy.props.BoolProperty(name="Filter 3", default=False)


# luvoid : for loop helper returns values with matching keys
def values_of_matched_keys(dict1, dict2):
    value_list = []
    items1 = dict1.items()
    items2 = dict2.items()
    if len(items1) <= len(items2):
        items1.reverse()
        for k1, v1 in items1:
            for i in range(len(items2) - 1, 0 - 1, -1):
                k2, v2 = items2[i]
                if k1 == k2:
                    value_list.append((v1, v2))
                    del items2[i]
    else:
        items2.reverse()
        for k2, v2 in items2:
            for i in range(len(items1) - 1, 0 - 1, -1):
                k1, v1 = items1[i]
                if k1 == k2:
                    value_list.append((v1, v2))
                    del items1[i]

    value_list.reverse()
    return value_list


# luvoid : helper to easily get source and target objects
def get_target_and_source_ob(context: bpy.context, copyTarget=False, copySource=False):
    target_ob: bpy.types.Object = None
    source_ob: bpy.types.Object = None
    target_original_ob: bpy.types.Object = None
    source_original_ob: bpy.types.Object = None

    selected_objects = list(context.selected_objects)

    target_original_ob = context.active_object
    if copyTarget:
        target_ob = target_original_ob.copy()
        target_ob.data = target_ob.data.copy()
        compat.link(context.scene, target_ob)
        context.view_layer.update()
        # bpy.ops.object.select_all(action='DESELECT')
        # compat.set_select(target_original_ob, select=True)
        # bpy.ops.object.duplicate()
        # target_ob = context.active_object
    else:
        target_ob = target_original_ob

    for ob in selected_objects:
        if ob != target_ob:
            source_original_ob = ob
            break

    if copySource:
        source_ob = source_original_ob.copy()
        new_data = source_original_ob.data.copy()
        print(f"new_data = {new_data.shape_keys}")
        source_ob.data = new_data
        print(f"source_ob.data = {source_ob.data.shape_keys}")
        compat.link(context.scene, source_ob)
        context.view_layer.update()
        # bpy.ops.object.select_all(action='DESELECT')
        # compat.set_select(source_original_ob, select=True)
        # bpy.ops.object.duplicate()
        # print(f"duplicated_object = {context.active_object}")
        # source_ob = context.active_object
    else:
        source_ob = source_original_ob

    bpy.ops.object.select_all(action="DESELECT")
    for obj in selected_objects:
        compat.set_select(obj, select=True)

    compat.set_active(context, target_ob)
    compat.set_select(target_ob, select=True)
    compat.set_select(source_ob, select=True)
    if copyTarget:
        compat.set_select(target_original_ob, select=False)
    if copySource:
        compat.set_select(source_original_ob, select=False)

    to_return = [target_ob, source_ob]
    if copyTarget:
        to_return.append(target_original_ob)
    if copySource:
        to_return.append(source_original_ob)
    return tuple(to_return)


# luvoid
def is_descendant_of(bone, ancestor) -> bool:
    """Returns true if a bone is the descendant of the given ancestor"""
    while bone.parent:
        bone = bone.parent
        if bone.name == ancestor.name:
            return True
    return False
