from maya import cmds
from maya.api import OpenMaya as om
from math import degrees, sqrt


def mirror_joints_translation(source_joints, destination_joints, axis='x'):
    """
    This method applies mirroring translation to a list of joints.
    """

    center = 0
    axis_index = 'xyz'.find(axis)

    for (sourceJoint, destJoint) in zip(source_joints, destination_joints):
        sourceJointPosition = cmds.xform(sourceJoint, query=True, worldSpace=True, translation=True)

        # Mirror the joint position.
        destJointPosition = sourceJointPosition
        destJointPosition[axis_index] = center - (destJointPosition[axis_index] - center)

        cmds.xform(destJoint, worldSpace=True, translation=destJointPosition)


def center_joints(joints, axis='x'):
    """
    This method centers a list of joints so they lie directly on the mirror plane.
    """

    axis_index = 'xyz'.find(axis)

    for joint in joints:
        jointPosition = cmds.xform(joint, query=True, worldSpace=True, translation=True)

        # Center the joint to the symmetry plane.
        jointPosition[axis_index] = 0

        cmds.xform(joint, worldSpace=True, translation=jointPosition)


def align_joints(joints, upTarget=None, primaryAxis='x', mirror=False):
    """
    This function to align axis of joint chains.
    @param joints: list of PyNode Joint
    @param upTarget: PyNode transform
    @param primaryAxis: axis used for aim to child joint. only "x" and "y" for now.
    """

    upT = upTarget

    if not upTarget and len(joints) < 3: return '<< UP TARGET IS NEEDED FOR UP AXIS >>'

    compareVec = None
    for x, jnt in enumerate(joints[0:(len(joints) - 1)]):
        # get parent and children
        par = cmds.listRelatives(jnt, parent=True)
        childs = cmds.listRelatives(jnt, children=True)

        # get up opp target
        if upT != None:
            oppTarget = upT
        elif par:
            oppTarget = par
        else:
            oppTarget = joints[-1]

        # unparent joint and its children, and get aim target
        aimTarget = joints[x+1]
        if par:
            cmds.parent(jnt, world=True)

        if childs:
            for c in childs:
                cmds.parent(c, world=True)
                if cmds.nodeType(c) == 'joint':
                    aimTarget = c

        # obtain jnt position
        pos = om.MPoint(cmds.xform(jnt, query=True, worldSpace=True, translation=True))
        aim = om.MPoint(cmds.xform(aimTarget, query=True, worldSpace=True, translation=True))
        opp = om.MPoint(cmds.xform(oppTarget, query=True, worldSpace=True, translation=True))
        if primaryAxis == 'x':
            # xVec
            xVec = aim - pos
            if mirror:
                xVec = pos - aim

            # oppVec
            oppVec = opp - pos
            if mirror:
                oppVec = pos - opp

            # check paralel
            if xVec.isParallel(oppVec):
                if par:
                    cmds.parent(jnt, par)
                if childs:
                    cmds.parent(childs, jnt)
                return '<< UP TARGET IS NEEDED FOR UP AXIS >>'

            # zVec
            yVec = oppVec ^ xVec
            if compareVec and 0 > yVec * compareVec:
                yVec = xVec ^ oppVec  # to force up axis the same
            compareVec = yVec

            # yVec
            zVec = yVec ^ xVec

    #     elif primaryAxis == 'y':
    #         # yVec
    #         yVec = aimTarget.getTranslation(space='world') - pos
    #         if mirror: yVec = pos - aimTarget.getTranslation(space='world')
    #         if vis: xfm.vectorVis(yVec, jnt, 'yVec')
    #         # oppVec
    #         oppVec = oppTarget.getTranslation(space='world') - pos
    #         if mirror: oppVec = pos - oppTarget.getTranslation(space='world')
    #         if vis: xfm.vectorVis(oppVec, jnt, 'oppVec')
    #         # check paralel
    #         if yVec.isParallel(oppVec):
    #             if par: jnt.setParent(par)
    #             if childs: cmds.parent(childs, jnt)
    #             return '<< UP TARGET IS NEEDED FOR UP AXIS >>'
    #         # xVec
    #         xVec = yVec.cross(oppVec)
    #         if compareVec and 0 > xVec.dot(compareVec): xVec = oppVec.cross(yVec)  # to force up axis the same
    #         compareVec = xVec
    #         if vis: xfm.vectorVis(xVec, jnt, 'xVec')
    #         # zVec
    #         zVec = yVec.cross(xVec)
    #         if vis: xfm.vectorVis(zVec, jnt, 'zVec')
    #     else:
    #         return 'only "x" and "y" accepted.'
    #

        # create matrix
        matrix = [[xVec.x, xVec.y, xVec.z, 0.0],
                  [yVec.x, yVec.y, yVec.z, 0.0],
                  [zVec.x, zVec.y, zVec.z, 0.0],
                  [pos.x, pos.y, pos.z, 1.0]]

        jntM = om.MMatrix(matrix).homogenize()
        transformMatrix = om.MTransformationMatrix(jntM)
        jnt_euler_rot = transformMatrix.rotation(asQuaternion=False)

        jnt_rot = map(degrees, jnt_euler_rot)

        cmds.xform(jnt, rotation=jnt_rot, ws=True)


        # reparent all
        if par:
            cmds.parent(jnt, par)
        cmds.makeIdentity(jnt, apply=True, t=False, r=True, s=False, jo=False, n=False)

        if childs:
            cmds.parent(childs, jnt)

    cmds.xform(joints[-1], rotation=jnt_rot, ws=True)

    cmds.select(cl=True)


def align_axis(transforms, x_vec, y_vec, z_vec):
    # type: (list(str), om.MVector, om.MVector, om.MVector) -> None

    x_vec.normalize()
    y_vec.normalize()
    z_vec.normalize()

    for transform in transforms:
        pos = om.MPoint(cmds.xform(transform, q=True, t=True, ws=True))

        MTX = [x_vec.x, x_vec.y, x_vec.z, 0,
               y_vec.x, y_vec.y, y_vec.z, 0,
               z_vec.x, z_vec.y, z_vec.z, 0,
               pos.x, pos.y, pos.z, 1]

        cmds.xform(transform, matrix=MTX, ws=True)


def rotate_axis(joints=None, rotate=[0, 0, 0]):
    sel = cmds.ls(sl=True)
    joints = sel or joints
    for j in joints:
        par = cmds.listRelatives(j, parent=True)
        chd = cmds.listRelatives(j, children=True)

        if par:
            cmds.parent(j, world=True)
        if chd:
            cmds.parent(chd, world=True)

        # j.setRotation(rotate, worldSpace=True)
        cmds.xform(j, rotation=rotate, objectSpace=True, r=True)
        if par:
            cmds.parent(j, par)
        if chd:
            cmds.parent(chd, j)

    cmds.makeIdentity(joints, apply=True, t=1, r=1, s=1, n=0, pn=True)

    if sel:
        cmds.select(sel)
    else:
        cmds.select(cl=True)


def get_axis_position_from_matrix(object, axis='x'):
    # type: (str, str) -> list

    ax = 'xyz'.find(axis)

    mtx = cmds.xform(object, q=True, m=True, ws=True)
    mtx_chunks = [mtx[i:i + 4] for i in range(0, 16, 4)]

    pos = om.MPoint(mtx_chunks[-1])
    vec = om.MVector(mtx_chunks[ax][:3])

    res = pos + vec

    return list(res)[0:3]


def get_vector_from_matrix(object, axis='x', add_position=False):
    neg = False
    if '-' in axis:
        axis = axis.replace('-', '')
        neg = True

    ax = 'xyz'.find(axis)

    mtx = cmds.xform(object, q=True, m=True, ws=True)
    mtx_chunks = [mtx[i:i + 4] for i in range(0, 16, 4)]

    vec = om.MVector(mtx_chunks[ax][:3])
    if neg:
        vec *= -1

    if add_position:
        vec += om.MVector(mtx_chunks[-1][:3])

    return list(vec)


def get_distance(transform_start, transform_end):
    pos1 = om.MPoint(cmds.xform(transform_start, q=True, translation=True, ws=True))
    pos2 = om.MPoint(cmds.xform(transform_end, q=True, translation=True, ws=True))

    return pos1.distanceTo(pos2)


def create_pos_by_vector(transforms, target_transform=None, mult=1.5, create_joint=None):
    if len(transforms) < 2:
        return om.MGlobal.displayError('Transfroms must be atleast 2 to create pos by vector.')

    pos = [om.MPoint(cmds.xform(tfm, q=True, translation=True, ws=True)) for tfm in transforms]
    vec = pos[1] - pos[0]
    target_pos = pos[0]
    if target_transform and cmds.objExists(target_transform):
        target_pos = om.MPoint(cmds.xform(target_transform, q=True, translation=True, ws=True))

    res_pos = target_pos + vec * mult

    if create_joint:
        cmds.select(cl=True)
        jnt = cmds.createNode('joint', n=create_joint)
        cmds.xform(jnt, translation=list(res_pos)[:3], ws=True)
        return jnt
    elif cmds.objExists(target_transform):
        cmds.xform(target_transform, translation=list(res_pos)[:3], ws=True)
    else:
        return res_pos


def create_pos_between_array(transform_start, transform_end, num=5):
    pos1 = om.MPoint(cmds.xform(transform_start, q=True, translation=True, ws=True))
    pos2 = om.MPoint(cmds.xform(transform_end, q=True, translation=True, ws=True))

    vec = pos2 - pos1
    length = vec.length()
    vec.normalize()

    ratio = 1.0 / (num - 1)

    positionResult = list()
    for x in range(num):
        position = pos1 + (vec * (length * (ratio * x)))
        positionResult.append([position.x, position.y, position.z])

    return positionResult


def create_pos_between(transform_start, transform_end, ratio=0.5):
    pos1 = om.MPoint(cmds.xform(transform_start, q=True, t=True, ws=True))
    pos2 = om.MPoint(cmds.xform(transform_end, q=True, t=True, ws=True))

    vec = pos2 - pos1
    length = vec.length()
    vec.normalize()

    position = pos1 + (vec * (length * ratio))

    return (position.x, position.y, position.z)


def project_vector_to_vector(vec1, vec2):
    return ((vec1 * vec2) / vec2.length() ** 2) * vec2


def get_closest_point_on_mesh(position, mesh):
    # type: (list, str) -> tuple(list, str)

    if cmds.nodeType(mesh) == r'transform':
        shapes = cmds.listRelatives(mesh, shapes=True)
        shapes = [s for s in shapes if not cmds.getAttr('{0}.intermediateObject'.format(mesh))]
        if shapes:
            mesh = shapes[0]
    elif cmds.nodeType(mesh) != r'mesh':
        return om.om.MGlobal.displayError('Cannot get closest point! "{0}" is not mesh object.'.format(mesh))

    pos = om.MPoint(position)

    selection_list = om.MSelectionList()
    selection_list.add(mesh)
    mesh_depend_node = selection_list.getDependNode(0)

    if mesh_depend_node.hasFn(om.MFn.kMesh):
        mesh_fn = om.MFnMesh(mesh_depend_node)

        closest_pos, vtx = mesh_fn.getClosestPoint(pos)

        return list(closest_pos)[:3]

    else:
        return


def get_closest_distance(position, mesh):
    start_pos = om.MPoint(position)
    pos = om.MPoint(get_closest_point_on_mesh(position, mesh))  # type: (om.MPoint)

    return start_pos.distanceTo(pos)


def poleVectorPosition(nodes, length=1.0):
    """
    This function gets the position of the polevector
    @param nodes: list of PyNode Joint, the nodes to use for position, takes in 3
    @return tuples of position and rotation, the vector position of the pole vector
    """

    if not nodes or len(nodes) > 3:
        return

    start, mid, end = [om.MPoint(cmds.xform(n, q=True, t=True, ws=True)) for n in nodes[0:3]]

    startEnd = end - start
    startMid = mid - start
    dotP = startMid * startEnd
    proj = float(dotP) / float(startEnd.length())

    startEndN = startEnd.normal()
    projV = startEndN * proj

    arrowV = startMid - projV
    arrowV.normalize()
    arrowV *= length
    finalV = mid + arrowV

    # TO GET ROTATION PARAREL TO PLANE
    # get cross product
    cross1 = startEnd ^ startMid
    cross1.normalize()

    cross2 = cross1 ^ arrowV
    cross2.normalize()

    # create matrix
    matrix = [cross1.x, cross1.y, cross1.z, 0,
              arrowV.x, arrowV.y, arrowV.z, 0,
              cross2.x, cross2.y, cross2.z, 0,
              0, 0, 0, 1]

    matrixM = om.MMatrix(matrix).homogenize()
    transformMatrix = om.MTransformationMatrix(matrixM)
    euler_rot = transformMatrix.rotation(asQuaternion=False)

    rot = map(degrees, euler_rot)

    return list(finalV)[:3], list(rot)[:3]


def vectorVis(vector, transform, name='vectorPoint', size=2):
    ''' visual aid for vectors '''

    currentSelected = cmds.selected()

    vector = [vector.x, vector.y, vector.z]
    vec = cmds.dt.Vector(vector)
    grp = cmds.group(em=True)
    loc = cmds.spaceLocator()
    h = 20*size
    pointer = cmds.cone(name=name, esw=360, ch=False, d=1, hr=h, s=3, r=0.1*size)[0]
    cmds.move(pointer.getShape().cv, [h*0.1, 0, 0], r=True, ws=True)
    cmds.parent(loc, pointer, grp)

    loc.setTranslation(vec)
    cmds.delete(cmds.aimConstraint(loc, pointer, aimVector=(1, 0, 0)))

    cmds.delete(cmds.pointConstraint(transform, grp, mo=False))
    pointer.setParent(world=True)
    cmds.delete(grp)

    pointer.overrideEnabled.set(True)
    if name == 'xVec':
        pointer.overrideColor.set(13)
    elif name == 'yVec':
        pointer.overrideColor.set(14)
    elif name == 'zVec':
        pointer.overrideColor.set(6)
    else:
        pointer.overrideColor.set(11)

    cmds.select(cl=True)
    if currentSelected:
        cmds.select(currentSelected)