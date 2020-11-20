# 「UV/画像エディター」エリア → ヘッダー
from . import common


# メニュー等に項目追加
def menu_func(self, context):
    img = getattr(context, 'edit_image')
    if img and 'cm3d2_path' in img:
        self.layout.label(text="For CM3D2: Internal Path", icon_value=common.kiss_icon())
        row = self.layout.row()
        row.prop(img, '["cm3d2_path"]', text="")
        row.scale_x = 3.0
