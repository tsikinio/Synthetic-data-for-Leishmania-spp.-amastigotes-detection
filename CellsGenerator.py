#python script that generates cells, infected or not. To be ran inside Blender python API

import bpy
import bmesh
import random
import math
import os

# User-defined parameters
num_images = 125  # Number of images to generate
z_offset_step = 0.0001  # Tiny Z-offset to prevent overlapping
rotation_range = (-0.2, 0.2)  # Rotation range (radians) for random tilts
output_folder = bpy.path.abspath("//SynthComps/NotInf/custom/")  # Output folder

# Ensure output folder exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Specify the name of the material to use from the library
existing_material_name = "CustomCell5"

# Check if the material exists in the Blender file
existing_material = bpy.data.materials.get(existing_material_name)

if not existing_material:
    raise ValueError(f"Material '{existing_material_name}' not found in Blender. Please add it to the scene.")

# Function to create a random organic smooth cell
def create_random_cell(name, radius, material, z_offset):
    # Create a new mesh and object
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, radius=radius, segments=random.randint(12, 24))

    # Add random smooth deformation
    for v in bm.verts:
        scale_factor = random.uniform(0.8, 1.2)  # Small random scale variation
        v.co.x *= scale_factor
        v.co.y *= scale_factor
        v.co.x += random.uniform(-0.2, 0.2) * radius * 0.1
        v.co.y += random.uniform(-0.2, 0.2) * radius * 0.1

    bm.to_mesh(mesh)
    bm.free()

    # Apply smooth shading
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()

    # Apply subdivision modifier for smooth organic look
    subdiv = obj.modifiers.new(name="Subdivision", type="SUBSURF")
    subdiv.levels = 3

    # Apply displacement modifier for subtle surface variation
    displace = obj.modifiers.new(name="Displace", type="DISPLACE")
    tex = bpy.data.textures.new(name="DisplaceTexture", type="CLOUDS")
    tex.noise_scale = random.uniform(0.2, 0.5)
    displace.texture = tex
    displace.strength = random.uniform(0.05, 0.15)

    # Apply existing material
    obj.data.materials.append(material)

    # Apply small Z-offset
    obj.location.z += z_offset

    # Apply random rotation
    obj.rotation_euler.x = random.uniform(*rotation_range)
    obj.rotation_euler.y = random.uniform(*rotation_range)
    obj.rotation_euler.z = random.uniform(-math.pi, math.pi)  # Full 360° random rotation on Z-axis

    return obj

# Set up rendering
bpy.context.scene.render.engine = 'CYCLES'  # Use Cycles for better transparency
bpy.context.scene.cycles.device = 'GPU'  # Use GPU rendering if available

# Transparent background settings
bpy.context.scene.render.film_transparent = True
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.image_settings.color_mode = 'RGBA'  # Enable Alpha channel

# Set up camera
def setup_camera():
    """Creates and adjusts the camera to ensure all objects are visible."""
    # Delete existing cameras
    for obj in bpy.data.objects:
        if obj.type == 'CAMERA':
            bpy.data.objects.remove(obj, do_unlink=True)

    bpy.ops.object.camera_add(location=(0, 0, 10))
    camera = bpy.context.object
    camera.data.type = 'ORTHO'

    # Compute the necessary ortho scale dynamically
    max_radius = max(cell_radius_range[1], parasite_radius_range[1])
    camera.data.ortho_scale = (area_size + max_radius) * 2.5  # Ensure all objects fit

    bpy.context.scene.camera = camera
    return camera

# Set up lighting
def setup_lighting():
    """Creates and adjusts lighting."""
    # Delete existing lights
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)

    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    light = bpy.context.object
    light.data.energy = 3.0
    return light

# Generate images in a loop
for i in range(num_images):
    num_cells =random.randint(1,4)  # Number of main cells per image
    num_parasites =0#random.randint(20,45)  # Number of parasite cells per image
    cell_radius_range = (0.5, 1.5)  # Min & max radius for cells
    parasite_radius_range = (0.07, 0.2)  # Min & max radius for parasites
    area_size =random.uniform(2,3)  # Spread area

    rotation_range = (-0.2, 0.2)  # Rotation range (radians) for random tilts

    print(f"Generating image {i + 1}/{num_images}...")

    # Clear scene (except camera and light)
    for obj in bpy.data.objects:
        if obj.type not in ['CAMERA', 'LIGHT']:
            bpy.data.objects.remove(obj, do_unlink=True)

    # Recreate camera and light to ensure visibility
    camera = setup_camera()
    light = setup_lighting()

    # Z-offset counter
    current_z_offset = 0.0  

    all_objects = []

    # Generate main cells with incremental Z-offset
    for j in range(num_cells):
        cell_radius = random.uniform(*cell_radius_range)
        x = random.uniform(-area_size, area_size)
        y = random.uniform(-area_size, area_size)
        current_z_offset += z_offset_step  # Increase Z-offset for each new object

        cell = create_random_cell(f"Cell_{j}", cell_radius, existing_material, current_z_offset)
        cell.location = (x, y, current_z_offset)
        all_objects.append(cell)

    # Generate parasites with incremental Z-offset
    for j in range(num_parasites):
        parasite_radius = random.uniform(*parasite_radius_range)
        x = random.uniform(-area_size, area_size)
        y = random.uniform(-area_size, area_size)
        current_z_offset += z_offset_step  # Increase Z-offset for each new parasite

        parasite = create_random_cell(f"Parasite_{j}", parasite_radius, existing_material, current_z_offset)
        parasite.location = (x, y, current_z_offset)
        all_objects.append(parasite)

    # Adjust camera to fit all objects
    if all_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in all_objects:
            obj.select_set(True)

        bpy.context.view_layer.objects.active = camera
        bpy.ops.view3d.camera_to_view_selected()  # Automatically frame objects

    # Set output path for this image
    output_path = os.path.join(output_folder, f"cellsClInf_{i+1}.png")
    bpy.context.scene.render.filepath = output_path
    
    # Render and save image
    bpy.ops.render.render(write_still=True)
    print(f"Image {i + 1} saved to: {output_path}")

# Final cleanup: Clear everything including the camera and light
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
print("Scene cleared after generating all images.")

print("All images generated successfully!")