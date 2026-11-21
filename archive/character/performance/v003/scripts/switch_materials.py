"""Run from Blender Text Editor. Real MToon companion material switch."""
import bpy
MODE='MTOON'  # Change to BEAUTY to restore the art-directed EEVEE materials.
key='mtoon_companion' if MODE=='MTOON' else 'beauty_companion'
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 for slot in ob.material_slots:
  m=slot.material
  if m and key in m and m[key] in bpy.data.materials:slot.material=bpy.data.materials[m[key]]
