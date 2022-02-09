from maya import cmds

def getParent(node, level=0):
    parent = cmds.listRelatives(node, parent=True)
    if parent: parent = parent[0]
    if level > 1:
        for x in range(level-1):
            par = cmds.listRelatives(parent, parent=True)
            if par: parent = par[0]
            else: break
    return parent

def addOffset(transform, suffix='offset'):
    offset = cmds.createNode('transform', n=transform+'_'+suffix)
    par = getParent(transform)
    mtx = cmds.xform(transform, q=True, m=True, ws=True)
    cmds.xform(offset, m=mtx, ws=True)
    cmds.parent(transform, offset)
    if par:
        cmds.parent(offset, par)

def createCenterLoc(size=1, cluster=True):
    sel = pm.ls(sl=True, fl=True)
    if not sel: return

    if cluster:
        verts = list()
        for n in sel:
            if type(n) == pm.general.MeshVertex or type(n) == pm.general.NurbsCurveCV:
                verts.append(n)
            elif type(n) == pm.general.MeshEdge:
                for v in n.connectedVertices(): verts.append(v)
            elif type(n) == pm.general.MeshFace:
                for v in n.getVertices():
                    meshName = n.name().split('.')[0]
                    verts.append(pm.PyNode('{0}.vtx[{1}]'.format(meshName, v)))
        if not verts: return
        clst, handle = pm.cluster(verts)

        loc = pm.spaceLocator()
        pm.delete(pm.pointConstraint(handle, loc, mo=False))
        loc.localScale.set(size, size, size)

        pm.delete(clst, handle)

        return loc

    else:
        pos, finalPos = list(), pm.dt.Point(0, 0, 0)
        for n in sel:
            if type(n) == pm.nt.Transform:
                pos.append(n.getTranslation(space='world'))
            elif type(n) == pm.general.MeshVertex or type(n) == pm.general.NurbsCurveCV:
                pos.append(n.getPosition(space='world'))
            elif type(n) == pm.general.MeshEdge:
                for v in n.connectedVertices(): pos.append(v.getPosition(space='world'))

        if pos:
            posX, posY, posZ = [p.x for p in pos], [p.y for p in pos], [p.z for p in pos]
            x = float(sum(posX) / len(pos))
            y = float(sum(posY) / len(pos))
            z = float(sum(posZ) / len(pos))
            finalPos = pm.dt.Point(x, y, z)

        loc = pm.spaceLocator()
        loc.setTranslation(finalPos, space='world')
        loc.localScale.set(size, size, size)

        return loc


def createCenterPos(pos):
    if type(pos) == pm.nt.NurbsCurve:
        pos = [p.getPosition(space='world') for p in pos.cv]
    elif type(pos) == list and type(pos[0]) == pm.general.NurbsCurveCV:
        pos = [p.getPosition(space='world') for p in pos]
    elif type(pos) == list and hasattr(pos[0], 'getTranslation'):
        pos = [p.getTranslation(space='world') for p in pos]

    posX, posY, posZ = [p.x for p in pos], [p.y for p in pos], [p.z for p in pos]
    x = float(sum(posX) / len(pos))
    y = float(sum(posY) / len(pos))
    z = float(sum(posZ) / len(pos))
    finalPos = pm.dt.Point(x, y, z)

    return finalPos




