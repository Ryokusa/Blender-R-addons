""" Reparent Bones
    by zoobot
    
    Set the parent of all selected bones to the active bone.
"""

import bpy

from cm3d2converter.templates.bone_functions import (
    require_armature,
    require_bone
)


# Check if there is an active armature object
armature = require_armature()

# Get the active bone
active_bone = require_bone()

# Switch to Edit Mode
pre_mode = bpy.context.mode
bpy.ops.object.mode_set(mode='EDIT')

# Parent selected bones to active bone
selected_bones = [b for b in armature.edit_bones if b.select]
for bone in selected_bones:
    bone.parent = active_bone
    
# Return to original mode
bpy.ops.object.mode_set(mode=pre_mode)
