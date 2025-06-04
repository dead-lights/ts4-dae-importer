import bpy
import bpy.ops
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper


# I need to check for duplicates when renaming things - it seems to be causing some issues 
def import_dae(filepath):
	name = bpy.path.display_name_from_filepath(filepath)
	view_layer = bpy.context.view_layer
	print(f'Importing {name}...')
	# import collada
	bpy.ops.wm.collada_import(filepath=filepath, display_type='DEFAULT')
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
		config_object(glass, f'{name}_glass', merge=False)
		config_shaders(glass, has_normal=False, has_alpha=True)
	config_object(model, name, merge=True)
	config_shaders(model, filepath=filepath, name=name)
	# merging vertices after adding shaders didn't do anything to Adelyn Fay's default model
	# I'm still going to run the script after configuring shaders tho - it seems like good practice
	merge_vertices(model)
	# this is where I should add the subsurf modifier
	# I think I want to start it at 0,0 but I might set it to 0,1
	# when I get the UI in place I'll let the user decide if/how to use subsurf mods
	
	# not sure if I need to go back to this being active but I'll leave it for now
	view_layer.objects.active = rig


# renames object and material
def config_object(model, name, merge=False):
	model.name = name
	model.active_material.name = f'{name}_material'
	# I'm going to try commenting this out and running merge_vertices in import_dae
		# had no effect on Adelyn Fay but it seems best practice to run this after the shader config
	# if merge:
	# 	merge_vertices(model)


'''this seems mostly workable as is but it does require changing the active object
unsure if I should be using this, relying on TS4SimRipper to clean up the mesh, or both
when I ran this on a Bella model after having TSR remove doubles, it didn't remove any vertices
which makes it seem like it's a workable solution
but when I ran it on Caleb, he had 1000+ vertices removed, lower than normal but still not ideal
then again, Caleb's model is extremely broken, so it's not great to draw conclusions from him
i did still need to remove the vertex on the inside of the head to fix the mesh when I added subsurf modifier
i'd love to eliminate that step because I don't think I can do it automatically, just manually
'''
def merge_vertices(model):
	bpy.context.view_layer.objects.active = model
	bpy.ops.object.editmode_toggle()
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=True, use_sharp_edge_from_normals=True)
	bpy.ops.object.editmode_toggle()
	print('merge_vertices()')


# has_specular=True for both base model and glass
# has_normal=True for only base model
# has_alpha=True only for glass
def config_shaders(model, has_specular=True, has_normal=True, has_alpha=False, filepath='', name=''):
	tree = model.active_material.node_tree
	if has_specular:
		config_specular(tree)
	# only base though I do need to see if glass is supposed to use the same normal map as the base
	# I don't think so but it's worth checking
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
	print(f'normal path: {normal_path}') # for testing
	filename = f'{clean_name}_normalmap.png'
	print(f'filename: {filename}') # for testing
	dir_path = filepath[:-len(f'{name}.dae')]
	print(f'dir_path = {dir_path}') # for testing
	relpath = bpy.path.relpath(normal_path)
	print(f'relpath: {relpath}') # for testing
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