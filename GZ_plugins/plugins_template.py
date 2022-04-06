import maya.cmds as cmds
import maya.api.OpenMaya as om

def maya_useNewAPI():
    '''
    Tell Maya this plugin uses the Python API 2.0
    '''
    pass

def initializePlugin(plugin):

    vendor = "Afip Hidayatulloh"
    version = "1.0.0"

    om.MFnPlugin(plugin, vendor, version)

    # code start
    om.MGlobal.displayInfo('Hello World!')

def uninitializePlugin(plugin):
    pass

if __name__ == "__main__":
    '''
    For development test only, delete this when publish
    '''
    # It's for unload and load back the plugin
    plugin_name = "plugins_template.py" # rename this with the script file name
    cmds.evalDeferred('if cmds.pluginInfo("{0}", q=True, loaded=True): cmds.unloadPlugin("{0}")'.format(plugin_name))
    cmds.evalDeferred('if not cmds.pluginInfo("{0}", q=True, loaded=True): cmds.loadPlugin("{0}")'.format(plugin_name))