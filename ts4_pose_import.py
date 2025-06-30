import bpy

# !!!! https://docs.blender.org/api/current/bpy.types.FileHandler.html read here



def import_poses(context, filepath):
    pack_name = get_pack_name()
    paths = get_filepaths(filepath)
    for path in paths:
        import_pose(path, pack_name)
    return {'FINISHED'}


def get_pack_name():
    # TODO make this a popup or something
    # TODO discover this by directory name
    return input('Pack name: ') # replace


# returns list of strings
def get_filepaths(filepath):
    # iterate through files in filepath directory
    # filepaths = TODO
    dummy_filepath = 'C:/Users/Darby/Documents\renders/_projects/_POSES/iloon/[iloon] emotional pack - FM/af/' # repalce
    return [f'{dummy_filepath}ah.blend', f'{dummy_filepath}angry2.blend', f'{dummy_filepath}ewww.blend'] # return filepaths


# imports pose, renames, and then adds to asset library
def import_pose(filepath, pack_name):
    action = import_action(filepath)
    filename = bpy.path.display_name_from_filepath(filepath)
    default_name = action[0]
    posemaker = default_name.split('PosePack')[0]
    action[0] = f'{posemaker}{pack_name}:{filename}' # action.name = f'{posemaker}{pack_name}:{filename}'
    save_pose(action)

def save_pose(pose):
    # save action to asset library
    print(f'saved {pose[0]} to asset library')    
    

def import_action(filepath):
    print(f'importing {filepath}')
    return ['iloooon:PosePack_202106232002581848_set_1', 2, 3] # return action




# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ImportPose(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_test.import_action"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Pose"

    # ImportHelper mix-in class uses this.
    filename_ext = ".blend"

    filter_glob: StringProperty(
        default="*.blend",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    # use_setting: BoolProperty(
    #     name="Example Boolean",
    #     description="Example Tooltip",
    #     default=True,
    # )

    # type: EnumProperty(
    #     name="Example Enum",
    #     description="Choose between two items",
    #     items=(
    #         ('OPT_A', "First Option", "Description one"),
    #         ('OPT_B', "Second Option", "Description two"),
    #     ),
    #     default='OPT_A',
    # )

    directory: bpy.props.StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE', 'HIDDEN'})
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'SKIP_SAVE', 'HIDDEN'})

    # TODO figure out how to 
    def execute(self, context):
        # print(f'self.filepath = {self.filepath}')
        # return import_poses(context, self.filepath)
        print([file.name for file in self.files])
        return {'FINISHED'}


# Only needed if you want to add into a dynamic menu.
def menu_func_import(self, context):
    self.layout.operator(ImportPose.bl_idname, text="Text Import Operator")


# Register and add to the "file selector" menu (required to use F3 search "Text Import Operator" for quick access).
def register():
    bpy.utils.register_class(ImportPose)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportPose)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_test.import_action('INVOKE_DEFAULT')
