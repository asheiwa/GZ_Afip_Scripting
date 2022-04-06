import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui
import maya.api.OpenMayaRender as omr

def maya_useNewAPI():
    '''
    Tell Maya this plugin uses the Python API 2.0
    '''
    pass

class HelloWorldNode(omui.MPxLocatorNode):

    TYPE_NAME = "helloworld"
    TYPE_ID = om.MTypeId(0x0007F7F7)
    DRAW_CLASSIFICATION = "drawdb/geometry/helloworld"
    DRAW_REGISTRANT_ID = "HelloWorldNode"

    def __init__(self):
        super(HelloWorldNode, self).__init__()

    @classmethod
    def creator(cls):
        return HelloWorldNode()

    @classmethod
    def initialize(cls):
        pass

class HelloWorldDrawOverride(omr.MPxDrawOverride):

    NAME = "HelloWorldDrawOverride"


    def __init__(self, obj):
        super(HelloWorldDrawOverride, self).__init__(obj, None, False)

    def prepareForDraw(self, obj_path, camera_path, frame_context, old_data):
        pass

    def supportedDrawAPIs(self):
        return (omr.MRenderer.kAllDevices)

    def hasUIDrawables(self):
        return True

    def addUIDrawables(self, obj_path, draw_manager, frame_context, data):
        draw_manager.beginDrawable()

        draw_manager.text2d(om.MPoint(100, 100), "Hello Maya! This is Afip!")

        draw_manager.endDrawable()

    @classmethod
    def creator(cls, obj):
        return HelloWorldDrawOverride(obj)

def initializePlugin(plugin):

    vendor = "Afip Hidayatulloh"
    version = "1.0.0"
    api_version = "Any"

    plugin_fn = om.MFnPlugin(plugin, vendor, version, api_version)
    try:
        plugin_fn.registerNode(HelloWorldNode.TYPE_NAME,
                               HelloWorldNode.TYPE_ID,
                               HelloWorldNode.creator,
                               HelloWorldNode.initialize,
                               om.MPxNode.kLocatorNode,
                               HelloWorldNode.DRAW_CLASSIFICATION)
    except:
        om.MGlobal.displayError("Failed to register node: {0}".format(HelloWorldNode.TYPE_NAME))

    try:
        omr.MDrawRegistry.registerDrawOverrideCreator(HelloWorldNode.DRAW_CLASSIFICATION,  # draw-specific classification
                                                      HelloWorldNode.DRAW_REGISTRANT_ID,  # unique name to identify registration
                                                      HelloWorldDrawOverride.creator)  # function/method that returns new instance of class
    except:
        om.MGlobal.displayError("Failed to register draw override: {0}".format(HelloWorldDrawOverride.NAME))

def uninitializePlugin(plugin):
    '''
    '''
    plugin_fn = om.MFnPlugin(plugin)
    try:
        omr.MDrawRegistry.deregisterDrawOverrideCreator(HelloWorldNode.DRAW_CLASSIFICATION,
                                                        HelloWorldNode.DRAW_REGISTRANT_ID)
    except:
        om.MGlobal.displayError("Failed to deregister draw override: {0}".format(HelloWorldDrawOverride.NAME))

    try:
        plugin_fn.deregisterNode(HelloWorldNode.TYPE_ID)
    except:
        om.MGlobal.displayError("Failed to deregister node: {0}".format(HelloWorldNode.TYPE_NAME))

if __name__ == "__main__":
    '''
    For development test only, delete this when publish
    '''
    # create new file, because we cannot unload the plugin if we still have a node in the scene
    cmds.file(new=True, force=True)

    # It's for unload and load back the plugin
    plugin_name = "hello_world_node.py" # rename this with the script file name
    cmds.evalDeferred('if cmds.pluginInfo("{0}", q=True, loaded=True): cmds.unloadPlugin("{0}")'.format(plugin_name))
    cmds.evalDeferred('if not cmds.pluginInfo("{0}", q=True, loaded=True): cmds.loadPlugin("{0}")'.format(plugin_name))

    cmds.evalDeferred('cmds.createNode("helloworld")')