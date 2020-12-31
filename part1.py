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
    
    
target_folder = os.path.dirname(bpy.data.filepath)
blendfile = "GSLV_Mk3.blend"
filename = "Collection"
directory = os.path.join(target_folder,blendfile) + "\\Collection\\"
bpy.ops.wm.append(filepath=blendfile,directory=directory,filename=filename)

#Adding Wind force field
bpy.ops.object.effector_add(type='WIND')
bpy.ops.transform.rotate(value=3.14159, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)))
bpy.ops.transform.translate(value=(0, 0, 41))
bpy.ops.transform.resize(value=(2.5, 2.5, 1))
bpy.context.object.field.shape = 'PLANE'
bpy.context.object.field.strength = 150
bpy.ops.object.move_to_collection(collection_index = 1)

#Adding Turbulance force field
bpy.ops.object.effector_add(type='TURBULENCE')
bpy.context.object.field.shape = 'POINT'
bpy.context.object.field.strength = 100
bpy.ops.object.move_to_collection(collection_index = 1)

objects = bpy.data.objects
satellite = objects['Satellite']
domain = objects['Smoke Domain']
emitter = objects['Circle']
emitter.name = 'Emitter'
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
        constraint.influence = 0
        constraint.keyframe_insert(data_path='influence', frame=ef)
        
        bpy.context.scene.frame_set(0)
        
    else:
        
        constraint = child.constraints.new('CHILD_OF')
        constraint.target = parent
        constraint.inverse_matrix = constraint.target.matrix_world.inverted()

    
parenting(rocket,objects['Flame'])
parenting(prop1,objects['Flame.001'])
parenting(prop2,objects['Flame.002']) 

children = [satellite, prop1, prop2, shell1, shell2]
for child in children:
    parenting(rocket, child)

#DOMAIN Modifier
dm = domain.modifiers.new(name="Fluid", type='FLUID')
dm.fluid_type = 'DOMAIN'
dm.domain_settings.use_adaptive_domain = False
dm.domain_settings.use_collision_border_front = True
dm.domain_settings.use_collision_border_back = True
dm.domain_settings.use_collision_border_right = True
dm.domain_settings.use_collision_border_left = True
dm.domain_settings.use_collision_border_top = True
dm.domain_settings.use_collision_border_bottom = True
#FLOW Modifier
fm = emitter.modifiers.new(name="Fluid", type='FLUID')
fm.fluid_type = 'FLOW'
fm.flow_settings.flow_type = 'BOTH'
fm.flow_settings.flow_behavior = 'INFLOW'
fm.flow_settings.fuel_amount = 2
#EFFECTOR Modifier
em = rocket.modifiers.new(name="Fluid", type='FLUID')
em.fluid_type = 'EFFECTOR'
em.effector_settings.effector_type = 'COLLISION'

#Adding Material to "DOMAIN" object
mat = bpy.data.materials[domain.material_slots[0].name]
mat.name = 'Smoke Domain'
mat.node_tree.nodes.remove(mat.node_tree.nodes['Normal Map'])
mat.node_tree.nodes.remove(mat.node_tree.nodes['Principled BSDF'])
matop = mat.node_tree.nodes['Material Output']
volm = mat.node_tree.nodes.new("ShaderNodeVolumePrincipled")
volm.location = (-200,400)
adsh = mat.node_tree.nodes.new("ShaderNodeAddShader")
adsh.location = (100, 200)
emis = mat.node_tree.nodes.new("ShaderNodeEmission")
emis.location = (-50,0)
math = mat.node_tree.nodes.new("ShaderNodeMath")
math.location = (-400,100)
attr = mat.node_tree.nodes.new("ShaderNodeAttribute")
attr.location = (-600,100)
volm.inputs[2].default_value = 10
emis.inputs[0].default_value = (1, 0.6, 0.06, 1)
math.operation = 'MULTIPLY'
math.inputs[1].default_value = 200
attr.attribute_name = "flame"
mat.node_tree.links.new(attr.outputs[2], math.inputs[0])
mat.node_tree.links.new(math.outputs[0], emis.inputs[1])
mat.node_tree.links.new(emis.outputs[0], adsh.inputs[1])
mat.node_tree.links.new(volm.outputs[0], adsh.inputs[0])
mat.node_tree.links.new(adsh.outputs[0], matop.inputs[1])

def bake_fluid():
    
    for scene in bpy.data.scenes:
        for object in scene.objects:
            for modifier in object.modifiers:
                if modifier.type == 'FLUID':
                    if modifier.fluid_type == 'DOMAIN':
                        print("Fluid Simulation and Domain Found")
                        try:
                            override = {'scene': scene, 'active_object': object, 'point_cache': modifier.domain_settings.point_cache}
                            bpy.ops.ptcache.bake(override, bake=True)
                            break
                            print("Baking of Fluid Sim completed")
                        except:
                            print("Baking of Fluid Sim Failed")

def animation():
    x,y,z = rocket.location
    rocket.keyframe_insert('location', frame = 25)
    rocket.keyframe_insert('rotation_euler', frame = 1)
    rocket.location = (x,y+5,z+150)
    rocket.rotation_euler = (np.radians(-5),0,0)
    rocket.keyframe_insert('location', frame= 150)
    rocket.keyframe_insert('rotation_euler', frame= 150)
 
def get_camera():
    camera = objects['Camera']
    camera.location = (25, -25, 75)
    camera.rotation_euler = (np.radians(-655), 0, np.radians(335))
    bpy.data.cameras['Camera'].lens = 15
    
    constraint = camera.constraints.new('TRACK_TO')
    constraint.target = rocket
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'
    constraint.influence = 1
    constraint.keyframe_insert(data_path='influence', frame = 1)

#bake_fluid() 
# Uncomment abobe line only when run in command line
# Do baking manually if run in text editor     
animation()
get_camera()

bpy.context.scene.frame_end=110
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.eevee.use_bloom = True
bpy.context.scene.eevee.volumetric_tile_size = '4'
bpy.context.scene.eevee.taa_render_samples = 16
bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
