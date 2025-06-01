import bpy
import bpy.ops
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper


# filter collada


def import_dae(filepath):
    name = bpy.path.display_name_from_filepath(filepath)
    view_layer = bpy.context.view_layer
    # create collection from name of model and select
    
    # import DAE into selected collection
    bpy.ops.wm.collada_import(filepath=filepath, display_type='DEFAULT')
    if 'rig' in bpy.data.objects: # change this to look for rig in just that collection
        rig = bpy.data.objects['rig']
        rig.name = f'{name}_rig'
        # by default adding model leaves names ModelName and ModelName_glass
        # this means that upon import, ModelName will always come first
        model = rig.children[0]
        # at this point the index for model will likely change relative to glass name
        model.name = name
        view_layer.objects.active = model
        model.active_material.name = f'{name}_material'
        # check for glass
        if len(rig.children) > 1:
            print("multiple children found")
            print([child.name for child in rig.children])
            for child in rig.children:
                if child.name[-5:] == 'glass':
                    print(f'found child: {child.name}')
                    glass_specular(child, name)
        # if rig.children[1].name[-5:] == 'glass':
        #     print("found child!")
        #     view_layer.objects.active = rig.children[1]
        #     glass_specular(name)
    if 'Lamp' in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects['Lamp'])
    return {'FINISHED'}

def merge_vertices():
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=True, use_sharp_edge_from_normals=True)
    bpy.ops.object.editmode_toggle()
    print('merge_vertices()')

def glass_specular(glass, name):
    print(f'glass_specular({name})')
    glass = glass
    glass.name = f'{name}_glass'
    print(f'active object: {glass.name}')
    material = glass.active_material
    material.name = f'{glass.name}_material'
    tree = material.node_tree
    nodes = tree.nodes
    bsdf = nodes.get("Principled BSDF")
    base_color_alpha_input = bsdf.inputs["Alpha"]
    base_color_node = nodes.get("Image Texture")
    base_color_alpha_output = base_color_node.outputs["Alpha"]
    tree.links.new(base_color_alpha_input, base_color_alpha_output)
    spec_input = bsdf.inputs["Specular IOR Level"]
    spec_tex = nodes.get("Image Texture.001")
    spec_output = spec_tex.outputs["Alpha"]
    tree.links.new(spec_input, spec_output)

def specular(filepath):
    model = bpy.context.view_layer.objects.active
    material = model.active_material
    tree = material.node_tree
    nodes = material.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    spec_input = bsdf.inputs["Specular IOR Level"]
    spec_tex = nodes.get("Image Texture.001")
    spec_output = spec_tex.outputs["Alpha"]
    tree.links.new(spec_input, spec_output)
    # create and attach normal map node to bsdf normal input
    bsdf_input_normal = bsdf.inputs["Normal"]
    normal_map_node = nodes.new("ShaderNodeNormalMap")
    normal_map_output = normal_map_node.outputs["Normal"]
    normal_map_input = normal_map_node.inputs["Color"]
    tree.links.new(bsdf_input_normal, normal_map_output)
    # create and attach mapping node to normal map node
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (2, 2, 2)
    mapping_output = mapping.outputs["Vector"]
    mapping_input = mapping.inputs["Vector"]
    tree.links.new(normal_map_input, mapping_output)
    # create and attach image texture node
    normal_tex = nodes.new("ShaderNodeTexImage")
    normal_tex_output = normal_tex.outputs["Color"]
    tree.links.new(mapping_input, normal_tex_output)
    # open image
    print(f'filepath: {filepath}')
    clean_model_name = model.name.replace(' ', '_')
    length = 4 + len(model.name)
    # convert spaces to _
    normal_path = f'{filepath[:-length]}{clean_model_name}_normalmap.png'
    print(f'normal path: {normal_path}')
    filename = f'{clean_model_name}_normalmap.png'
    print(f'filename: {filename}')
    dir_path = filepath[:-len(f'{model.name}.dae')]
    print(f'dir_path = {dir_path}')
    relpath = bpy.path.relpath(normal_path)
    print(f'relpath: {relpath}')
    bpy.ops.image.open(filepath=relpath, directory=dir_path, files=[{"name":filename, "name":filename}], show_multiview=False)
    # set image
    normal_tex.image = bpy.data.images.get(filename)





def normal():
    pass

def subsurf():
    print('subsurf()')

def import_model(context, filepath):
    import_dae(filepath)
    merge_vertices()
    specular(filepath)
    return {'FINISHED'}
    

class ImportModel(Operator, ImportHelper):
    bl_idname = 'import_test.import_model'
    bl_label = 'Import DAE'

    filename_ext = '.dae'

    filter_glob: StringProperty(
        default='*.dae',
        options={'HIDDEN'},
        maxLen=255
    )

    def execute(self, context):
        return import_model(context, self.filepath)

def register():
    bpy.utils.register_class(ImportModel)

def unregister():
    bpy.utils.unregister_class(ImportModel)




if __name__ == "__main__":
    register()
    bpy.ops.import_test.import_model('INVOKE_DEFAULT')