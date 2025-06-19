#python script that generates cells, infected or not. To be ran inside Blender python API


import bpy
from pascal_voc_writer import Writer
import random
from datetime import datetime
import math
import mathutils
import os
import json
import numpy as np
from mathutils import Euler
from mathutils.bvhtree import BVHTree


#functions
def clamp(x, minimum, maximum):
    return max(minimum, min(x, maximum))

def camera_view_bounds_2d(scene, cam_ob, me_ob):
    """
    Returns camera space bounding box of mesh object.

    Negative 'z' value means the point is behind the camera.

    Takes shift-x/y, lens angle and sensor size into account
    as well as perspective/ortho projections.

    :arg scene: Scene to use for frame size.
    :type scene: :class:`bpy.types.Scene`
    :arg obj: Camera object.
    :type obj: :class:`bpy.types.Object`
    :arg me: Untransformed Mesh.
    :type me: :class:`bpy.types.Mesh´
    :return: a Box object (call its to_tuple() method to get x, y, width and height)
    :rtype: :class:`Box`
    """

    mat = cam_ob.matrix_world.normalized().inverted()  #  Get the inverse transformation matrix.
    depsgraph = bpy.context.evaluated_depsgraph_get()  
    mesh_eval = me_ob.evaluated_get(depsgraph)
    me = mesh_eval.to_mesh()
    me.transform(me_ob.matrix_world)
    me.transform(mat)

    camera = cam_ob.data
    frame = [-v for v in camera.view_frame(scene=scene)[:3]]
    camera_persp = camera.type != 'ORTHO'

    lx = []
    ly = []

    for v in me.vertices:
        co_local = v.co
        z = -co_local.z

        if camera_persp:
            if z == 0.0:
                lx.append(0.5)
                ly.append(0.5)

            else:
                frame = [(v / (v.z / z)) for v in frame]

        min_x, max_x = frame[1].x, frame[2].x
        min_y, max_y = frame[0].y, frame[1].y

        x = (co_local.x - min_x) / (max_x - min_x)
        y = (co_local.y - min_y) / (max_y - min_y)

        lx.append(x)
        ly.append(y)

    min_x = clamp(min(lx), 0.0, 1.0)
    max_x = clamp(max(lx), 0.0, 1.0)
    min_y = clamp(min(ly), 0.0, 1.0)
    max_y = clamp(max(ly), 0.0, 1.0)

    mesh_eval.to_mesh_clear()

    r = scene.render
    fac = r.resolution_percentage * 0.01
    dim_x = r.resolution_x * fac
    dim_y = r.resolution_y * fac

    # Sanity check
    if round((max_x - min_x) * dim_x) == 0 or round((max_y - min_y) * dim_y) == 0:
        return (0, 0, 0, 0)

    return (
        round(min_x * dim_x),            # X
        round(dim_y - max_y * dim_y),    # Y
        round((max_x - min_x) * dim_x),  # Width
        round((max_y - min_y) * dim_y)   # Height
    )


# Render scene in JPEG format
def render_scene(it, resolution_x, resolution_y):
    bpy.context.scene.render.image_settings.file_format='JPEG'
    bpy.context.scene.render.filepath = output_dir + "/Customimage" + "-"+"%0.5d.jpg"%it #Setup output files name
     # Set resolution
    bpy.context.scene.render.resolution_x = resolution_x
    bpy.context.scene.render.resolution_y = resolution_y
    bpy.ops.render.render(use_viewport = True, write_still=True)



def add_image_as_plane(image_path):
    # Ensure the image file exists
    if not os.path.isfile(image_path):
        print(f"Error: File not found at {image_path}")
        return

    # Extract the directory and filename from the image path
    directory, filename = os.path.split(image_path)

    # Import the image as a plane
    bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects
    bpy.ops.image.import_as_mesh_planes(
        files=[{"name": filename}],
        directory=directory,
        align='WORLD',
        relative=True,
        shader='PRINCIPLED',
        size_mode='ABSOLUTE',
        height=1.0
    )

#main    

#Get parameters from json
json_file_path = "PATH_TO_PARAMETERS"  # Path to JSON 
with open(json_file_path, "r") as file:
    js = json.load(file)
    
#setup output directory
output_dir = js["output_directory"]
if not os.path.exists(output_dir):
    os.makedirs(output_dir)    
    
# Path to the folder containing images of not infected cells
NotInfCellsFolderPathBase = js["NotInfCellsDirectory"]   
# Path to the folder containing images of infected cells
InfCellsFolderPathBase=js["InfCellsDirectory"]
# Path to the folder containing background images
BackgroundsFolderPathBase=js["BackgroundsDirectory"]

#Number of images:
numImg= js["number_of_images"]
infectedCells=[]
scene=[]
image=0

for i in range(0, numImg):
    #deselect all objects
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = None 
    
    image+=1
    imgType=random.randint(1,6) #Different types of images -> access to different folders
    if imgType==1:
        t="custom7"
    elif imgType==2:
        t="custom4"
    elif imgType==3:
        t="mixCustom"     
    elif imgType==4:
        t="custom3"     
    elif imgType==5:
        t="custom"     
    elif imgType==6:
        t="custom2"    
         
  
    NotInfCellsFolderPath = os.path.join(NotInfCellsFolderPathBase, t)
    InfCellsFolderPath = os.path.join(InfCellsFolderPathBase, t)
    BackgroundsFolderPath = os.path.join(BackgroundsFolderPathBase, t)
    
      
    # List all image files in the folder containing not infected cells
    NotInfCellsImageFiles = [f for f in os.listdir(NotInfCellsFolderPath ) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    # List all image files in the folder containing infected cells
    InfCellsImageFiles= [f for f in os.listdir(InfCellsFolderPath ) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    # List all image files in the folder containing backgrounds
    BackgroundsFiles=  [f for f in os.listdir(BackgroundsFolderPath ) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    
        
    #import background
    background_selection= random.choice(BackgroundsFiles)
    add_image_as_plane(str(BackgroundsFolderPath) + "/"+ str(background_selection))
    
    #rename object
    active_object = bpy.context.view_layer.objects.active
    active_object.name="background"
    background=bpy.data.objects["background"]
    background.dimensions=(8, 8,0)
    background.location=(0.95,0,0)
    scene.append(background)
    
    #br    
        
    
    numOfCells= random.randint(10,40)) 
    frame_length= background.dimensions[0]
    
    dimen=0
    #br            
    for ii in range(0,numOfCells):
        #import cell
        InfOrNot= random.randint(1,8) # possibility of infected cell
        if InfOrNot==2:
            selected_cell= random.choice(InfCellsImageFiles)
            add_image_as_plane(InfCellsFolderPath + "/"+ selected_cell)
            infectedCells.append(bpy.context.view_layer.objects.active)
            
        else:
            selected_cell= random.choice(NotInfCellsImageFiles)
            add_image_as_plane(NotInfCellsFolderPath + "/"+ selected_cell)  
        
        #rename object
        bpy.context.view_layer.objects.active.name = "cell" + str(ii)
        cell=bpy.data.objects["cell" + str(ii)]
        scene.append(cell)
        if  InfOrNot==2:
            scaler=random.uniform(0.6, 0.8)    
        else:
            scaler= random.uniform(0.3, 0.5)   
        cell.scale=(scaler,scaler,scaler)
        cell.rotation_euler=(0,0, math.radians(random.randint(0,360)))
        #update the scene
        bpy.context.scene.frame_set(1)    
        
        #define 1st cell position
        posx=-0.75
        posy=0.39
        posz=0.1
        
        #cell's position randomisation 
        randomiser=random.uniform(-0.05, 0.05)
        
        if image % 7 ==0:
            h=1.5
        else:    
            h=random.randint(1,3)
        
        
        
        if ii==0:
            cell.location=(posx,posy,posz)
            previous_cell=cell
            dimen=cell.dimensions[0]
            
        elif ( dimen < 1.73): 
            cell.location= (previous_cell.location[0]+ h*previous_cell.dimensions[0] - randomiser, previous_cell.location[1] + randomiser, previous_cell.location[2]+0.001)
            previous_cell=cell
            dimen+= cell.dimensions[0]
        elif (dimen > 1.73):
            cell.location= (posx, previous_cell.location[1] - h* cell.dimensions[1], previous_cell.location[2]+ 0.001)
            previous_cell=cell
            dimen=0  
            
                   
    #camera setup
    cam=random.randint(0,5)
    camera = bpy.context.scene.camera
    
    #standard camera position
    if cam!=1:
        camera.location=(1.07,-1,6.6) #(0.72, -1, 10)
        camera.rotation_euler=(0,0,0)
    elif cam==1:
        if infectedCells != []:
            target_cell= random.choice(infectedCells)
            camera.location=(target_cell.location[0],target_cell.location[1], random.uniform(2,3))
            
        else:
            camera.location=(0.72, -1, 10)    
            camera.rotation_euler=(0,0,0)
        
    #lightning setup
    #light = bpy.data.objects.get("light")
    #light.data.energy= random.randint(50,350)
    
    
    #render
    
    
    render_scene(i, js["resolution_x"],js["resolution_y"])
    print("render is done")  
    #annotations generation
    writer = Writer(output_dir +"/Customimage"+ "-"+"%0.5d.jpg"%i, js["resolution_x"],js["resolution_y"])
    for object in infectedCells:
        if object is not None:            
            bound_x, bound_y, bound_w, bound_h = (camera_view_bounds_2d(bpy.context.scene, bpy.context.scene.camera, object))
            part_name= "Infected"
            if (bound_x != 0 or bound_y !=0 or bound_w != 0 or bound_h != 0):
                writer.addObject(part_name, bound_x, bound_y, bound_x+bound_w, bound_y+bound_h)
    writer.save(output_dir + "/Customimage-"+ "%0.5d.xml"%i)
    
    #clear scene     
    for object in scene:
        bpy.data.objects.remove(object, do_unlink=True)
    
    #clear lists        
    scene.clear()
    infectedCells.clear()    
       
   
        
                  
              
            
                
        
        


