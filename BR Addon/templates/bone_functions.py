""" Bone Functions
    by luvoid

    This script defines various helper functions for working with bones.
    You can reference these functions in other scripts by importing them.
    ```
    from cm3d2converter.templates.bone_functions import (
        require_armature,
        find_bones
    )
    
    armature = require_armature()
    bones = find_bones(armature, ['Bip01', 'Bip01 Spine'])
    print(bones)
    ```
    
    You can also use freely experiment inside the main() function.
    
    NOTE: Changes you make to this in the text editor won't take effect
    when importing into other scripts, because this only a copy of the template.
"""
import bpy
from bpy.types import Object, Armature, Bone

from typing import Iterable

def main():
    """This is the first function that runs when the script is executed"""
    armature = require_armature()
    bones = find_bones(armature, ['Bip01', 'Bip01 Spine'])
    print(bones)


def require_armature_object() -> Object:
    """Require the active object to be an armature, and return it.

    Raises:
        RuntimeError: If the active object is not an armature.

    Returns:
        Object: The active armature object.
    """

    # Get the active object
    obj = bpy.context.active_object

    # Get the active armature
    if obj is None or obj.type != 'ARMATURE':
        raise RuntimeError("Please selecet an armature as the active object")

    return obj


def require_armature(obj: Object = ...) -> Armature:
    """Require the active object to be an armature, and return it.

    Args:
        obj (Object, optional): The object to get the armature from.
        Defaults to `require_armature()`.
    
    Raises:
        TypeError: If the argument passed is not an Object.
        ValueError: If the object passed is not an ARMATURE.
        RuntimeError: If no object passed and active object is not an armature.

    Returns:
        Armature: The active armature
    """

    if obj is ...:
        obj = require_armature_object()

    if obj is None:
        raise TypeError(f"Expected argument of type Object, got {type(obj)}")

    if not obj.type == 'ARMATURE':
        raise ValueError("Expected Object to be an 'ARMATURE', " +
                         f"but got Object.type == '{obj.type}'")

    return obj.data


def require_bone(armature: Armature = ...) -> Bone:
    """Require an active bone from the armature. If no armature is specified,
    requires the active object to be an armature.
    
    If no armature is specified, gets the bone from `bpy.context.active_bone`

    Args:
        armature (Armature, optional): The armature to get the active bone from.

    Raises:
        TypeError: If the argument passed is not an armature.
        RuntimeError: If there is no active bone.

    Returns:
        Bone: The active bone
    """
    if armature is None:
        raise TypeError("Expected argument of type Armature, " +
                        f"got {type(armature)}")

    if armature is not ...:
        bone = armature.bones.active
    else:
        bone = bpy.context.active_bone

    if bone is None:
        raise RuntimeError("Please select a bone")

    return bone


def find_bones(armature: Armature, names: Iterable[str]) -> list[Bone]:
    """Find bones in the armature by name

    Args:
        armature (Armature): The armature in which to find the bones.
        names (Iterable[str]): A iterable of the bone names to find.

    Raises:
        TypeError: If an argument of incorrect type was provided.
    
    Returns:
        list[Bone]: A list of all the bones that were found.
    """
    if not isinstance(armature, Armature):
        raise TypeError("Expected argument 'armature' to be an Armature," +
                        f"but got {type(armature)}")
    bone_list = []
    for name in names:
        if not isinstance(name, str):
            raise TypeError("Expected elements of 'names' to be str, " +
                            f"but got {type(name)}")
        bone = armature.bones.get(name)
        if bone is not None:
            bone_list.append(bone)
    return bone_list


ALPHABET = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
            'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
def rename_bone_descendants(bone: Bone, prefix, nub_prefix=None, depth=0):
    """Rename the bone's descendants folloing CM3D2 hair naming conventions.

    If a deform_list is specified:
    If a bone has no children, and it's name is not in deform_list,
    it will be renamed as a nub bone instead.
    """
    # This is a recursive function
    if nub_prefix is None:
        nub_prefix = prefix

    children = bone.children
    if not children:
        return

    letter = ALPHABET[depth % len(ALPHABET)].lower()
    letter *= (depth // len(ALPHABET)) + 1

    if len(children) == 1:
        child = children[0]
        if child.children:
            child.name = prefix + letter
            rename_bone_descendants(child, prefix, nub_prefix, depth+1)
        else:  # It is a nub
            child.name = nub_prefix + 'nub'

        return

    # else
    for i, child in enumerate(bone.children):
        new_prefix = f"{prefix}{i+1:02}"
        new_nub_prefix = f"{nub_prefix}{i+1:02}"
        child.name = new_prefix + letter
        rename_bone_descendants(child, new_prefix, new_nub_prefix, depth+1)

    return


def remove_extra_bones(armature: Armature, ignore_bones):
    """Remove extra bones from the active armature"""

    def try_remove_recursive(bone: bpy.types.Bone):
        """Check if the bone should be deleted"""

        # Keep if any children are kept
        remove = True
        for child in list(bone.children):
            if not try_remove_recursive(child):
                remove = False
        if not remove:
            return False

        # Keep ignored bones
        if bone in ignore_bones:
            return False

        # Keep nub bones
        if (bone.parent
            and bone.parent in ignore_bones
            and len(bone.parent.children) == 1):
            return False

        # else
        armature.edit_bones.remove()
        return True

    # Loop through all bones in the armature and get root bones
    root_bones = []
    for bone in armature.edit_bones:
        if not bone.parent:
            root_bones.append(bone)

    # Loop through all root bones and remove unneeded bones
    for bone in root_bones:
        try_remove_recursive(bone)


def get_deform_bones(armature_object: Object) -> list[Bone]:
    """Searches the armature's users and detects which bones deform meshes.
    
    This works by finding bones that match vertex groups in a meshes
    that use this armature.
    """
    if not isinstance(armature_object, Object):
        raise TypeError("Expected 'armature_object' to be an Object, " +
                        f"but got {type(armature_object)}")

    user_map = bpy.data.user_map(subset=[armature_object], 
                                 value_types={'OBJECT'})
    users: set[Object] = user_map[armature_object]

    vertex_group_names = set()
    for user in users:
        if user.type == 'MESH':
            for group in user.vertex_groups:
                vertex_group_names.add(group.name)

    return find_bones(armature_object.data, vertex_group_names)


if __name__ == '__main__':
    # When the script is run, call main()
    main()
