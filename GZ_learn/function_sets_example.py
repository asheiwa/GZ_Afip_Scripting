import maya.api.OpenMaya as om

selection = om.MGlobal.getActiveSelectionList()

# Iterate over each selected object and use the appropriate function set
# to query type specific data
for i in range(selection.length()):
    if i > 0:
        print("-------")

    obj = selection.getDependNode(i) # Returns an MObject
    print("API Type: {0}".format(obj.apiTypeStr))

    if obj.hasFn(om.MFn.kDependencyNode):  # Check if function set is compatible with the MObject

        depend_fn = om.MFnDependencyNode(obj)  # Attach supported function set to MObject
        print("Dependency Node: {0}".format(depend_fn.name()))  # Use function set to query data

        if obj.hasFn(om.MFn.kTransform):
            transform_fn = om.MFnTransform(obj)
            print("Translation: {0}".format(transform_fn.translation(om.MSpace.kTransform)))

        elif obj.hasFn(om.MFn.kMesh):
            mesh_fn = om.MFnMesh(obj)
            print("Mesh Vertices: {0}".format(mesh_fn.getVertices()))

        elif obj.hasFn(om.MFn.kCamera):
            camera_fn = om.MFnCamera(obj)
            print("Clipping Planes: {0}, {1}".format(camera_fn.nearClippingPlane, camera_fn.farClippingPlane))
