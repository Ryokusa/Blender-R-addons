import os
import bpy
from . import common
from . import compat


@compat.BlRegister()
class CNV_OT_import_cm3d2_tex(bpy.types.Operator):
    bl_idname = 'image.import_cm3d2_tex'
    bl_label = "Import .tex"
    bl_description = "Imports a CM3D2 tex file (.tex)"
    bl_options = {'REGISTER'}

    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".tex;.png"
    filter_glob = bpy.props.StringProperty(default="*.tex;*.png", options={'HIDDEN'})

    items = [
        ('PACK', "Package", "", 'PACKAGE', 1),
        ('PNG', "Opens or converts to png", "", 'IMAGE_DATA', 2),
    ]
    mode = bpy.props.EnumProperty(items=items, name="Mode", default='PNG')

    def invoke(self, context, event):
        prefs = common.preferences()
        if prefs.tex_default_path:
            self.filepath = common.default_cm3d2_dir(prefs.tex_default_path, None, "tex")
        else:
            self.filepath = common.default_cm3d2_dir(prefs.tex_import_path, None, "tex")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        box = self.layout.box()
        col = box.column(align=True)
        col.label(text="Mode", icon='FILESEL')
        col.prop(self, 'mode', icon='FILESEL', expand=True)

    def execute(self, context):
        common.preferences().tex_import_path = self.filepath
        try:
            tex_data = common.load_cm3d2tex(self.filepath)
            if tex_data is None:
                # bpy.ops.image.open(filepath=self.filepath)
                # img = context.edit_image
                self.report(type={'ERROR'}, message="Failed to open the file, it does not exist or is inaccessible" + self.filepath)
                return {'CANCELLED'}

            tex_format = tex_data[1]
            if not (tex_format == 3 or tex_format == 5):
                self.report(type={'ERROR'}, message="Unsupported tex format! format=" + str(tex_format))
                return {'CANCELLED'}

            root, ext = os.path.splitext(self.filepath)
            png_path = root + ".png"
            is_png_overwrite = os.path.exists(png_path)
            if self.mode == 'PACK' and is_png_overwrite:
                png_path += ".temp.png"
            with open(png_path, 'wb') as png_file:
                png_file.write(tex_data[-1])
            bpy.ops.image.open(filepath=png_path)
            img = context.edit_image
            img.name = os.path.basename(self.filepath)
            img['cm3d2_path'] = common.get_tex_cm3d2path(root + ".png")

            if self.mode == 'PACK':
                img.pack(as_png=True)
                os.remove(png_path)
            return {'FINISHED'}

        except:
            self.report(type={'ERROR'}, message="Failed to open file, inaccessible or file does not exist."+ self.filepath)
            return {'CANCELLED'}


# メニューを登録する関数
def menu_func(self, context):
    self.layout.separator()
    self.layout.operator(CNV_OT_import_cm3d2_tex.bl_idname, icon_value=common.kiss_icon())
