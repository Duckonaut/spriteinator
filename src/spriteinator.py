import bpy
import os
from math import pi, cos, sin, tan

bl_info = {
    "name": "Spriteinator",
    "author": "Duckonaut",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "File > Export",
    "description": "Export scene as directional sprites",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"
}

def export_as_sprites(context, filepath, step_count, distance, angle, animation_resolution, fov):
    # check if filepath is valid (we want a directory)
    # if filepath points to a file, we throw an error
    if os.path.exists(filepath) and os.path.isfile(filepath):
        print("ERROR: filepath is a file, not a directory")
        return {'CANCELLED'}

    # make sure filepath ends with a slash
    if not filepath.endswith("/"):
        filepath += "/"

    # spawn camera
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.location = (0, distance, 0)
    rel_angle = (90.0 + angle) * (pi / 180.0)
    rad_angle = angle * (pi / 180.0)
    camera.data.lens = fov

    # store previous active camera
    previous_active_camera = bpy.context.scene.camera

    # set camera as active
    bpy.context.scene.camera = camera

    height = distance * sin(-rad_angle)

    for i in range(0, step_count):
        iter_angle = i * (2 * pi / step_count)
        # spin camera
        camera.rotation_euler = (rel_angle, 0, pi - iter_angle)
        location_flat = (sin(iter_angle), cos(iter_angle))
        # location x and y then scale by distance * cos(angle)
        scaler = cos(-rad_angle) * distance
        location_flat = (location_flat[0] * scaler, location_flat[1] * scaler)
        # location z scales with sin(angle)
        location = (location_flat[0], location_flat[1], height)

        # move camera
        camera.location = location

        # get ready to render stuff
        dir_name = filepath + str(i)
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)

        bpy.context.scene.render.filepath = dir_name + "/"

        # render all animation frames for all animations in file
        for action in bpy.data.actions:
            bpy.context.scene.frame_start = int(action.frame_range[0])
            bpy.context.scene.frame_end = int(action.frame_range[1])
            bpy.context.scene.frame_step = animation_resolution
            bpy.context.scene.render.filepath = dir_name + "/" + action.name + "."
            bpy.ops.render.render(animation=True)

    # restore previous active camera
    bpy.context.scene.camera = previous_active_camera

    # delete camera
    bpy.ops.object.delete()

    return {'FINISHED'}


# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_types import Operator


class ExportAsDirectionalSprites(Operator):
    """Exports the file as a series of directional sprites"""
    bl_idname = "spriteinator.sprites"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export as Directional Sprites"

    step_count: bpy.props.IntProperty(
        name="Direction Step Count",
        description="How many steps around the model to snap",
        min=0,
        max=360,
        soft_min=1,
        soft_max=16,
        step=1,
        default=8,
    )

    angle: bpy.props.FloatProperty(
        name="Camera Angle",
        description="The angle to take the camera above the \"equator\"",
        min=-90.0,
        max=90.0,
        default=-30.0
    )

    distance: bpy.props.FloatProperty(
        name="Camera Distance",
        description="The distance from world origin to spin at",
        min=0.0,
        default=10.0,
    )

    fov: bpy.props.FloatProperty(
        name="Camera Field of View",
        description="The camera FOV",
        min=1.0,
        max=179.0,
        default=70.0,
    )

    animation_resolution: bpy.props.IntProperty(
        name="Animation Resolution",
        description="Render every nth frame",
        min=1,
        max=1000,
        default=1,
    )

    directory: bpy.props.StringProperty(
        name="Directory Path",
        description="Directory to export to",
        maxlen=1024,
        subtype='DIR_PATH',
    )

    def invoke(self, context, _event):
        import os
        if not self.directory:
            blend_filepath = context.blend_data.filepath
            if not blend_filepath:
                blend_filepath = "untitled"
            else:
                blend_filepath = os.path.dirname(blend_filepath)

            self.directory = blend_filepath

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        return export_as_sprites(context,
                                 self.directory,
                                 self.step_count,
                                 self.distance,
                                 self.angle,
                                 self.animation_resolution,
                                 self.fov)


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportAsDirectionalSprites.bl_idname, text="Export as Directional Sprites")


# Register and add to the "file selector" menu (required to use F3 search "Text Export Operator" for quick access).
def register():
    bpy.utils.register_class(ExportAsDirectionalSprites)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportAsDirectionalSprites)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.spriteinator.sprites('INVOKE_DEFAULT')

