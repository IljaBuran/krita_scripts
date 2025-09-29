bl_info = {
    "name": "Simple Example Add-on",
    "author": "Ilja Buran",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Simple Tab",
    "description": "Adds a button that creates a cube and scales it",
    "category": "3D View",
}

import bpy
from bpy.types import Operator, Panel, AddonPreferences
from bpy.props import FloatProperty, StringProperty

# --- Add-on preferences (Edit > Preferences > Add-ons > this add-on) ---
class SIMPLEADDON_Preferences(AddonPreferences):
    bl_idname = __name__

    scale_default: FloatProperty(name="Default Scale", default=1.5, min=0.01, max=100.0)
    note: StringProperty(name="Note", default="Hello Blender!")

    def draw(self, context):
        col = self.layout.column()
        col.prop(self, "scale_default")
        col.prop(self, "note")

# --- Operator ---
class SIMPLEADDON_OT_make_cube(Operator):
    bl_idname = "simpleaddon.make_cube"
    bl_label = "Make Scaled Cube"
    bl_options = {'REGISTER', 'UNDO'}

    scale: FloatProperty(name="Scale", default=1.0, min=0.01, max=100.0)

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        obj = context.active_object
        obj.scale = (self.scale, self.scale, self.scale)
        self.report({'INFO'}, f"Made cube at scale {self.scale}")
        return {'FINISHED'}

# --- Panel in the 3D Viewport > N-panel ---
class SIMPLEADDON_PT_panel(Panel):
    bl_label = "Simple Add-on"
    bl_idname = "SIMPLEADDON_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Simple"

    def draw(self, context):
        prefs = context.preferences.addons[__name__].preferences
        col = self.layout.column(align=True)
        col.label(text=prefs.note)
        op = col.operator(SIMPLEADDON_OT_make_cube.bl_idname, text="Make Cube (Pref Scale)")
        op.scale = prefs.scale_default
        col.separator()
        col.operator(SIMPLEADDON_OT_make_cube.bl_idname, text="Make Cube (1.0)").scale = 1.0

# --- Registration ---
classes = (
    SIMPLEADDON_Preferences,
    SIMPLEADDON_OT_make_cube,
    SIMPLEADDON_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()