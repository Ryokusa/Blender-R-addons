import sys
from types import ModuleType
from pathlib import Path
from typing import Dict, Tuple

import pdoc
from pdoc import doc, extract, render
from bpydoc import *


import bpy
# blender modules; must be imported after bpy
import bpy_types
import rna_info



def pdoc_bpy(module: ModuleType, out_dir: str | Path = None) -> Dict[str, Module]:
    """
    Render the documentation for all exported bpy operators.
    """
    module_dir = Path(f'{module.__file__}/../').resolve()
    if not out_dir is None:
        out_dir = Path(out_dir)
    

    # To find the module's additions, get RNA info, call register, 
    # then get RNA info again, and find what was added
    base_rna_info_list = rna_info.BuildRNAInfo()
    base_rna_info_keys = ( list(base_rna_info_list[0].keys()),  
                           list(base_rna_info_list[1].keys()), 
                           list(base_rna_info_list[2].keys()), 
                           list(base_rna_info_list[3].keys()))
    module.register()
    both_rna_info_list = rna_info.BuildRNAInfo()
    module_rna_info_list = ({}, {}, {}, {})
    for i in range(len(module_rna_info_list)):
        for k, v in both_rna_info_list[i].items():
            if k not in base_rna_info_keys[i]:
                module_rna_info_list[i][k] = v

    # Store where each struct is to easily resolve it later
    struct_modules = { }
    bpy_modules: Dict[ModuleType | str, set] = { }
    loaded_modules = { }
    bpy_ops_sub_modules = set()

    def _get_rna_base(rna_obj: bpy_types.RNAMeta | bpy_types.StructRNA):
        while (rna_obj.bl_rna.base is not None):
            rna_obj = rna_obj.bl_rna.base
        rna_base = getattr(bpy.types, rna_obj.identifier)
        return rna_base

    def _find_draw_funcs(rna_meta: bpy_types.RNAMeta):
        if not hasattr(rna_meta, 'draw') or not hasattr(rna_meta.draw, '_draw_funcs'):
            return
        draw_func_docs = set()
        for i, draw_func in enumerate(rna_meta.draw._draw_funcs):
            file_path = Path(draw_func.__code__.co_filename)
            if (file_path.is_relative_to(module_dir)):
                func_doc = doc.Function(bpy.types.__name__, 
                                        f'{rna_meta.bl_rna.identifier}.draw.draw_funcs[{i}]',
                                        draw_func,
                                        (draw_func.__module__, draw_func.__qualname__))
                draw_func_docs.add(func_doc)
        if len(draw_func_docs) > 0:
            bpyparent = BpyParent(bpy_types, rna_meta.bl_rna, (rna_meta.__module__, rna_meta.__qualname__), draw_func_docs)
            rna_base = _get_rna_base(rna_meta)
            bpy_modules.setdefault(f'{rna_base.__module__}.{rna_base.__qualname__}', set()).add(bpyparent)
            #print(bpyparent)
    
    for attr in dir(bpy.types):
        _find_draw_funcs(getattr(bpy.types, attr))


    def _get_sub_module(module_name):
        return loaded_modules.setdefault(f'bpy.ops.{module_name}', getattr(bpy.ops, module_name))
    
    def _get_parent(child_key) -> Tuple[Tuple[str, str], InfoMemberRNA, ModuleType]:
        parent_key = ('', child_key[0])
        parent = None
        if parent_key in both_rna_info_list[0].keys():
            parent = both_rna_info_list[0][parent_key]
            parent_module = bpy.types
        elif parent_key in both_rna_info_list[2].keys():
            parent = both_rna_info_list[2][parent_key]
            parent_module = _get_sub_module(parent.module_name)
        return parent_key, parent, parent_module

    def _get_bpyparent(parent: InfoMemberRNA, parent_module) -> BpyParent:
        for rna_mamber_info in bpy_modules.setdefault(parent_module, set()):
            if isinstance(rna_mamber_info, BpyParent) and rna_mamber_info.rna_struct is parent:
                return rna_mamber_info
        else: # if loop doesn't terminate
            bpyparent = BpyParent(parent_module, parent, ignore_rna_info_keys=base_rna_info_keys)
            bpy_modules[parent_module].add(bpyparent)
            return bpyparent

    def _set_parent(child_key, child_info):
        parent_key, parent, parent_module = _get_parent(child_key)
        if parent is None:
            print(f"Could not find parent for InfoFunctionRNA[{key}] = {func_info}; assuming bpy.types")
            bpy_modules[parent_module].add(child_info)
        elif parent_key not in base_rna_info_keys[0] and parent_key not in base_rna_info_keys[2]:
            # It's parent is part of the target module
            # wait until later to add it
            #print(f"Parent '{parent_key}' of child '{child_key}' is part of the target module")
            pass
        else:
            bpyparent = _get_bpyparent(parent, parent_module)
            bpyparent.rna_member_info.add(child_info)
            print(f"Got bpyparent {bpyparent}")


    for key, func_info in module_rna_info_list[1].items():
        _set_parent(key, func_info)
    for key, prop_info in module_rna_info_list[3].items():
        _set_parent(key, prop_info)
    for struct_info in module_rna_info_list[0].values():
        bpy_modules.setdefault(bpy.types, set()).add(struct_info)
        struct_modules[struct_info.identifier] = bpy.types
        _find_draw_funcs(struct_info)
    for op_info in module_rna_info_list[2].values():
        sub_module = _get_sub_module(op_info.module_name)
        bpy_modules.setdefault(sub_module, set()).add(op_info)
        bpy_ops_sub_modules.add(sub_module)
        struct_modules[op_info.identifier] = sub_module


    all_modules = {}
    for bpy_module, rna_members in bpy_modules.items():
        if isinstance(bpy_module, ModuleType):
            pdoc_module = BpyModule(bpy_module, rna_members)
        else:
            pdoc_module = BpyNamespace(str(bpy_module), rna_members)
        all_modules[pdoc_module.fullname] = pdoc_module
        #print(f'all_modules[{bpy_module.__name__}] = {pdoc_module}')
    
    # handle bpy.ops
    bpy_ops_sub_module_docs = [all_modules[sub_module.__name__] for sub_module in bpy_ops_sub_modules]
    all_modules[bpy.ops.__name__] = BpyModule(bpy.ops, bpy_ops_sub_module_docs)

    #for sub_module in bpy_ops_sub_modules:
    #    all_modules.pop(sub_module.__name__)
    
    bpy_ops_sub_module_doc_names = [module_doc.name for module_doc in bpy_ops_sub_module_docs]
    #print(bpy_ops_sub_module_doc_names)

    return all_modules


def pdoc_blender_add_on(module: ModuleType, out_dir: Path | str):

    all_modules: dict[str, doc.Module] = {}

    source_doc = doc.Module(module)
    
    api_docs = pdoc_bpy(module)
    all_modules.update(api_docs.items())  

    module_dir = Path(f'{module.__file__}/../').resolve()
    main_modules = {}
    for module_name in extract.walk_specs([str(module_dir)]):
        main_modules[module_name] = doc.Module.from_name(module_name)  

    all_modules.update(main_modules)

    out_dir = Path(out_dir)
    for pdoc_module in all_modules.values():
        out = render.html_module(pdoc_module, all_modules)
        if not out_dir:
            return out
        else:
            outfile = out_dir / f"{pdoc_module.fullname.replace('.', '/')}.html"
            outfile.parent.mkdir(parents=True, exist_ok=True)
            outfile.write_bytes(out.encode())
    
    print(all_modules.keys())

    index_names = {
        'bpy_types.Header': 'Headers'      ,
        'bpy_types.Panel' : 'Panels'       ,
        'bpy_types.Menu'  : 'Menus'        ,
        'bpy.ops'         : 'Operators'    ,
        'bpy.types'       : 'Types'        ,
        module.__name__   : module.__name__,
    }
    index_modules = { k: all_modules[k] for k in index_names }

    for submodule in all_modules.values():
        if submodule in index_modules.values():
            continue
        for index_module in index_modules.values():
            if submodule in index_module.submodules:
                break
        else: # if loop did not break
            if submodule not in main_modules.values():
                print(f"WARN: Unreferenced submodule '{submodule.fullname}'")
    index = render.html_index(index_modules)
    if index:
        for old_name, new_name in index_names.items():
            index = index.replace(old_name, new_name)
        (out_dir / "index.html").write_bytes(index.encode())

    search = render.search_index(all_modules)
    if search:
        (out_dir / "search.js").write_bytes(search.encode())


def main():
    modules_path = Path(f'{__file__}/../../').resolve()
    sys.path.append(str(modules_path)) # Make it possible to find "../CM3D2 Converter"
    br_addon = __import__("BR Addon")
    pdoc_blender_add_on(br_addon, 'docs/build')

if __name__ == '__main__':
    main()