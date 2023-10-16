# Spriteinator
A Blender tool for exporting a scene as a series of pre-rendered sprites, viewed from N directions.

## Requirements
This has been tested on Blender 3.6, but there's nothing that should stop it from working as early as 2.80

## Features
### Animations
Exports each available Blender Action as a series of frames for each direction. The naming scheme is `ACTION_NAME.FRAME`.

You can define the animation resolution, this steps the animation a given number of frames between renders.

### Godot exporting
> [!IMPORTANT]
> This addon only supports Godot 4.1+.
> It uses typed array export for making working with the exported resources nicer,
> and they have only been added in 4.1.

With the Godot option checked, if the export folder is in a Godot project, handles organizing the frame data.
- Inserts a couple GDScript files to define custom Spriteinator resources in `res://scripts/vendor/`
- Creates a mega-resource `DIRECTORY_NAME.tres` in the directory you exported to, containing all the information.
- To access it, check how it's structured in the editor, it goes `Animation -> Direction -> Frame`

## Installation
As is usual with Blender add-ons, navigate to `Edit > Preferences > Add-ons`, click the `Install` button, and select `spriteinator.py` you downloaded.

### License
This project is licensed under the MIT license.
