import bpy
import os
from math import pi, cos, sin

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

gd_spriteinator_direction = """extends Resource
class_name SpriteinatorDirection

@export var frames: Array[Texture2D] = []
"""

gd_spriteinator_animation = """extends Resource
class_name SpriteinatorAnimation

@export var directions: Array[SpriteinatorDirection] = []
"""

gd_spriteinator = """extends Resource
class_name Spriteinator

@export var animations: Array[SpriteinatorAnimation] = []
"""

def uidfy(string: str) -> str:
    uid = hash(string)
    # convert to unsigned int
    uid = uid & 0xffffffffffffffff

    return f'{uid:0>16x}'

def output_godot_resources(filepath, step_count, animation_resolution):
    # find project root
    project_root = filepath
    while not os.path.exists(project_root + "/project.godot"):
        project_root = os.path.dirname(project_root)
        if project_root == "/":
            print("ERROR: Could not find Godot project root")
            return

    # add script files to project/scripts/vendor/
    vendor_path = project_root + "/scripts/vendor/"
    if not os.path.exists(vendor_path):
        # create directory recursively
        os.makedirs(vendor_path, exist_ok=True)

    with open(vendor_path + "SpriteinatorDirection.gd", "w") as f:
        f.write(gd_spriteinator_direction)

    with open(vendor_path + "SpriteinatorAnimation.gd", "w") as f:
        f.write(gd_spriteinator_animation)

    with open(vendor_path + "Spriteinator.gd", "w") as f:
        f.write(gd_spriteinator)

    # output resources in filepath
    base_res_path = "res://" + os.path.relpath(filepath, project_root) + "/"

    # get output directory name, used for resource name
    output_dir_name = os.path.basename(os.path.normpath(filepath))

    animation_res_uids = []
    action_names = []

    for action in bpy.data.actions:
        direction_uids = []

        for i in range(0, step_count):
            tex_names = []
            for j in range(int(action.frame_range[0]), int(action.frame_range[1]), animation_resolution):
                tex_names.append(f'{i}/{action.name}.{j:04d}.png')

            anim_dir_uid = uidfy(f'{output_dir_name}.{action.name}.{i}')

            with open(filepath + f"/{action.name}.{i}.tres", "w") as f:
                f.write(
                        f'[gd_resource type="Resource" script_class="SpriteinatorDirection" load_steps={2 + len(tex_names)} format=3 uid="uid://{anim_dir_uid}"]\n\n')
                f.write(
                    '[ext_resource path="res://scripts/vendor/SpriteinatorDirection.gd" type="Script" id=1]\n')
                for j in range(0, len(tex_names)):
                    f.write(
                        f'[ext_resource path="{base_res_path}{tex_names[j]}" type="Texture2D" id={j + 2}]\n')

                f.write('\n[resource]\n')
                f.write(f'script = ExtResource( 1 )\n')
                f.write(f'frames = Array[Texture2D]([')
                for j in range(0, len(tex_names)):
                    f.write(f'ExtResource( {j + 2} )')
                    if j < len(tex_names) - 1:
                        f.write(", ")
                f.write(f'])\n')

            direction_uids.append(anim_dir_uid)

        anim_uid = uidfy(f'{output_dir_name}.{action.name}')

        with open(filepath + f"/{action.name}.tres", "w") as f:
            f.write(
                f'[gd_resource type="Resource" script_class="SpriteinatorAnimation" load_steps={2 + len(direction_uids)} format=3 uid="uid://{anim_uid}"]\n\n')
            f.write(
                '[ext_resource path="res://scripts/vendor/SpriteinatorAnimation.gd" type="Script" id=1]\n')
            for i in range(0, len(direction_uids)):
                f.write(
                    f'[ext_resource path="{base_res_path}{action.name}.{i}.tres" type="Resource" id={i + 2}]\n')

            f.write('\n[resource]\n')
            f.write(f'script = ExtResource( 1 )\n')
            f.write(f'directions = Array[Resource("res://scripts/vendor/SpriteinatorDirection.gd")]([')
            for i in range(0, len(direction_uids)):
                f.write(f'ExtResource( {i + 2} )')
                if i < len(direction_uids) - 1:
                    f.write(", ")
            f.write(f'])\n')
        
        animation_res_uids.append(anim_uid)
        action_names.append(action.name)

    with open(filepath + f"/{output_dir_name}.tres", "w") as f:
        f.write(
            f'[gd_resource type="Resource" script_class="Spriteinator" load_steps={2 + len(animation_res_uids)} format=3 uid="uid://{uidfy(output_dir_name)}"]\n\n')
        f.write(
            '[ext_resource path="res://scripts/vendor/Spriteinator.gd" type="Script" id=1]\n')
        for i in range(0, len(animation_res_uids)):
            f.write(
                f'[ext_resource uid="uid://{animation_res_uids[i]}" path="{base_res_path}{action_names[i]}.tres" type="Resource" id={i + 2}]\n')

        f.write('\n[resource]\n')
        f.write(f'script = ExtResource( 1 )\n')
        f.write(f'animations = Array[Resource("res://scripts/vendor/SpriteinatorAnimation.gd")]([')

        for i in range(0, len(animation_res_uids)):
            f.write(f'ExtResource( {i + 2} )')
            if i < len(animation_res_uids) - 1:
                f.write(", ")

        f.write(f'])\n')


def export_as_sprites(context, filepath, step_count, distance, angle, animation_resolution, fov, godot):
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
    rel_angle = (pi / 2 + angle)
    camera.data.lens = fov

    # store previous active camera
    previous_active_camera = bpy.context.scene.camera

    # set camera as active
    bpy.context.scene.camera = camera

    height = distance * sin(-angle)

    for i in range(0, step_count):
        iter_angle = i * (2 * pi / step_count)
        # spin camera
        camera.rotation_euler = (rel_angle, 0, pi - iter_angle)
        location_flat = (sin(iter_angle), cos(iter_angle))
        # location x and y then scale by distance * cos(angle)
        scaler = cos(-angle) * distance
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

    if godot:
        output_godot_resources(filepath, step_count, animation_resolution)

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
        min=-pi/2,
        max=pi/2,
        default=-pi/6,
        subtype='ANGLE',
    )

    distance: bpy.props.FloatProperty(
        name="Camera Distance",
        description="The distance from world origin to spin at",
        min=0.0,
        default=10.0,
        subtype='DISTANCE',
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

    godot: bpy.props.BoolProperty(
        name="Godot",
        description="Export Godot resources",
        default=False,
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
                                 self.fov,
                                 self.godot)


def menu_func_export(self, context):
    self.layout.operator(ExportAsDirectionalSprites.bl_idname, text="Export as Directional Sprites")


def register():
    bpy.utils.register_class(ExportAsDirectionalSprites)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportAsDirectionalSprites)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
