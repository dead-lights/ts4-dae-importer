import bpy
import bpy.ops
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector

# !!!! https://docs.blender.org/api/current/bpy.types.FileHandler.html read here


# I need to check for duplicates when renaming things - it seems to be causing some issues
# to do:
	# remove the light that gets imported
	# add subsurf modifier
	# attach emission map
def import_dae(filepath):
	name = bpy.path.display_name_from_filepath(filepath)
	view_layer = bpy.context.view_layer
	print(f'Importing {name}...')
	# import collada, brings up file select
	bpy.ops.wm.collada_import(filepath=filepath, display_type='DEFAULT', filter_collada=True)
	# rig is active object now after import
	rig = view_layer.objects.active
	rig.name = f'{name}_rig'
	# upon import the main model is automatically at rig.children[0] and glass is at rig.children[1]
	# this order will change when you rename the main model
	model = rig.children[0]
	# check for glass, do this before renaming main model so it's still alphabetical
	if len(rig.children) > 1:
		glass = rig.children[1]
		print(f'glass identified: {glass.name}') # for testing
		# remove merge=False later when I clean up
		config_object(glass, f'{name}_glass')
		config_shaders(glass, has_normal=False, has_alpha=True)
		glass.select_set(False)
	config_object(model, name)
	config_shaders(model, filepath=filepath, name=name)
	# merge_vertices does approx the same thing as TS4SimRipper's clean mesh function, but i prefer to handle that in Blender
	# you can delete this line if you don't want to use it
	merge_vertices(model)
	

def arrange_nodes(tree):
	nodes = tree.nodes
	print([f'{node.name} | location: ({node.location.x}, {node.location.y}); width: {node.width}; height: {node.height}' for node in nodes])
	# reference nodes
	bsdf = nodes.get('Principled BSDF')
	mat_output = nodes.get('Material Output')
	color = nodes.get('Image Texture')
	spec = nodes.get('Image Texture.001')
	ambient = nodes.get('RGB')
	spacing = bsdf.location.x - color.location.x + color.width
	# move ambient below material output
	ambient.location.x = mat_output.location.x
	ambient.location.y = mat_output.location.y - 175
	# Image Texture.002 is how normal maps import - glass does not have normal
	if 'Image Texture.002' in nodes:
		normal = nodes.get('Image Texture.002')
		mapping = nodes.get('Mapping')
		normal_map = nodes.get('Normal Map')
		# move normal map underneath base color
		normal_map.location.x = color.location.x + color.width/2 - normal_map.width/2
		normal_map.location.y = color.location.y - 325
		# move mapping to the left of base color level with normal map
		mapping.location.x = color.location.x - (mapping.width+25)
		mapping.location.y = normal_map.location.y
		# move normal to the left of mapping at the same y
		normal.location.x = mapping.location.x - (normal.width+25)
		normal.location.y = mapping.location.y
		spec.location.y = normal_map.location.y - 200
	# when there's no normal map like with glass move specular closer to base color
	else:
		spec.location.x = color.location.x
		spec.location.y = color.location.y - 300


# renames object and material
def config_object(model, name):
	model.name = name
	model.active_material.name = f'{name}_material'


def merge_vertices(model):
	bpy.context.view_layer.objects.active = model
	bpy.ops.object.editmode_toggle()
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=False, use_sharp_edge_from_normals=True)
	bpy.ops.object.editmode_toggle()
	print('merge_vertices()')


# has_specular=True for both base model and glass
# has_normal=True for only base model
# has_alpha=True only for glass
def config_shaders(model, has_specular=True, has_normal=True, has_alpha=False, filepath='', name=''):
	tree = model.active_material.node_tree
	if has_specular:
		config_specular(tree)
	if has_normal:
		config_normal(tree, filepath, name)
	if has_alpha:
		config_alpha(tree)
	arrange_nodes(tree)


# specular texture node exists but is not attached to the rest of the tree
def config_specular(tree):
	nodes = tree.nodes
	bsdf = nodes.get('Principled BSDF')
	specular_tex_node = nodes.get("Image Texture.001")
	specular_output = specular_tex_node.outputs["Alpha"]
	tree.links.new(bsdf.inputs['Specular IOR Level'], specular_output)


# normal does not automatically end up on tree, must create normal map, vector mapping, and image texture nodes
def config_normal(tree, filepath, name):
	nodes = tree.nodes
	bsdf = nodes.get('Principled BSDF')
	# create normal map node and attach to BSDF's Normal input
	normal_map = nodes.new('ShaderNodeNormalMap')
	tree.links.new(bsdf.inputs['Normal'], normal_map.outputs['Normal'])
	# create vector mapping node and attach to normal_map
	# mapping required because TS4 imports normal maps at 50% the height/width of base texture
	mapping = nodes.new('ShaderNodeMapping')
	mapping.inputs['Scale'].default_value = (2, 2, 2)
	tree.links.new(normal_map.inputs['Color'], mapping.outputs['Vector'])
	# create and attach image texture node
	normal_texture = nodes.new ('ShaderNodeTexImage')
	tree.links.new(mapping.inputs["Vector"], normal_texture.outputs['Color'])
	# open image from file
	# need to clean name because TSR exports textures with ' ' turned to '_'
	clean_name = name.replace(' ', '_')
	# len('.png') and len('.dae') = 4; this gives the length of ModelName.dae so I can grab just the filename
	# so I can get ModelName_normalmap.png from the filepath - that's the naming convention
	length = 4 + len(name) 
	# there is definitely a cleaner way to handle this, but meh it works it's just a bit sloppy
	normal_path = f'{filepath[:-length]}{clean_name}_normalmap.png'
	filename = f'{clean_name}_normalmap.png'
	dir_path = filepath[:-len(f'{name}.dae')]
	relpath = bpy.path.relpath(normal_path)
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