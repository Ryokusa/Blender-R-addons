""" Batch Shape Key Transfer
    by luvoid
    
    Transfers shape keys from active mesh to all other selected meshes.
    
    This script uses the `bpy.ops.object.precision_shape_key_transfer` operator.
    See details of this and related operators in the CM3D2 Converter Docs:
        https://luvoid.github.io/Blender-CM3D2-Converter/bpy/ops/object.html#precision_shape_key_transfer
    Translated:
        https://luvoid-github-io.translate.goog/Blender-CM3D2-Converter/bpy/ops/object.html?_x_tr_sl=auto&_x_tr_tl=default#precision_shape_key_transfer
"""
import bpy

def batch_shape_key_transfer():
    """Transfer shape keys from active mesh to all other selected meshes."""

    # Check if there's an active object and if there are other selected objects
    if bpy.context.active_object and bpy.context.selected_objects:
        source_object = bpy.context.active_object
        selected_objects = list(bpy.context.selected_objects)

        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        # Select the active object
        source_object.select_set(True)

        # Loop through all selected objects except the active one
        for obj in selected_objects:
            if obj is source_object:
                continue
            # Set the current object as the active object
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            # Transfer shape keys from active object to the current object
            bpy.ops.object.precision_shape_key_transfer()

            # Deselect the current object after the transfer
            obj.select_set(False)

        # Restore the original active object and its selection state
        source_object.select_set(True)
        bpy.context.view_layer.objects.active = source_object


if __name__ == '__main__':
    # Call the function to transfer shape keys
    batch_shape_key_transfer()
