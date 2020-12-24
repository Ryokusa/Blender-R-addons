# -*- coding: utf-8 -*-
import bpy
import re
import struct
import os
import mathutils
from typing import Any, Optional


# LEGAY: version less than 2.80
IS_LEGACY = not hasattr(bpy.app, 'version') or bpy.app.version < (2, 80)

OPENGL_TO_BLEND_MAT4 = mathutils.Matrix(
    [(-1,  0,  0,  0), 
     ( 0,  0, -1,  0), 
     ( 0,  1,  0,  0),
     ( 0,  0,  0,  1)]
)
OPENGL_TO_BLEND_QUAT = OPENGL_TO_BLEND_MAT4.to_quaternion()

BLEND_TO_OPENGL_MAT4 = mathutils.Matrix(
    [( 1,  0,  0,  0), 
     ( 0,  0,  1,  0), 
     ( 0, -1,  0,  0),
     ( 0,  0,  0,  1)]
)
BLEND_TO_OPENGL_QUAT = BLEND_TO_OPENGL_MAT4.to_quaternion()

Y_UP_TO_Z_UP_MAT4 = mathutils.Matrix(
    [( 0, -1,  0,  0), 
     ( 1,  0,  0,  0), 
     ( 0,  0,  1,  0),
     ( 0,  0,  0,  1)]
)
Y_UP_TO_Z_UP_QUAT = Y_UP_TO_Z_UP_MAT4.to_quaternion()

Z_UP_TO_Y_UP_MAT4 = Y_UP_TO_Z_UP_MAT4.inverted()
#mathutils.Matrix(     
#    [( 0,  1,  0,  0), 
#     (-1,  0,  0,  0), 
#     ( 0,  0,  1,  0),
#     ( 0,  0,  0,  1)]
#)                     
Z_UP_TO_Y_UP_QUAT = Z_UP_TO_Y_UP_MAT4.to_quaternion()

class BlRegister():
    idnames = set()
    classes = []

    def __init__(self, *args, **kwargs):
        self.make_annotation = kwargs.get('make_annotation', True)
        self.use_bl_attr = kwargs.get('use_bl_attr', True)
        self.only_legacy = kwargs.get('only_legacy', False)
        self.only_latest = kwargs.get('only_latest', False)

    def __call__(self, cls):

        if hasattr(cls, 'bl_idname'):
            bl_idname = cls.bl_idname
        else:
            if self.use_bl_attr:
                bl_ctx = getattr(cls, 'bl_context', '')
                bl_idname = "{}{}{}{}".format(cls.bl_space_type, cls.bl_region_type, bl_ctx, cls.bl_label)
            else:
                bl_idname = cls.__qualname__

        if self.only_legacy:
            if IS_LEGACY:
                BlRegister.add(bl_idname, cls)
        elif self.only_latest:
            if IS_LEGACY is False:
                BlRegister.add(bl_idname, cls)
        else:
            BlRegister.add(bl_idname, cls)

        if self.make_annotation:
            cls = make_annotations(cls)
        return cls

    @classmethod
    def add(cls: type, bl_idname: str, op_class: type) -> None:
        if bl_idname in cls.idnames:
            raise RuntimeError("Duplicate bl_idname: %s" % bl_idname)

        cls.idnames.add(bl_idname)
        cls.classes.append(op_class)

    @classmethod
    def register(cls):
        for cls1 in cls.classes:
            bpy.utils.register_class(cls1)

    @classmethod
    def unregister(cls):
        for cls1 in reversed(cls.classes):
            bpy.utils.unregister_class(cls1)

    @classmethod
    def cleanup(cls):
        cls.classes.clear()
        cls.idnames.clear()


def make_annotations(cls):
    if IS_LEGACY:
        return cls

    cls_props = {}
    for k, v in cls.__dict__.items():
        if isinstance(v, tuple):
            cls_props[k] = v

    annos = cls.__dict__.get('__annotations__')  # type: dict[str, type]
    if annos is None:
        annos = {}
        setattr(cls, '__annotations__', annos)

    for k, v in cls_props.items():
        annos[k] = v
        delattr(cls, k)

    # 親クラスを辿ってアノテーションを生成
    for bc in cls.__bases__:
        # bpyのタイプやbuiltinsの場合はスキップ
        if bc.__module__ in ['bpy_types', 'builtins']:
            continue
        make_annotations(bc)

    return cls


def layout_split(layout, factor=0.0, align=False):
    if IS_LEGACY:
        return layout.split(percentage=factor, align=align)

    return layout.split(factor=factor, align=align)


def get_active():
    if IS_LEGACY:
        return bpy.context.scene.objects.active

    return bpy.context.view_layer.objects.active

def get_active(context):
    if IS_LEGACY:
        return context.scene.objects.active

    return context.view_layer.objects.active


def set_active(context, obj):
    if IS_LEGACY:
        context.scene.objects.active = obj
    else:
        context.view_layer.objects.active = obj


def get_active_uv(me):
    if IS_LEGACY:
        uvs = me.uv_textures
    else:
        uvs = me.uv_layers
    return uvs.active


def set_display_type(ob, disp_type):
    if IS_LEGACY:
        ob.draw_type = disp_type
    else:
        ob.display_type = disp_type


def get_select(obj: bpy.types.Object) -> bool:
    if IS_LEGACY:
        return obj.select

    return obj.select_get()


def set_select(obj: bpy.types.Object, select: bool) -> None:
    if IS_LEGACY:
        obj.select = select
    else:
        obj.select_set(select)


def is_select(*args) -> bool:
    """すべてが選択状態であるかを判定する."""
    if IS_LEGACY:
        return all(arg.select for arg in args)

    return all(arg.select_get() for arg in args)


def get_hide(obj: bpy.types.Object) -> bool:
    if IS_LEGACY:
        return obj.hide

    return obj.hide_viewport


def set_hide(obj: bpy.types.Object, hide: bool):
    if IS_LEGACY:
        obj.hide = hide

    else:
        obj.hide_viewport = hide


def link(scene: bpy.types.Scene, obj: bpy.types.Object):
    if IS_LEGACY:
        scene.objects.link(obj)
    else:
        scene.collection.objects.link(obj)


def unlink(scene: bpy.types.Scene, obj: bpy.types.Object):
    if IS_LEGACY:
        scene.objects.unlink(obj)
    else:
        scene.collection.objects.unlink(obj)


def get_cursor_loc(context):
    if IS_LEGACY:
        return context.space_data.cursor_location
    else:
        return context.scene.cursor.location


def get_lights(blend_data):
    if IS_LEGACY:
        return blend_data.iamps
    else:
        return blend_data.lights


def mul(x, y):
    if IS_LEGACY:
        return x * y

    return x @ y


def mul3(x, y, z):
    if IS_LEGACY:
        return x * y * z

    return x @ y @ z


def mul4(w, x, y, z):
    if IS_LEGACY:
        return w * x * y * z

    return w @ x @ y @ z


def opengl_quat_to_mat3(q):
    w = q.w
    x = q.x
    y = q.y
    z = q.z
    
    return mathutils.Matrix(
        [( 1 - 2*y*y - 2*z*z,     2*x*y + 2*w*z,     2*x*z - 2*w*y), 
         (     2*x*y - 2*w*z, 1 - 2*x*x - 2*z*z,     2*y*z + 2*w*x), 
         (     2*x*z + 2*w*y,     2*y*z - 2*w*x, 1 - 2*x*x - 2*y*y)]
    )


def convert_opengl_to_blend_mat4(x):
    return mul(OPENGL_TO_BLEND_MAT4, x)

def convert_blend_to_opengl_mat4(x):
    return mul(BLEND_TO_OPENGL_MAT4, x)

def convert_y_up_to_z_up_mat4(x):
    return mul(x, Y_UP_TO_Z_UP_MAT4)

def convert_z_up_to_y_up_mat4(x):
    return mul(x, Z_UP_TO_Y_UP_MAT4)

def convert_opengl_y_up_to_blend_z_up_mat4(x):
    return convert_y_up_to_z_up_mat4(convert_opengl_to_blend_mat4(x))

def convert_blend_z_up_to_opengl_y_up_mat4(x):
    return convert_blend_to_opengl_mat4(convert_z_up_to_y_up_mat4(x))


def convert_opengl_to_blend_quat(x):
    return mul(OPENGL_TO_BLEND_QUAT, x)

def convert_blend_to_opengl_quat(x):
    return mul(BLEND_TO_OPENGL_QUAT, x)

def convert_y_up_to_z_up_quat(x):
    return mul(x, Y_UP_TO_Z_UP_QUAT)

def convert_z_up_to_y_up_quat(x):
    return mul(x, Z_UP_TO_Y_UP_QUAT)

def convert_opengl_y_up_to_blend_z_up_quat(x):
    return convert_y_up_to_z_up_quat(convert_opengl_to_blend_quat(x))

def convert_blend_z_up_to_opengl_y_up_quat(x):
    return convert_blend_to_opengl_quat(convert_z_up_to_y_up_quat(x))


def set_bone_matrix(bone, mat):
    bone.matrix = mat
    if not IS_LEGACY and isinstance(bone, bpy.types.EditBone):
        #print("Bone align_roll: ", (mat[0][0],mat[1][0],mat[2][0]))
        bone.align_roll((mat[0][0],mat[1][0],mat[2][0]))


BL28_TO_LEGACY_ICON = {
    # Renamed in 2.80               
    'ADD'                          : 'ZOOMIN'             ,  
    'REMOVE'                       : 'ZOOMOUT'            ,  
    'FILE_NEW'                     : 'NEW'                ,  
    'SHADING_BBOX'                 : 'BBOX'               ,  
    'SHADING_TEXTURE'              : 'POTATO'             , #'TEXTURE_SHADED',  
    'SHADING_RENDERED'             : 'SMOOTH'             ,  
    'SHADING_SOLID'                : 'SOLID'              ,  
    'SHADING_WIRE'                 : 'WIRE'               ,  
    'XRAY'                         : 'ORTHO'              ,  
    'PROPERTIES'                   : 'BUTS'               ,  
    'IMAGE'                        : 'IMAGE_COL'          ,  
    'OUTLINER'                     : 'OOPS'               ,  
    'GRAPH'                        : 'IPO'                ,  
    'PREFERENCES'                  : 'SCRIPTWIN'          ,  
    'PIVOT_CURSOR'                 : 'CURSOR'             ,  
    'PIVOT_INDIVIDUAL'             : 'ROTATECOLLECTION'   ,  
    'PIVOT_MEDIAN'                 : 'ROTATECENTER'       ,  
    'PIVOT_ACTIVE'                 : 'ROTACTIVE'          ,  
    'WINDOW'                       : 'FULLSCREEN'         ,  
    'LIGHT'                        : 'LAMP'               ,  
    'LIGHT_DATA'                   : 'LAMP_DATA'          ,  
    'OUTLINER_OB_LIGHT'            : 'OUTLINER_OB_LAMP'   ,  
    'OUTLINER_DATA_LIGHT'          : 'OUTLINER_DATA_LAMP' ,  
    'LIGHT_POINT'                  : 'LAMP_POINT'         ,  
    'LIGHT_SUN'                    : 'LAMP_SUN'           ,  
    'LIGHT_SPOT'                   : 'LAMP_SPOT'          ,  
    'LIGHT_HEMI'                   : 'LAMP_HEMI'          ,  
    'LIGHT_AREA'                   : 'LAMP_AREA'          ,  
    'HIDE_OFF'                     : 'VISIBLE_IPO_ON'     ,  
    'HIDE_ON'                      : 'VISIBLE_IPO_OFF'    ,  

    # Added in 2.80
    'ALEMBIC'                      : None                 ,
    'ALIGN_BOTTOM'                 : None                 ,  
    'ALIGN_CENTER'                 : None                 ,  
    'ALIGN_FLUSH'                  : None                 ,  
    'ALIGN_JUSTIFY'                : None                 ,  
    'ALIGN_LEFT'                   : None                 ,  
    'ALIGN_MIDDLE'                 : None                 ,  
    'ALIGN_RIGHT'                  : None                 ,  
    'ALIGN_TOP'                    : None                 ,  
    'ASSET_MANAGER'                : None                 ,  
    'BOLD'                         : None                 ,  
    'DECORATE'                     : None                 ,  
    'DECORATE_ANIMATE'             : None                 ,  
    'DECORATE_DRIVER'              : None                 ,  
    'DECORATE_KEYFRAME'            : None                 ,  
    'DECORATE_LIBRARY_OVERRIDE'    : None                 ,  
    'DECORATE_LINKED'              : None                 ,  
    'DECORATE_LOCKED'              : None                 ,  
    'DECORATE_OVERRIDE'            : None                 ,  
    'DECORATE_UNLOCKED'            : None                 ,  
    'DRIVER_DISTANCE'              : None                 ,  
    'DRIVER_ROTATIONAL_DIFFERENCE' : None                 ,  
    'DRIVER_TRANSFORM'             : None                 ,  
    'DUPLICATE'                    : None                 ,  
    'FACE_MAPS'                    : None                 ,
    'FAKE_USER_OFF'                : None                 ,
    'FAKE_USER_ON'                 : None                 ,
    'GP_MULTIFRAME_EDITING'        : None                 ,
    'GP_ONLY_DSELECTED'            : None                 ,
    'GP_SELECT_POINTS'             : None                 ,
    'GP_SELECT_STROKES'            : None                 ,
    'GREASEPENCIL'                 : None                 ,
    'HEART'                        : None                 ,
    'ITALIC'                       : None                 ,
    'LIBRARY_DATA_OVERRIDE'        : None                 ,
    'LIGHTPROBE_CUBEMAP'           : None                 ,
    'LIGHTPROBE_GRID'              : None                 ,
    'LIGHTPROBE_PLANAR'            : None                 ,
    'LINE_DATA'                    : None                 ,
    'MATCLOTH'                     : None                 ,
    'MATFLUID'                     : None                 ,
    'MATSHADERBALL'                : None                 ,
    'MOD OPACITY'                  : None                 ,
    'MOD_HUE_SATURATION'           : None                 ,
    'MOD_INSTANCE'                 : None                 ,
    'MOD_NOISE'                    : None                 ,
    'MOD_OFFSET'                   : None                 ,
    'MOD_PARTICLE_INSTANCE'        : None                 ,
    'MOD_SIMPLIFY'                 : None                 ,
    'MOD_THICKNESS'                : None                 ,
    'MOD_TIME'                     : None                 ,
    'MODIFIER_OFF'                 : None                 ,
    'MODIFIER_ON'                  : None                 ,
    'MOUSE_LMB'                    : None                 ,
    'MOUSE_LMB_DRAG'               : None                 ,
    'MOUSE_MMB'                    : None                 ,
    'MOUSE_MMB_DRAG'               : None                 ,
    'MOUSE_MOVE'                   : None                 ,
    'MOUSE_RMB'                    : None                 ,
    'MOUSE_RMB_DRAG'               : None                 ,
    'NORMALS_FACE'                 : None                 ,
    'NORMALS_VERTEX'               : 'MATCAP_23'          ,
    'NORMALS_VERTEX_FACE'          : 'MATCAP_23'          ,
    'OBJECT_ORIGIN'                : None                 ,
    'ONIONSKIN_OFF'                : None                 ,
    'ONIONSKIN_ON'                 : None                 ,
    'ORIENTATION_GIMBAL'           : None                 ,
    'ORIENTATION_GLOBAL'           : None                 ,
    'ORIENTATION_LOCAL'            : None                 ,
    'ORIENTATION_NORMAL'           : None                 ,
    'ORIENTATION_VIEW'             : None                 ,
    'OUTLINER_DATA_GREASEPENCIL'   : None                 ,
    'OUTLINER_OB_IMAGE'            : None                 ,
    'OUTLINER_OB_LIGHTPROBE'       : None                 ,
    'OVERLAY'                      : None                 ,
    'PRESET'                       : None                 ,
    'PRESET_NEW'                   : None                 ,
    'SEALED'                       : None                 ,
    'SETTINGS'                     : None                 ,
    'SHADERFX'                     : None                 ,
    'SMALL_CAPS'                   : None                 ,
    'SYSTEM'                       : None                 ,
    'THREE_DOTS'                   : None                 ,
    'TOOL_SETTINGS'                : None                 ,
    'TRACKING'                     : None                 ,

    # Other
    #'ARROW_LEFTRIGHT'              : 'MAN_SCALE'         ,
    #'FILE_FOLDER'                  : 'FILESEL'           ,
    #'FILEBROWSER'                  : 'FILESEL'           ,
    #'FILE_IMAGE'                   : 'IMAGE_COL'         ,
    #'MOD_DATA_TRANSFER'            : 'RETOPO'            ,
    #'BRUSH_SOFTEN'                 : 'MATCAP_19'         ,
    #'CLIPUV_DEHLT'                 : 'MATCAP_24'         ,
    #'MESH_CIRCLE'                  : 'MATCAP_24'         ,
    #'VIS_SEL_01'                   : 'VISIBLE_IPO_OFF'   ,
    #'VIS_SEL_11'                   : 'VISIBLE_IPO_ON'    ,
    #'BRUSH_TEXFILL'                : 'MATCAP_05'         ,
    #'NODE_MATERIAL'                : 'MATCAP_05'         ,
    #'HOLDOUT_ON'                   : 'MATCAP_13'         ,
}

LEGACY_TO_BL28_ICON = {
    # Renamed in 2.80
    'ZOOMIN'                       : 'ADD'                ,  
    'ZOOMOUT'                      : 'REMOVE'             ,  
    'NEW'                          : 'FILE_NEW'           ,  
    'BBOX'                         : 'SHADING_BBOX'       ,  
    'POTATO'                       : 'SHADING_TEXTURE'    , #'TEXTURE_SHADED',  
    'SMOOTH'                       : 'SHADING_RENDERED'   ,  
    'SOLID'                        : 'SHADING_SOLID'      ,  
    'WIRE'                         : 'SHADING_WIRE'       ,  
    'ORTHO'                        : 'XRAY'               ,  
    'BUTS'                         : 'PROPERTIES'         ,  
    'IMAGE_COL'                    : 'IMAGE'              ,  
    'OOPS'                         : 'OUTLINER'           ,  
    'IPO'                          : 'GRAPH'              ,  
    'SCRIPTWIN'                    : 'PREFERENCES'        ,  
    'CURSOR'                       : 'PIVOT_CURSOR'       ,  
    'ROTATECOLLECTION'             : 'PIVOT_INDIVIDUAL'   ,  
    'ROTATECENTER'                 : 'PIVOT_MEDIAN'       ,  
    'ROTACTIVE'                    : 'PIVOT_ACTIVE'       ,  
    'FULLSCREEN'                   : 'WINDOW'             ,  
    'LAMP'                         : 'LIGHT'              ,  
    'LAMP_DATA'                    : 'LIGHT_DATA'         ,  
    'OUTLINER_OB_LAMP'             : 'OUTLINER_OB_LIGHT'  ,  
    'OUTLINER_DATA_LAMP'           : 'OUTLINER_DATA_LIGHT',  
    'LAMP_POINT'                   : 'LIGHT_POINT'        ,  
    'LAMP_SUN'                     : 'LIGHT_SUN'          ,  
    'LAMP_SPOT'                    : 'LIGHT_SPOT'         ,  
    'LAMP_HEMI'                    : 'LIGHT_HEMI'         ,  
    'LAMP_AREA'                    : 'LIGHT_AREA'         ,  
    'VISIBLE_IPO_ON'               : 'HIDE_OFF'           ,  
    'VISIBLE_IPO_OFF'              : 'HIDE_ON'            ,  
                                                          
    # Removed in 2.80              
    'LINK_AREA'                    : 'LINKED'             ,
    'PLUG'                         : 'PLUGIN'             ,
    'EDIT'                         : None                 , 
    'GAME'                         : None                 , 
    'RADIO'                        : None                 ,
    'DOTSUP'                       : 'DOT'                ,
    'DOTSDOWN'                     : 'DOT'                ,
    'LINK'                         : 'LAYER_USED'         , #(maybe use DOT, LAYER_ACTIVE or LAYER_USED)
    'INLINK'                       : None                 ,  
    'GO_LEFT'                      : None                 ,
    'TEMPERATURE'                  : None                 ,
    'SNAP_SURFACE'                 : None                 ,
    'MANIPUL'                      : None                 ,
    'BORDER_LASSO'                 : None                 ,
    'MAN_TRANS'                    : None                 ,
    'MAN_ROT'                      : None                 ,
    'MAN_SCALE'                    : None                 ,
    'RENDER_REGION'                : None                 ,
    'RECOVER_AUTO'                 : None                 ,
    'SAVE_COPY'                    : None                 ,
    'OPEN_RECENT'                  : None                 ,
    'LOAD_FACTORY'                 : None                 ,
    'ALIGN'                        : None                 ,
    'SPACE2'                       : None                 ,
    'ROTATE'                       : None                 ,
    'SAVE_AS'                      : None                 ,
    'BORDER_RECT'                  : None                 ,
}                                                          

def icon(key):
    if IS_LEGACY:
        # 対応アイコンがdictにない場合はNONEとする
        return BL28_TO_LEGACY_ICON.get(key, key) or 'NONE'
    else:
        return LEGACY_TO_BL28_ICON.get(key, key) or 'NONE'
        
    return key


def region_type():
    if IS_LEGACY:
        return 'TOOLS'

    return 'UI'


def pref_type():
    if IS_LEGACY:
        return 'USER_PREFERENCES'

    return 'PREFERENCES'


def get_prefs(context):
    if IS_LEGACY:
        return context.user_preferences

    return context.preferences


def get_system(context):
    if IS_LEGACY:
        return get_prefs(context).system

    return get_prefs(context).view


def get_tex_image(context, node_name=None):
    if IS_LEGACY:
        if hasattr(context, 'texture'):
            tex = context.texture
            if tex:
                return tex.image
    else:
        mate = context.material
        if mate and mate.use_nodes:
            node = mate.node_tree.nodes.get(node_name)
            if node and node.type == 'TEX_IMAGE':
                return node.image

    return None



BL29_TO_LEGACY_SUBTYPE = {
    # Scalar subtypes       
    #'PIXEL'           : 'PIXEL'           ,
    #'UNSIGNED'        : 'UNSIGNED'        ,
    #'PERCENTAGE'      : 'PERCENTAGE'      ,
    #'FACTOR'          : 'FACTOR'          ,
    #'ANGLE'           : 'ANGLE'           ,
    #'TIME'            : 'TIME'            ,
    #'DISTANCE'        : 'DISTANCE'        ,
    'DISTANCE_CAMERA' : 'DISTANCE'        ,
    'TEMPERATURE'     : None              ,

    # Vector subtypes
    #'COLOR'           : 'COLOR'           ,
    #'TRANSLATION'     : 'TRANSLATION'     ,
    #'DIRECTION'       : 'DIRECTION'       ,
    #'VELOCITY'        : 'VELOCITY'        ,
    #'ACCELERATION'    : 'ACCELERATION'    ,
    #'MATRIX'          : 'MATRIX'          ,
    #'EULER'           : 'EULER'           ,
    #'QUATERNION'      : 'QUATERNION'      ,
    #'AXISANGLE'       : 'AXISANGLE'       ,
    #'XYZ'             : 'XYZ'             ,
    #'COLOR_GAMMA'     : 'COLOR_GAMMA'     ,
    #'LAYER'           : 'LAYER'           ,
    'LAYER_MEMBER'    : 'LAYER'           ,
    'XYZ_LENGTH'      : 'XYZ'             ,
    'COORDINATES'     : 'XYZ'             ,
    
    # Other
    'POWER'           : None              ,
    'NONE'            : None              ,
}

BL29_TO_BL28_SUBTYPE = {
    # Scalar subtypes    
    #'PIXEL'           : 'PIXEL'           ,
    #'UNSIGNED'        : 'UNSIGNED'        ,
    #'PERCENTAGE'      : 'PERCENTAGE'      ,
    #'FACTOR'          : 'FACTOR'          ,
    #'ANGLE'           : 'ANGLE'           ,
    #'TIME'            : 'TIME'            ,
    #'DISTANCE'        : 'DISTANCE'        ,
    'DISTANCE_CAMERA' : 'DISTANCE'        ,
    'TEMPERATURE'     : None              ,

    # Vector subtypes
    #'COLOR'           : 'COLOR'           ,
    #'TRANSLATION'     : 'TRANSLATION'     ,
    #'DIRECTION'       : 'DIRECTION'       ,
    #'VELOCITY'        : 'VELOCITY'        ,
    #'ACCELERATION'    : 'ACCELERATION'    ,
    #'MATRIX'          : 'MATRIX'          ,
    #'EULER'           : 'EULER'           ,
    #'QUATERNION'      : 'QUATERNION'      ,
    #'AXISANGLE'       : 'AXISANGLE'       ,
    #'XYZ'             : 'XYZ'             ,
    #'COLOR_GAMMA'     : 'COLOR_GAMMA'     ,
    #'LAYER'           : 'LAYER'           ,
    #'LAYER_MEMBER'    : 'LAYER_MEMBER'    ,
    'XYZ_LENGTH'      : 'XYZ'             ,
    'COORDINATES'     : 'XYZ'             ,
    
    # Other
    'POWER'           : None              ,
    'NONE'            : None              ,
}

def subtype(key):
    if IS_LEGACY:
        return BL29_TO_LEGACY_SUBTYPE.get(key, key) or 'NONE'
    elif bpy.app.version < (2, 90):
        return BL29_TO_BL28_SUBTYPE.get(key, key) or 'NONE'
    return key

