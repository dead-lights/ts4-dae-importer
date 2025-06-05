import bpy
from mathutils import Vector


def main(context):
    model = context.view_layer.objects.active
    tree = model.active_material.node_tree
    nodes = tree.nodes
    # declare nodes
    bsdf = nodes.get('Principled BSDF')
    mat_output = nodes.get('Material Output')
    base_color = nodes.get('Image Texture')
    ambient = nodes.get('RGB')
    specular = nodes.get('Image Texture.001')
    # this part works
    ambient_x = mat_output.location[0]
    ambient_y = mat_output.location[1] - mat_output.dimensions[1]
    ambient.location = (ambient_x, ambient_y)

    if 'Image Texture.002' in nodes:
        y_gap = base_color.location[1] - (base_color.dimensions[1] + specular.dimensions[1])
        normal_map = nodes.get('Normal Map')
        normal_map_x = base_color.location[0] + (base_color.dimensions[0]/2) - (normal_map.dimensions[0]/2)
        normal_map_y = base_color.location[1] - base_color.dimensions[1]
        normal_map.location = (normal_map_x, normal_map_y)

        mapping = nodes.get('Mapping')
        mapping.location[0] = base_color.location[0] - mapping.dimensions[0]
        mapping.location[1] = normal_map.location[1]

        normal = nodes.get('Image Texture.002')
        normal.location[0] = mapping.location[0] - normal.dimensions[0]
        normal.location[1] = normal_map.location[1]

    else:
        specular.location[0] = base_color.location[0]
        specular.location[1] = base_color.location[1] - base_color.dimensions[1]



class SimpleOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.simple_operator"
    bl_label = "Simple Object Operator"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main(context)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(SimpleOperator.bl_idname, text=SimpleOperator.bl_label)


# Register and add to the "object" menu (required to also use F3 search "Simple Object Operator" for quick access).
def register():
    bpy.utils.register_class(SimpleOperator)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(SimpleOperator)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.object.simple_operator()