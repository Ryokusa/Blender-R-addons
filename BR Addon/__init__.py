# アドオンを読み込む時に最初にこのファイルが読み込まれます

# アドオン情報
bl_info = {
    "name": "BR Addon",
    "author": "@saidenka_cm3d2, @trzrz, @luvoid @ryokusa",
    "version": ("ryokusa", 2024, 3, 19),
    "blender": (3, 3, 0),
    "description": "カスメ関連機能削除改変プラグイン",
    "warning": "",
    "wiki_url": "https://github.com/Ryokusa/Blender-R-addons/blob/bl_28/README.md",
    "tracker_url": "https://github.com/Ryokusa/Blender-R-addons",
    "category": "Import-Export",
}

import importlib
from . import package_helper

if "bpy" in locals():
    importlib.reload(package_helper)


# Install dependencies
def install_dependencies():
    import bpy  # import inside a function, so "bpy" in locals() check later is unchanged

    if not package_helper.check_module("pythonnet"):
        print("Installing dependency 'pythonnet'...")
        package_helper.install_package("pythonnet==3.0.1")
        raise Exception("Dependencies installed. Restart is required.")
    else:
        print("Package 'pythonnet' is installed")


install_dependencies()


# Dynamically detect what modules are imported in the following section
if "_SUB_MODULES" not in locals():
    _SUB_MODULES = []
_pre_locals = locals().copy()

# サブスクリプト群をインポート
if True:
    from . import compat
    from . import common

    from . import misc_DATA_PT_context_arm
    from . import misc_DATA_PT_modifiers
    from . import misc_INFO_HT_header
    from . import misc_INFO_MT_curve_add
    from . import misc_INFO_MT_help
    from . import misc_MESH_MT_attribute_context_menu
    from . import misc_MESH_MT_shape_key_specials
    from . import misc_MESH_MT_vertex_group_specials
    from . import misc_OBJECT_PT_context_object
    from . import misc_OBJECT_PT_transform
    from . import misc_VIEW3D_MT_edit_mesh_specials
    from . import misc_VIEW3D_MT_edit_mesh_split
    from . import misc_VIEW3D_MT_pose_apply
    from . import misc_VIEW3D_PT_tools_weightpaint

    from . import translations


# Save modules that were loaded in the previous section
for key, module in locals().copy().items():
    if key == "_pre_locals":
        continue
    if key not in _pre_locals:
        _SUB_MODULES.append(module)

if "bpy" in locals():
    import importlib

    for module in _SUB_MODULES:
        try:
            importlib.reload(module)
        except ModuleNotFoundError:
            # module was renamed or moved
            pass

import bpy, os.path, bpy.utils.previews  # type: ignore


# アドオン設定
@compat.BlRegister()
class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    backup_ext = bpy.props.StringProperty(
        name="バックアップの拡張子 (空欄で無効)",
        description="エクスポート時にバックアップを作成時この拡張子で複製します、空欄でバックアップを無効",
        default="bak",
    )
    scale = bpy.props.FloatProperty(
        name="倍率",
        description="Blenderでモデルを扱うときの拡大率",
        default=5,
        min=0.01,
        max=100,
        soft_min=0.01,
        soft_max=100,
        step=10,
        precision=2,
    )

    skip_shapekey = bpy.props.BoolProperty(
        name="無変更シェイプキーをスキップ",
        default=True,
        description="ベースと同じシェイプキーを出力しない",
    )
    is_apply_modifiers = bpy.props.BoolProperty(
        name="モディファイアを適用", default=False
    )

    custom_normal_blend = bpy.props.FloatProperty(
        name="CM3D2用法線のブレンド率",
        default=0.5,
        min=0,
        max=1,
        soft_min=0,
        soft_max=1,
        step=3,
        precision=3,
    )

    bone_display_type = bpy.props.EnumProperty(
        items=[
            (
                "OCTAHEDRAL",
                "Octahedral",
                "Display bones as octahedral shape (default).",
            ),
            ("STICK", "Stick", "Display bones as simple 2D lines with dots."),
            (
                "BBONE",
                "B-Bone",
                "Display bones as boxes, showing subdivision and B-Splines.",
            ),
            (
                "ENVELOPE",
                "Envelope",
                "Display bones as extruded spheres, showing deformation influence volume.",
            ),
            (
                "WIRE",
                "Wire",
                "Display bones as thin wires, showing subdivision and B-Splines.",
            ),
        ],
        name="Display Type",
        default="STICK",
    )
    show_bone_names = bpy.props.BoolProperty(
        name="Show Bone Names", default=False, description="Display bone names"
    )
    show_bone_axes = bpy.props.BoolProperty(
        name="Show Bone Axes", default=False, description="Display bone axes"
    )
    show_bone_custom_shapes = bpy.props.BoolProperty(
        name="Show Bone Shapes",
        default=True,
        description="Display bones with their custom shapes",
    )
    show_bone_group_colors = bpy.props.BoolProperty(
        name="Show Bone Group Colors",
        default=True,
        description="Display bone group colors",
    )
    show_bone_in_front = bpy.props.BoolProperty(
        name="Show Bones in Front",
        default=True,
        description="Make the object draw in front of others",
    )

    def draw(self, context):
        if compat.IS_LEGACY:
            self.layout.label(
                text="ここの設定は「ユーザー設定の保存」ボタンを押すまで保存されていません",
                icon="QUESTION",
            )
        else:
            self.layout.label(
                text="設定値を変更した場合、「プリファレンスを保存」ボタンを押下するか、「プリファレンスを自動保存」を有効にして保存してください",
                icon="QUESTION",
            )

        col = self.layout.column()
        col.label(text="Blender-R-addons Info")
        factor = 0.25
        split = compat.layout_split(col.row(), factor)
        split.label(text="Add-on Version: ")
        split.label(text=".".join(str(i) for i in bl_info["version"]))
        split = compat.layout_split(col.row(), factor)
        split.label(text="Branch: ")
        split.label(text=common.BRANCH)
        split = compat.layout_split(col.row(), factor)
        split.label(text="Repo URL: ")
        split.label(text=common.URL_REPOS)
        split = compat.layout_split(col.row(), factor)
        split.label(text="Blender Version: ")
        split.label(
            text=".".join(str(i) for i in bpy.app.version)
            if hasattr(bpy.app, "version")
            else "Legacy"
        )
        split = compat.layout_split(col.row(), factor)
        split.label(text="Blender Language: ")
        split.label(text=compat.get_system(bpy.context).language or "None")
        default_locale = "UNKNOWN"
        try:
            import locale

            default_locale = locale.getdefaultlocale()[0]
        except:
            pass
        split = compat.layout_split(col.row(), factor)
        split.label(text="Default Language: ")
        split.label(text=default_locale)

        self.layout.label(text="." * 9999)
        self.layout.label(text="Preferences:")

        self.layout.prop(self, "backup_ext", icon="FILE_BACKUP")

        box = self.layout.box()
        box.label(text="Default Armature Settings", icon="ARMATURE_DATA")
        if not compat.IS_LEGACY:
            box.use_property_split = True
        box.prop(self, "bone_display_type", text="Display As")
        if compat.IS_LEGACY:
            flow = box.column_flow(align=True)
        else:
            flow = box.grid_flow(align=True)
        col = flow.column()
        col.prop(self, "show_bone_names", text="Names")
        col = flow.column()
        col.prop(self, "show_bone_axes", text="Axes")
        col = flow.column()
        col.prop(self, "show_bone_custom_shapes", text="Shapes")
        col = flow.column()
        col.prop(self, "show_bone_group_colors", text="Group Colors")
        col = flow.column()
        col.prop(self, "show_bone_in_front", text="In Front")

        box = self.layout.box()
        box.label(text="各操作の初期パラメータ", icon="MATERIAL")
        row = box.row()  # export
        row.prop(self, "custom_normal_blend", icon="SNAP_NORMAL")
        row.prop(self, "skip_shapekey", icon="SHAPEKEY_DATA")
        row.prop(self, "is_apply_modifiers", icon="MODIFIER")

        row = self.layout.row()
        # TODO: Update関連処理を変更
        # row.operator("script.update_cm3d2_converter", icon="FILE_REFRESH")
        # row.menu("INFO_MT_help_CM3D2_Converter_RSS", icon="INFO")

        # self.layout.operator("cm3d2_converter.dump_py_messages")


# プラグインをインストールしたときの処理
def register():
    pcoll = bpy.utils.previews.new()
    dir = os.path.dirname(__file__)
    pcoll.load("KISS", os.path.join(dir, "kiss.png"), "IMAGE")
    common.preview_collections["main"] = pcoll
    common.bl_info = bl_info

    compat.BlRegister.register()
    if compat.IS_LEGACY:
        bpy.types.INFO_MT_curve_add.append(misc_INFO_MT_curve_add.menu_func)
        bpy.types.INFO_MT_help.append(misc_INFO_MT_help.menu_func)

        bpy.types.VIEW3D_PT_tools_weightpaint.append(
            misc_VIEW3D_PT_tools_weightpaint.menu_func
        )

        # menu
        bpy.types.DATA_PT_vertex_colors.append(
            misc_MESH_MT_attribute_context_menu.menu_func
        )
        bpy.types.MESH_MT_shape_key_specials.append(
            misc_MESH_MT_shape_key_specials.menu_func
        )
        bpy.types.MESH_MT_vertex_group_specials.append(
            misc_MESH_MT_vertex_group_specials.menu_func
        )
        bpy.types.VIEW3D_MT_edit_mesh_specials.append(
            misc_VIEW3D_MT_edit_mesh_specials.menu_func
        )
        bpy.types.VIEW3D_MT_edit_mesh.append(misc_VIEW3D_MT_edit_mesh_split.menu_func)
    else:
        bpy.types.VIEW3D_MT_curve_add.append(misc_INFO_MT_curve_add.menu_func)
        # (更新機能)
        bpy.types.TOPBAR_MT_help.append(misc_INFO_MT_help.menu_func)

        # マテリアルパネルの追加先がないため、別途Panelを追加
        # bpy.types.MATERIAL_PT_context_xxx.append(misc_MATERIAL_PT_context_material.menu_func)

        # TODO 修正＆動作確認後にコメント解除  (ベイク)
        # レンダーエンジンがCycles指定時のみになる
        # bpy.types.CYCLES_RENDER_PT_bake.append(misc_RENDER_PT_bake.menu_func)
        bpy.types.VIEW3D_PT_tools_weightpaint_options.append(
            misc_VIEW3D_PT_tools_weightpaint.menu_func
        )

        # context menu
        if bpy.app.version < (3, 0):
            bpy.types.DATA_PT_vertex_colors.append(
                misc_MESH_MT_attribute_context_menu.menu_func
            )
        else:
            bpy.types.MESH_MT_attribute_context_menu.append(
                misc_MESH_MT_attribute_context_menu.menu_func
            )
            bpy.types.MESH_MT_color_attribute_context_menu.append(
                misc_MESH_MT_attribute_context_menu.menu_func
            )
        bpy.types.MESH_MT_shape_key_context_menu.append(
            misc_MESH_MT_shape_key_specials.menu_func
        )
        bpy.types.MESH_MT_vertex_group_context_menu.append(
            misc_MESH_MT_vertex_group_specials.menu_func
        )
        bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(
            misc_VIEW3D_MT_edit_mesh_specials.menu_func
        )
        if bpy.app.version < (2, 90):
            bpy.types.VIEW3D_MT_edit_mesh.append(
                misc_VIEW3D_MT_edit_mesh_split.menu_func
            )
        else:
            bpy.types.VIEW3D_MT_edit_mesh_split.append(
                misc_VIEW3D_MT_edit_mesh_split.menu_func
            )

    bpy.types.DATA_PT_context_arm.append(misc_DATA_PT_context_arm.menu_func)
    bpy.types.DATA_PT_modifiers.append(misc_DATA_PT_modifiers.menu_func)
    bpy.types.INFO_HT_header.append(misc_INFO_HT_header.menu_func)

    bpy.types.OBJECT_PT_context_object.append(misc_OBJECT_PT_context_object.menu_func)
    bpy.types.OBJECT_PT_transform.append(misc_OBJECT_PT_transform.menu_func)
    bpy.types.VIEW3D_MT_pose_apply.append(misc_VIEW3D_MT_pose_apply.menu_func)

    translations.register(__name__)

    # Change wiki_url based on locale (only works in legacy version)
    locale = translations.get_locale()
    if locale != "ja_JP":
        bl_info["wiki_url"] = (
            common.URL_REPOS + f"blob/bl_28/translations/{locale}/README.md"
        )


# プラグインをアンインストールしたときの処理
def unregister():
    if compat.IS_LEGACY:
        bpy.types.INFO_MT_curve_add.remove(misc_INFO_MT_curve_add.menu_func)
        bpy.types.INFO_MT_help.remove(misc_INFO_MT_help.menu_func)

        bpy.types.VIEW3D_PT_tools_weightpaint.remove(
            misc_VIEW3D_PT_tools_weightpaint.menu_func
        )

        # menu
        bpy.types.DATA_PT_vertex_colors.remove(
            misc_MESH_MT_attribute_context_menu.menu_func
        )
        bpy.types.MESH_MT_shape_key_specials.remove(
            misc_MESH_MT_shape_key_specials.menu_func
        )
        bpy.types.MESH_MT_vertex_group_specials.remove(
            misc_MESH_MT_vertex_group_specials.menu_func
        )
        bpy.types.VIEW3D_MT_edit_mesh_specials.remove(
            misc_VIEW3D_MT_edit_mesh_specials.menu_func
        )
        bpy.types.VIEW3D_MT_edit_mesh.remove(misc_VIEW3D_MT_edit_mesh_split.menu_func)
    else:
        bpy.types.VIEW3D_MT_curve_add.remove(misc_INFO_MT_curve_add.menu_func)
        bpy.types.TOPBAR_MT_help.remove(misc_INFO_MT_help.menu_func)

        # bpy.types.MATERIAL_MT_context_menu.remove(misc_MATERIAL_PT_context_material.menu_func)
        # bpy.types.CYCLES_RENDER_PT_bake.remove(misc_RENDER_PT_bake.menu_func)

        bpy.types.VIEW3D_PT_tools_weightpaint_options.remove(
            misc_VIEW3D_PT_tools_weightpaint.menu_func
        )
        # menu
        if bpy.app.version < (3, 0):
            bpy.types.DATA_PT_vertex_colors.remove(
                misc_MESH_MT_attribute_context_menu.menu_func
            )
        else:
            bpy.types.MESH_MT_attribute_context_menu.remove(
                misc_MESH_MT_attribute_context_menu.menu_func
            )
            bpy.types.MESH_MT_color_attribute_context_menu.remove(
                misc_MESH_MT_attribute_context_menu.menu_func
            )
        bpy.types.MESH_MT_shape_key_context_menu.remove(
            misc_MESH_MT_shape_key_specials.menu_func
        )
        bpy.types.MESH_MT_vertex_group_context_menu.remove(
            misc_MESH_MT_vertex_group_specials.menu_func
        )
        bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(
            misc_VIEW3D_MT_edit_mesh_specials.menu_func
        )
        if bpy.app.version < (2, 90):
            bpy.types.VIEW3D_MT_edit_mesh.remove(
                misc_VIEW3D_MT_edit_mesh_split.menu_func
            )
        else:
            bpy.types.VIEW3D_MT_edit_mesh_split.remove(
                misc_VIEW3D_MT_edit_mesh_split.menu_func
            )

    bpy.types.DATA_PT_context_arm.remove(misc_DATA_PT_context_arm.menu_func)
    bpy.types.DATA_PT_modifiers.remove(misc_DATA_PT_modifiers.menu_func)
    bpy.types.INFO_HT_header.remove(misc_INFO_HT_header.menu_func)

    bpy.types.OBJECT_PT_context_object.remove(misc_OBJECT_PT_context_object.menu_func)
    bpy.types.OBJECT_PT_transform.remove(misc_OBJECT_PT_transform.menu_func)
    bpy.types.VIEW3D_MT_pose_apply.remove(misc_VIEW3D_MT_pose_apply.menu_func)

    for pcoll in common.preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    common.preview_collections.clear()

    compat.BlRegister.unregister()

    translations.unregister(__name__)


# メイン関数
if __name__ == "__main__":
    register()

# Make sure that this module is always accessible as 'cm3d2converter'
import sys

sys.modules["cm3d2converter"] = sys.modules[__name__]
