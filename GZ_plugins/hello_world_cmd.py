import maya.cmds as cmds
import maya.api.OpenMaya as om

def maya_useNewAPI():
    '''
    Tell Maya this plugin uses the Python API 2.0
    '''
    pass

class HelloWorldCmd(om.MPxCommand):

    COMMAND_NAME = "HelloWorld"

    def __init__(self):
        super(HelloWorldCmd, self).__init__()

    def doIt(self, args):
        om.MGlobal.displayInfo("Hello Maya! Afip dsini!")

    @classmethod
    def creator(cls):
        return HelloWorldCmd()


def initializePlugin(plugin):

    vendor = "Afip Hidayatulloh"
    version = "1.0.0"

    plugin_fn = om.MFnPlugin(plugin, vendor, version)

    try:
        plugin_fn.registerCommand(HelloWorldCmd.COMMAND_NAME, HelloWorldCmd.creator)
    except:
        om.MGlobal.displayError("Failed to register command: {0}".format(HelloWorldCmd))

def uninitializePlugin(plugin):
    '''
    '''
    plugin_fn = om.MFnPlugin(plugin)
    try:
        plugin_fn.deregisterCommand(HelloWorldCmd.COMMAND_NAME)
    except:
        om.MGlobal.displayError("Failed to deregister command: {0}".format(HelloWorldCmd))

if __name__ == "__main__":
    '''
    For development test only, delete this when publish
    '''
    # It's for unload and load back the plugin
    plugin_name = "hello_world_cmd.py" # rename this with the script file name
    cmds.evalDeferred('if cmds.pluginInfo("{0}", q=True, loaded=True): cmds.unloadPlugin("{0}")'.format(plugin_name))
    cmds.evalDeferred('if not cmds.pluginInfo("{0}", q=True, loaded=True): cmds.loadPlugin("{0}")'.format(plugin_name))