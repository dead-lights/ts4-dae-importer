import bpy
import bpy.ops
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper


# after importing collada, the active object is the rig
def import_dae(filepath):
	name = bpy.path.display_name_from_filepath(filepath)
	view_layer = bpy.context.view_layer
	print(f'Importing {name}...')
	# import collada
	bpy.ops.wm.collada_import(filepath=filepath, display_type='DEFAULT')
	# rig is active object now after import
	rig = view_layer.objects.active
	rig.name = f'{name}_rig'
	# upon import the main model is automatically at [0] and glass is at [1]
	# this will change when you rename the main model
	model = rig.children[0]
	# check for glass, do this before renaming main model so it's still alphabetical
	if len(rig.children) > 1:
		glass = rig.children[1]
		print(f'glass identified: {glass.name}')
		config_object(glass, f'{name}_glass', merge=False)
		config_shaders(glass, has_normal=False, has_alpha=True)
	config_object(model, name, merge=True)
	config_shaders(model, filepath=filepath, name=name)
	# not sure if I need to go back to this being active but I'll leave it for now
	view_layer.objects.active = rig


# renames object and material
def config_object(model, name, merge=False):
	model.name = name
	model.active_material.name = f'{name}_material'
	if merge:
		merge_vertices(model)


# this seems mostly workable as is but it does require changing the active object
def merge_vertices(model):
	bpy.context.view_layer.objects.active = model
	bpy.ops.object.editmode_toggle()
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=True, use_sharp_edge_from_normals=True)
	bpy.ops.object.editmode_toggle()
	print('merge_vertices()')


# this should work with or without glass
def config_shaders(model, has_specular=True, has_normal=True, has_alpha=False, filepath='', name=''):
	tree = model.active_material.node_tree
	if has_specular:
		config_specular(tree)
	if has_normal:
		config_normal(tree, filepath, name)
	if has_alpha:
		config_alpha(tree)


# specular texture node exists but is not attached to the rest of the tree
def config_specular(tree):
	nodes = tree.nodes
	bsdf = nodes.get('Principled BSDF')
	specular_tex_node = nodes.get("Image Texture.001")
	specular_output = specular_tex_node.outputs["Alpha"]
	tree.links.new(bsdf.inputs['Specular IOR Level'], specular_output)


# normal does not automatically end up on tree, must create nodes
def config_normal(tree, filepath, name):
	nodes = tree.nodes
	bsdf = nodes.get('Principled BSDF')
	# create normal map node and attach to BSDF
	normal_map = nodes.new('ShaderNodeNormalMap')
	tree.links.new(bsdf.inputs['Normal'], normal_map.outputs['Normal'])
	# create vector mapping node and attach to normal_map
	mapping = nodes.new('ShaderNodeMapping')
	mapping.inputs['Scale'].default_value = (2, 2, 2)
	tree.links.new(normal_map.inputs['Color'], mapping.outputs['Vector'])
	# create and attach image texture node
	normal_texture = nodes.new ('ShaderNodeTexImage')
	tree.links.new(mapping.inputs["Vector"], normal_texture.outputs['Color'])
	# open image
	clean_name = name.replace(' ', '_')
	length = 4 + len(name) # for .dae/.png
	normal_path = f'{filepath[:-length]}{clean_name}_normalmap.png'
	print(f'normal path: {normal_path}')
	filename = f'{clean_name}_normalmap.png'
	print(f'filename: {filename}')
	dir_path = filepath[:-len(f'{name}.dae')]
	print(f'dir_path = {dir_path}')
	relpath = bpy.path.relpath(normal_path)
	print(f'relpath: {relpath}')
	bpy.ops.image.open(filepath=relpath, directory=dir_path, files=[{"name":filename, "name":filename}], show_multiview=False)
	# set image
	normal_texture.image = bpy.data.images.get(filename)


# for use only when glass layer is present
def config_alpha(tree):
	nodes = tree.nodes
	bsdf = nodes.get('Principled BSDF')
	base_color_node = nodes.get('Image Texture')
	tree.links.new(bsdf.inputs['Alpha'], base_color_node.outputs['Alpha'])


def import_model(context, filepath):
	import_dae(filepath)
	return {'FINISHED'}


# sets up the script to run in this environment
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


# run program!
if __name__ == "__main__":
	register()
	bpy.ops.import_test.import_model('INVOKE_DEFAULT')