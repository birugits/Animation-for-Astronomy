import bpy
import numpy as np
from mathutils import Vector, Euler
from math import *
import os
import astropy.units as u
#from scipy.integrate import solve_ivp
from sklearn.preprocessing import MinMaxScaler


for o in bpy.context.scene.objects:
    if o.type in ['MESH','CURVE','EMPTY','LIGHT']:
        o.select_set(True)
    else:
        o.select_set(False)
bpy.ops.object.delete()

for mesh in bpy.data.meshes:
  bpy.data.meshes.remove(mesh)

for m in bpy.data.materials:
    bpy.data.materials.remove(m)

for k in bpy.context.scene.objects:
    k.animation_data_clear()
    
bpy.ops.object.light_add(type='SUN', radius=1, location=(-300, 0, 0))
bpy.context.object.data.energy = 5
bpy.data.objects['Sun'].rotation_euler = (0,-pi/2,0)
target_folder = os.path.dirname(bpy.data.filepath)
blendfile = 'Chy2Sat.blend'
directory = os.path.join(target_folder,blendfile) + "\\Object\\"
bpy.ops.wm.append(filepath=blendfile,directory=directory,filename='Chy2Sat')
bpy.ops.wm.append(filepath=blendfile,directory=directory,filename='Flame')
orbiter = bpy.data.objects['Chy2Sat']
orbiter.name = 'Orbiter'
flame = bpy.data.objects['Flame']
constraint = flame.constraints.new('CHILD_OF')
constraint.target = orbiter
constraint.inverse_matrix = constraint.target.matrix_world.inverted()
orbiter.scale = (0.01,0.01,0.01)

bpy.ops.mesh.primitive_uv_sphere_add(radius=6.371, location=(0,0,0))
bpy.ops.object.modifier_add(type='SUBSURF')
bpy.ops.object.shade_smooth()
earth = bpy.data.objects['Sphere']
earth.name = 'Earth'

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.737, location=(0,0,0))
bpy.ops.object.shade_smooth()
moon = bpy.data.objects['Sphere']
moon.name = 'Moon'

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

mat = bpy.data.materials.new(name = 'moon')
mat.use_nodes = True 
moon.data.materials.append(mat)
bsdf = mat.node_tree.nodes["Principled BSDF"]
img = '2k_moon.JPG'
file_path = os.path.join(target_folder, img)
image = bpy.data.images.load(filepath=file_path)
bsdf = mat.node_tree.nodes["Principled BSDF"]
texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
texImage.location = (-300,200)
texImage.image = image
mat.node_tree.links.new(texImage.outputs[0], bsdf.inputs[0])


def orbital_period(semi_major_axis, m, M):
    
    a = semi_major_axis
     
    if a.unit != 'm' or M.unit != 'kg':
        a = a.to(u.m)
        M = M.to(u.kg)
    
    return (4*(pi**2)*(a**3)/(G*(M+m)))**0.5

def true_anomaly(time, T, e):
    
    mean_anomaly = 2 * pi * ((time/T) % 1)
    
    if e == 0:
        return mean_anomaly
    elif 0 <= e < 1:
        eccentric_anomaly = mean_anomaly
        e_old = 0
        while abs(e_old - eccentric_anomaly) > 1e-10:
            e_old = eccentric_anomaly
            eccentric_anomaly = mean_anomaly + e * sin(e_old)
            
        true_anomaly = acos((cos(eccentric_anomaly) - e) / (1 - e * cos(eccentric_anomaly)))
        
        if mean_anomaly > pi:
            true_anomaly = 2 * pi - true_anomaly 
            
        return true_anomaly
    
    else:
        eccentric_anomaly = mean_anomaly
        e_old = 0
        while abs(e_old - eccentric_anomaly) > 1e-10:
            e_old = eccentric_anomaly
            #eccentric_anomaly = e * sinh(e_old) - mean_anomaly
            eccentric_anomaly = asinh((mean_anomaly + e_old)/e)
            
        true_anomaly = acos((e - cosh(eccentric_anomaly)) / (e * cosh(eccentric_anomaly) - 1)) 
         
        if mean_anomaly > pi:
            true_anomaly = 2 * pi - true_anomaly 
               
        return true_anomaly

def orbit_position(a, e, m, M, time):
    #Calculate the position of the planet in the xy-plane
    #a = semi_major_axis
    #e = eccentricity
    
    T = orbital_period(a, m, M)
    theta = true_anomaly(time, T, e)
    
    if e == 0:
        r = a
    elif 0 <= e < 1:
        r = a * (1 - e ** 2) / (1 + e * cos(theta))
    else:
        r = a * (e**2 - 1) / (1 + e * cos(theta))
        
    x = r * cos(theta)
    y = r * sin(theta)
    z = 0
    
    location = Vector((x.value,y.value,z))
    velocity = (G*M*(2/r - 1/a))**0.5
    
    return r, location, velocity.value

def curve_trace(coords, name):
    
    # create the Curve Datablock
    global curve_data
    
    curve_data = bpy.data.curves.new('myCurve', type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 2
    
    # map coords to spline
    w = 1   #weight
    polyline = curve_data.splines.new('POLY')
    polyline.points.add(len(coords)-1)
    
    for i, coord in enumerate(coords):
        x,y,z = coord
        polyline.points[i].co = (x, y, z, w)

    # create Object
    global curve
    
    curve = bpy.data.objects.new(name, curve_data)
    view_layer = bpy.context.view_layer
    view_layer.active_layer_collection.collection.objects.link(curve)

def orbit_parameters(perihelion, aphelion):

     P = perihelion
     A = aphelion 
         
     e = (A - P)/(A + P)
     a = P/(1 - e)
     
     return e.value, a

G = 6.673e-11 *(u.m**3/(u.kg * u.s**2)) #Gravitational Constant
M = 5.9724e24 *u.kg                     # Mass of Earth
m = 0.07346e24 *u.kg                    # Mass of Moon
a = 384748e3 *u.m                       # Semi-major axis of moon
e = 0.0549                              # Eccentricity of moon's orbit
T = orbital_period(a, m, M)             # T = 2360776.2 s
f = 10000
n = int(T.value//f) + 1
moon_angle = np.empty(shape = (0,3))
earth_angle = np.empty(shape = (0,3))

for i in np.linspace(0, 360, n, endpoint = True ):
    moon_angle = np.append(moon_angle, [[0,0,np.radians(i)]], axis=0)
    
for i in np.linspace(0, 360*T.value/(24*3600), n, endpoint = True ):
    earth_angle = np.append(earth_angle, [[0,0,np.radians(i)]], axis=0)
    
velocity = np.empty(shape = (0,1))

for i in range(n):
    _,_, v = orbit_position(a, e, m, M, i*f *u.s)
    velocity = np.append(velocity, [[1/v]], axis = 0)
    
scaler = MinMaxScaler(feature_range=(10, 25))
steps = scaler.fit_transform(velocity)
steps = steps.astype(int)

current_frame = 0
coords1 = []

for i in range(n):
    
    bpy.context.scene.frame_set(current_frame)
 
    _, location, _ = orbit_position(a, e, m, M, i*f *u.s)
    coord = location/2e6
    moon.location = coord
    moon.keyframe_insert('location')
    moon.rotation_euler = Euler(moon_angle[i])
    moon.keyframe_insert('rotation_euler')
    earth.rotation_euler = Euler(earth_angle[i])
    earth.keyframe_insert('rotation_euler')
    
    coords1.append(coord)
    
    current_frame += steps[i]
    
curve_trace(coords1, name = 'Moon_orbit')

mat = bpy.data.materials.new(name = 'orbit')
mat.use_nodes = True
curve.data.materials.append(mat)
bsdf = mat.node_tree.nodes["Principled BSDF"]
mat_op = mat.node_tree.nodes["Material Output"]
mat.node_tree.nodes.remove(bsdf)
emission = mat.node_tree.nodes.new("ShaderNodeEmission")
emission.location = (10, 300)
emission.inputs[0].default_value = (1, 0, 0, 1)
emission.inputs[1].default_value = 2
mat.node_tree.links.new(emission.outputs[0], mat_op.inputs[0])

curve_data.bevel_depth = 0.01
bevel_end = np.linspace(0,1,n)
j = 0

for i in range(n):
    curve_data.bevel_factor_end = bevel_end[i]
    curve_data.keyframe_insert(data_path='bevel_factor_end', frame = j)
    j += steps[i]
   
earth_orbits = [(230,45163),(251,54829),(276,71792),(277,89472),(276,142975)]
m = 2379 *u.kg
f = 100
coords2 = []
velocity1 = np.empty(shape=(0,1))
show_flame = [0]

for peri, aph in earth_orbits:
    
    e, a = orbit_parameters((peri+6371) *u.km, (aph+6371) *u.km)
    T = orbital_period(a, m, M)
    n = int(T.value//f) + 1
    
    for i in range(n):
        
        _, location, v = orbit_position(a, e, m, M, i*f *u.s)
        coord = location/1e3
        coords2.append(coord)
        velocity1 = np.append(velocity1, [[1/v]], axis = 0)
        
        if i == n-1:
            show_flame.append(i+show_flame[-1])
            

#eccentricity of escape hyparabolic orbit
e = 1.085
n = 540
for i in range(n):
    _, location, _ = orbit_position(a, e, m, M, i*f *u.s)
    coord = location/1e3
    coords2.append(coord)
    velocity1 = np.append(velocity1, [[1/v]], axis = 0)
    if i == n-1:
        show_flame.append(i+show_flame[-1])

distance = np.sum(np.square(np.array(coords1) - coords2[-1]), axis = 1)
idx = np.argmin(distance)

moon_orbits = [(114, 18072), (118, 4412), (179, 1412), (124, 164), (119, 127)]
M = 0.07346e24 *u.kg
f = 100
j = 35

for peri, aph in moon_orbits:
    
    e, a = orbit_parameters((peri+1737) *u.km, (aph+1737) *u.km)
    T = orbital_period(a, m, M)
    n = int(T.value//f) + 1
    
    for i in range(j, n):
        
        _, location, v = orbit_position(a, e, m, M, i*f *u.s)
        coord = location/5e2
        theta = np.radians(-10)
        coord = Vector((coord[0]*cos(theta)+coord[1]*sin(theta), -coord[0]*sin(theta)+coord[1]*cos(theta), coord[2]))
        coord = coord + coords1[idx+1]
        coords2.append(coord)
        velocity1 = np.append(velocity1, [[1/v]], axis = 0)
        
        if i == n-1:
            show_flame.append(i+show_flame[-1])
    j = 0
        
curve_trace(coords2, name = 'Orbiter_orbit')
curve.data.materials.append(bpy.data.materials['orbit'])
curve_data.bevel_depth = 0.01
curve_data.bevel_factor_mapping_end = 'SPLINE'


scaler = MinMaxScaler(feature_range=(3,8))
steps1 = scaler.fit_transform(velocity1)
steps1 = steps1.astype(int)
n = len(steps1)
bevel_end = np.linspace(0,1,n)
bevel_start = np.linspace(0, 0.75, 10)
j = 0

for i in range(0,n,14):

    curve_data.bevel_factor_end = bevel_end[i]
    curve_data.keyframe_insert(data_path='bevel_factor_end', frame = j)
    j += steps1[i]
    
j = np.sum(steps[:idx+1]) 
for i in range(len(bevel_start)):
    curve_data.bevel_factor_start = bevel_start[i]
    curve_data.keyframe_insert(data_path='bevel_factor_start', frame = j)
    j += 1
    
con = orbiter.constraints.new('FOLLOW_PATH')
con.target = bpy.data.objects['Orbiter_orbit']
con.use_curve_follow = True
con.use_fixed_location = True
offsets = np.linspace(0,1,n)
j = 0
for i in range(0,n,14):
    
    con.offset_factor = offsets[i]
    con.keyframe_insert(data_path='offset_factor', frame=j)
    j += steps1[i]
    
override={'constraint': orbiter.constraints["Follow Path"]}
#bpy.ops.constraint.followpath_path_animate(override,constraint='Follow Path')

bpy.context.scene.frame_set(sum(steps[:idx+1])-1)     #important step
con = bpy.data.objects['Orbiter_orbit'].constraints.new('CHILD_OF')
con.target = moon
con.inverse_matrix = con.target.matrix_world.inverted()
con.influence = 0
con.keyframe_insert(data_path='influence', frame=sum(steps[:idx+1])-1)
con.influence = 1
con.keyframe_insert(data_path='influence', frame=sum(steps[:idx+1]))
bpy.context.scene.frame_set(0)

list1 = [sum(steps1[:i+1]) for i in show_flame]
for i in list1:
    flame.hide_viewport = False
    flame.hide_render = False
    flame.keyframe_insert('hide_viewport',frame = i)
    flame.keyframe_insert('hide_render',frame = i)
    flame.hide_viewport = True
    flame.hide_render = True
    flame.keyframe_insert('hide_viewport',frame = i+100)
    flame.keyframe_insert('hide_render',frame = i+100)


#Adding Environment texture(stars)
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

bpy.context.scene.frame_set(0)
bpy.context.scene.frame_start = 0
bpy.context.scene.frame_end = 1850

bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.eevee.taa_render_samples = 16
bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
