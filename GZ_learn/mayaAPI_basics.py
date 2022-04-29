import maya.api.OpenMaya as om

def getDagPath(name):
    try:
        selection_list = om.MSelectionList()
        selection_list.add(name)
        return selection_list.getDagPath(0)
    except:
        om.MGlobal.displayError('No object matches or more than one object matches name: {0}'.format(name))

def getPlug(node, attribute):
    obj = getDagPath(node)
    if obj.hasFn(om.MFn.kTransform):
        transform_fn = om.MFnTransform(obj)
        return transform_fn.findPlug(attribute, False)

def omGetAttr(node, attribute):
    plug = getPlug(node, attribute)
    return plug.asDouble()

def omSetAttr(node, attribute, value):
    plug = getPlug(node, attribute)
    return plug.setDouble(value)
