from maya import cmds, mel
import pymel.core as pm


def setToDefaultValue(selected=[], channelBox=True, transformOnly=False):
    sel = selected or pm.selected()

    if not sel: return MGlobal.displayInfo('Select nodes to set to the default value.')

    for s in sel:
        if channelBox:
            channelBox = mel.eval(
                'global string $gChannelBoxName; $temp=$gChannelBoxName;')  # fetch maya's main channelbox
            attr = pm.channelBox(channelBox, q=True, sma=True)
            if attr:
                attr = [s.attr(a) for a in attr if s.hasAttr(a)]
            else:
                attr = s.listAttr(k=True, se=True, l=False)
        else:
            attr = s.listAttr(k=True, se=True, l=False)

        if not transformOnly:
            for a in attr:
                # if a.isKeyable() and len(a.connections(d=False, s=True)) == 0 and not a.isLocked():
                if a.isKeyable():
                    try:
                        if a.isDynamic():
                            a.set(pm.addAttr(a, q=True, dv=True))
                        elif a.shortName() in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                            a.set(0)
                        elif a.shortName() in ['sx', 'sy', 'sz', 'v']:
                            a.set(1)
                    except:
                        pass
        else:
            pm.move(s, (0,0,0), os=True)
            pm.rotate(s, (0,0,0), os=True)
            pm.scale(s, (1,1,1))
            # if s.v.isKeyable() and len(s.v.connections()) == 0 and not s.v.isLocked(): s.v.set(1)

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

def getClosestTransform(tfm, target, data=False):
    if   type(tfm) != pm.dt.Matrix and hasattr(tfm, 'wm'):
        tfm = tfm.wm.get()
    elif type(tfm) == list():
        tfm = pm.dt.Matrix( (1,0,0), (0,1,0), (0,0,1), tfm[:3] )

    targetMatrix = []
    for t in target:
        if   type(t) == pm.dt.Matrix: targetMatrix.append(t)
        elif hasattr(t, 'wm'):        targetMatrix.append(t.wm.get())
        else:                         targetMatrix.append(t)

    distances = [ tfm.distanceTo(t) for t in targetMatrix ]
    indexes   = dict()
    for dist, tgt in zip(distances, target):
        indexes[dist] = tgt

    distances.sort()
    result  = [ indexes[dist] for dist in distances ]

    if data: return result
    else:    return result[0]

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


def rivetFollicle(mesh, tfm, snap=False, constraint=False, parent=False):
    if pm.objExists(mesh): mesh = pm.PyNode(mesh)
    if pm.objExists(tfm): tfm = pm.PyNode(tfm)
    
    name = tfm.name()
    
    fcl = pm.createNode('follicle')
    fcl.getParent().rename(name+'_follicle')
    parU, parV = 0.5, 0.5
    
    # Connect Objects
    if type(mesh.getShape()) == pm.nt.NurbsSurface:
        mesh.getShape().local.connect( fcl.inputSurface )
        cpom  = pm.createNode('closestPointOnSurface', n=name+'_closestPointOnSurface')
        mesh.getShape().connectAttr('worldSpace[0]', cpom.inputSurface, f=True )
        
    elif type(mesh.getShape()) == pm.nt.Mesh:
        mesh.getShape().outMesh.connect( fcl.inputMesh )
        cpom  = pm.createNode('closestPointOnMesh', n=name+'_closestPointOnSurface')
        mesh.getShape().connectAttr('outMesh', cpom.inMesh, f=True )
        
        
    pointM = pm.createNode('pointMatrixMult', n=name+'_pointMatrixMult')
    compM  = pm.createNode('decomposeMatrix', n=name+'_decomposeMatrix')
    
    mesh.getShape().connectAttr('worldInverseMatrix[0]', pointM.inMatrix, f=True )
    tfm.connectAttr('worldMatrix[0]', compM.inputMatrix, f=True )
    compM.connectAttr('outputTranslate', pointM.inPoint, f=True )
    pointM.connectAttr('output', cpom.inPosition, f=True)
    
    parU = cpom.parameterU.get()
    parV = cpom.parameterV.get()
    
    mesh.getShape().connectAttr('worldMatrix[0]', fcl.inputWorldMatrix, f=True )
    fcl.outRotate.connect( fcl.getParent().rotate )
    fcl.outTranslate.connect( fcl.getParent().translate )
    
    fcl.parameterU.set( parU )    
    fcl.parameterV.set( parV )    
    
    # snap
    if snap == True:
        # pm.delete( pm.parentConstraint( fcl.getParent(), tfm, mo=False) )
        tfm.setMatrix( fcl.getParent().wm.get() )
        
    # constraint
    if constraint:
        pm.parentConstraint( fcl.getParent(), tfm, mo=not snap)
    else:
        if parent: tfm.setParent( fcl.getParent() )

    return flc

