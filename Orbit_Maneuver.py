import bpy
import os
import numpy as np

for o in bpy.context.scene.objects:
    if o.type in ['MESH','LIGHT','EMPTY','CAMERA']:
        o.select_set(True)
    else:
        o.select_set(False)
bpy.ops.object.delete()

for mesh in bpy.data.meshes:
  bpy.data.meshes.remove(mesh)
  
for c in bpy.data.cameras:
  bpy.data.cameras.remove(c)

for k in bpy.context.selected_objects:
    k.animation_data_clear()
    
for m in bpy.data.materials:
    bpy.data.materials.remove(m)

for c in bpy.data.collections:
    bpy.data.collections.remove(c)
    
objects = bpy.data.objects
target_folder = os.path.dirname(bpy.data.filepath)
blendfile = "ChySat_Texture.blend"
filename = "Collection"
directory = os.path.join(target_folder,blendfile)+"\\Collection\\" 
bpy.ops.wm.append(filepath=blendfile,directory=directory,filename=filename)

satellite = objects['Satellite']
rocket = objects['NurbsPath']
rocket.name = 'Rocket'
shell1 = objects['NurbsPath.002']
shell1.name = 'Shell.01'
shell2 = objects['NurbsPath.001']
shell2.name = 'Shell.02'
prop1 = objects['Cylinder.002']
prop1.name = 'Propeller.01'
prop2 = objects['Cylinder.003']
prop2.name = 'Propeller.02'
    
bpy.ops.mesh.primitive_uv_sphere_add(radius=330, location=(0,450,100))
bpy.ops.object.modifier_add(type='SUBSURF')
bpy.ops.object.shade_smooth()
earth = objects['Sphere']
earth.name = 'Earth'
bpy.data.collections[0].objects.link(bpy.data.objects['Earth'])
bpy.context.scene.collection.objects.unlink(bpy.data.objects['Earth'])

mat = bpy.data.materials.new(name = 'earth')
mat.use_nodes = True
earth.data.materials.append(mat)
img = 'earth_16k.JPG'
file_path = os.path.join(target_folder, img)
image = bpy.data.images.load(filepath=file_path)
bsdf = mat.node_tree.nodes["Principled BSDF"]
texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
texImage.location = (-300,200)
texImage.image = image
mat.node_tree.links.new(texImage.outputs[0], bsdf.inputs[0])

def parenting(parent, child, **kwargs):
    
    
    if 'start_frame' and 'end_frame' in kwargs:
        
        sf = kwargs['start_frame']
        ef = kwargs['end_frame']
        
        if sf != 0:
            bpy.context.scene.frame_set(sf - 1)
        
        constraint = child.constraints.new('CHILD_OF')
        constraint.target = parent
        constraint.inverse_matrix = constraint.target.matrix_world.inverted()
        constraint.influence = 0
        constraint.keyframe_insert(data_path='influence', frame=sf - 1)
        constraint.influence = 1
        constraint.keyframe_insert(data_path='influence', frame=sf)
        constraint.influence = 1
        constraint.keyframe_insert(data_path='influence', frame=ef - 1)
        child.keyframe_insert('location', frame = ef - 1)
        bpy.context.scene.frame_set(ef)
        child.select_set(True)
        bpy.ops.object.visual_transform_apply()
        child.keyframe_insert('location', frame = ef)
        constraint.influence = 0
        constraint.keyframe_insert(data_path='influence', frame=ef)
        
    else:
        
        constraint = child.constraints.new('CHILD_OF')
        constraint.target = parent
        constraint.inverse_matrix = constraint.target.matrix_world.inverted()

parenting(rocket,objects['Flame'])
parenting(prop1,objects['Flame.001'])
parenting(prop2,objects['Flame.002'])

img = '8k_stars.JPG'
file_path = os.path.join(target_folder, img)
image = bpy.data.images.load(filepath=file_path)
world = bpy.context.scene.world
world.use_nodes = True
bgr = world.node_tree.nodes['Background']
Envnode = world.node_tree.nodes.new("ShaderNodeTexEnvironment")
Envnode.location = (-300,100)
Envnode.image = image
world.node_tree.links.new(Envnode.outputs[0], bgr.inputs[0])
rocket.keyframe_insert('location', frame = 1)
rocket.location = (0,20,150)
rocket.keyframe_insert('location', frame = 230)

for obj in [prop1, prop2, shell1, shell2, satellite]:
    if obj in [prop1, prop2]:
        parenting(rocket,obj,start_frame=1,end_frame=100)
        obj.keyframe_insert('rotation_euler')
        x, y, z = obj.location
        
        if obj == prop1:
            obj.location = (x+2,y,z+5)
            obj.keyframe_insert('location', frame = 110)
            obj.location = (x+15,y+100,z-10)
            obj.rotation_euler = (np.radians(70), np.radians(40),0)
        else:
            obj.location = (x-2,y,z+5)
            obj.keyframe_insert('location', frame = 110)
            obj.location = (x-15,y+100,z-10)
            obj.rotation_euler = (np.radians(70), np.radians(-40),0)
              
        obj.keyframe_insert('location', frame = 250)
        obj.keyframe_insert('rotation_euler', frame = 250)
        
    elif obj in [shell1, shell2]:
        parenting(rocket,obj,start_frame=1,end_frame=150)
        obj.keyframe_insert('rotation_euler')
        x, y, z = obj.location
        
        if obj == shell1:
            obj.location = (x+2,y,z+3)
            obj.keyframe_insert('location', frame = 160)
            obj.location = (x+15,y+50,z-30)
            obj.rotation_euler = (0,np.radians(20), np.radians(50))
        else:
            obj.location = (x-2,y,z+3)
            obj.keyframe_insert('location', frame = 160)
            obj.location = (x-15,y+50,z-30)
            obj.rotation_euler = (0,np.radians(10), np.radians(-50))
               
        obj.keyframe_insert('location', frame = 250)
        obj.keyframe_insert('rotation_euler', frame = 250)
        
    else:
        parenting(rocket,obj,start_frame=1,end_frame=200)
        x, y, z = obj.location
        obj.location = (x,y+3,z+10)
        obj.keyframe_insert('location', frame = 250)
        
for obj in [objects['Flame'],objects['Flame.001'],objects['Flame.002']]:
            
    obj.hide_viewport = False
    obj.hide_render = False
    obj.keyframe_insert('hide_viewport',frame = 0)
    obj.keyframe_insert('hide_render',frame = 0)
    obj.hide_viewport = True
    obj.hide_render = True
    obj.keyframe_insert('hide_viewport',frame = 95)
    obj.keyframe_insert('hide_render',frame = 95)
    obj.hide_viewport = False
    obj.hide_render = False
    obj.keyframe_insert('hide_viewport',frame = 99)
    obj.keyframe_insert('hide_render',frame = 99)
    if obj != objects['Flame']:
        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert('hide_viewport',frame = 100)
        obj.keyframe_insert('hide_render',frame = 100)

def get_camera():
    camera = objects['Camera']
    camera.location = (-24, -33, 54)
    camera.rotation_euler = (np.radians(105), np.radians(70), np.radians(-17))
    bpy.data.cameras['Camera.001'].lens = 20
    
get_camera()

bpy.context.scene.frame_set(0)
bpy.context.scene.frame_start =0 
bpy.context.scene.frame_end = 250

bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.eevee.use_bloom = True
bpy.context.scene.eevee.taa_render_samples = 16
bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
bpy.context.scene.render.filepath = './'
#bpy.ops.render.render(animation=True, write_still=1)
