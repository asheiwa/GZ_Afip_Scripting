import pymel.core as pm
from maya import mel
from maya.OpenMaya import MGlobal

def detectSkin(name='', checkOnly=False):
    if name != '' and pm.objExists(name):
        mesh = pm.PyNode(name)
    else:
        return MGlobal.displayInfo('"{}" not valid.'.format(name))

    sclst = mel.eval('findRelatedSkinCluster '+mesh.name())
    if pm.objExists(sclst):
        sclst = pm.PyNode(sclst)
    else:
        sclst = None

    if checkOnly:
        if sclst != None:
            return True
        else:
            return False

    return sclst

def getInfluencesFromSel():
    '''Get all influences from all selected skinned meshes'''
    influences = []
    for s in cmds.ls(sl=True):
        sclst = mel.eval('findRelatedSkinCluster {};'.format(s))
        influ = cmds.skinCluster(sclst, q=True, weightedInfluence=True)
        for i in influ:
            if i not in influences: influences.append(i)
    return influences

def copySkinWeight(source=None, destination=None, vtxID=False):
    selVtxID = []
    if pm.objExists(source): source = pm.PyNode(source)
    if pm.objExists(destination): destination = pm.PyNode(destination)

    if not source and not destination:
        sel = pm.selected()
        if len(sel) < 2: return MGlobal.displayInfo('Select source and target to copy skin weight.')

        meshVertex = [ s for s in sel if type(s) == pm.general.MeshVertex ]
        if meshVertex:
            for vtx in meshVertex: selVtxID += vtx.indices()
            src, dst = meshVertex[0].node(), sel[-1]
            if type(dst) != pm.nt.Transform :
                return MGlobal.displayInfo('Vertices selected. Please select a mesh to copy skin weight.')

        else:
            src, dst = sel[0], sel[1]

    else:
        src = source
        dst = destination

    sclst_src = detectSkin(src)
    sclst_dst = detectSkin(dst)
    if not sclst_dst:
        sclst_dst = pm.skinCluster(sclst_src.getInfluence(), dst, tsb=True)
        sclst_dst.rename( 'sclst_'+dst.name() )

    inf_src = sclst_src.getInfluence()
    inf_dst = sclst_dst.getInfluence()

    # add influence first if influence in source is not in destination
    notInf = []
    for inf in inf_src:
        if inf not in inf_dst:
            notInf.append(inf)
    if notInf:
        sclst_dst.addInfluence(notInf, lockWeights=True, weight=0)
        for i in notInf: i.lockInfluenceWeights.set(False)

    if not vtxID:
        ia = ['name','oneToOne','closestJoint']
        pm.copySkinWeights(ss=sclst_src, ds=sclst_dst, noMirror=True, influenceAssociation=ia)
        MGlobal.displayInfo('Copy skin weight from "{}" to "{}".'.format(src, dst))
    else:
        src_numOfVertex = cmds.polyEvaluate(src.name(), vertex=True)
        dst_numOfVertex = cmds.polyEvaluate(dst.name(), vertex=True)
        max = src_numOfVertex
        if meshVertex: max = len(selVtxID)

        gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
        cmds.progressBar(gMainProgressBar, edit=True, beginProgress=True, isInterruptable=False, maxValue=max,
                         status='Copying skin from "{}" to "{}"...'.format(src, dst))

        for i in range(src_numOfVertex):
            if i <= dst_numOfVertex and i in selVtxID:
                src_vtxName = '%s.vtx[%d]' % (src.name(), i)
                dst_vtxName = '%s.vtx[%d]' % (dst.name(), i)
                trans = cmds.skinPercent(sclst_src.name(), src_vtxName, query=True, transform=None)
                jValue = []
                for t in trans:
                    weight = cmds.skinPercent(sclst_src.name(), src_vtxName, transform=t, normalize=False, query=True)
                    valList = (t, weight)
                    jValue.append(valList)

                cmds.skinPercent(sclst_dst.name(), dst_vtxName, normalize=True, transformValue=jValue)

                cmds.progressBar(gMainProgressBar, edit=True, step=1)

        cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)

        MGlobal.displayInfo('Copy skin weight from "{}" to "{}" per vertex ID done.'.format(src, dst))