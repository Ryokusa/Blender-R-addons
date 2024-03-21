""" Convert to CM3D2 Hair
    by zoobot & luvoid
    
    Renames all the bones in the active armature to conform to 
    cm3d2 hair naming conventions. The active bone will be used as the root
    for all yure bones.
"""
import bpy
from bpy.types import Object, Armature, Bone

from cm3d2converter.templates.bone_functions import (
    require_armature_object,
    require_armature,
    require_bone,
    find_bones,
    rename_bone_descendants,
    remove_extra_bones,
    get_deform_bones,
    ALPHABET,
)


def main():
    """This is the first function that runs when the script is executed"""

    # This is a list of bones that shouldn't be deleted or modified
    keep_bones_names = [
        'Hair',
    ]
    armature_object = require_armature_object()
    yure_root = require_bone(armature_object.data)
    convert_to_cm3d2_hair(armature_object, yure_root, keep_bones_names)


def convert_to_cm3d2_hair(armature_object: Object, yure_root: Bone = None,
                          keep_bone_names: list[str] = None):
    """Rename all the bones in an armature to conform to cm3d2 hair conventions.
    
    If yure_root is specified, will make that bone's descendants yure bones.
    """
    if keep_bone_names is None:
        keep_bone_names = []
    else:
        keep_bone_names = keep_bone_names.copy()
    armature = require_armature(armature_object)

    # Get bones that deform a mesh
    deform_bones = get_deform_bones(armature_object)

    # Preserve the base bone
    base_bone_name = None
    if 'BaseBone' in bpy.context.active_object.data:
        base_bone_name = bpy.context.active_object.data['BaseBone']
        keep_bone_names.append(base_bone_name)

    keep_bones = find_bones(armature, keep_bone_names)

    # Delete unnecessary bones
    remove_extra_bones(armature, keep_bones + deform_bones)

    # Rename all the bones
    rename_bones_as_hair(armature, deform_bones)
    if yure_root:
        rename_bones_as_yure_hair(yure_root)


def rename_bones_as_hair(armature: Armature, deform_bones=None):
    """Rename bones in the active armature to hair_# bones.
    
    If a `deform_bones` is specified, that will be used to help
    decide which bones to rename.
    """

    def get_next_root_name():
        root_name = "Hair_A"
        for i in range(len(armature.bones)):
            letter = ALPHABET[i % len(ALPHABET)].lower()
            letter *= (i // len(ALPHABET)) + 1
            root_name = "Hair_" + letter
            if not armature.bones.find(root_name):
                break
        return root_name

    # Loop over root bones
    for bone in armature.bones:
        if bone.parent:
            continue
        if (deform_bones and bone in deform_bones) or bone.children:
            if not bone.name.lower().startswith("hair_"):
                bone.name = get_next_root_name()
            tree_name = bone.name[len("hair_"):]
            rename_bone_descendants(
                bone = bone,
                prefix = "hair_" + tree_name
            )


def rename_bones_as_yure_hair(yure_root: Bone):
    """Renames the selected bone and all it's descendants
    to be '_yure_hair_#' bones
        
    If a bone has no children, and is not a deforming bone,
    it will be renamed to 'hair_#_nub' instead.
    """
    if not isinstance(yure_root, Bone):
        raise TypeError("Expected argument 'yure_root' to be a Bone, " +
                        f"but got {type(yure_root)}")

    tree_name = yure_root.name
    if tree_name.lower().startswith('hair_'):
        tree_name = tree_name[len('hair_'):]
    depth = 0
    if yure_root.parent:
        try:
            int(yure_root.name[-3])
            int(yure_root.name[-2])
            end = yure_root.name[-1]
            depth = ALPHABET.index(yure_root.name[-1].upper()) + 1
            tree_name = tree_name[:-1]
        except:
            pass

    rename_bone_descendants(
        bone         = yure_root,
        prefix       = f"_yure_hair_{tree_name}",
        nub_prefix   = f"hair_{tree_name}",
        depth        = depth
    )


if __name__ == '__main__':
    # When the script is run, call main()
    main()
