import os
from maya import mel
from maya import cmds
import pymel.core as pm
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
    sel = pm.selected()
    if sel and len(sel) == 2: source, destination = sel

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

def saveSkin(checkName=False):
    meshes = [m for m in pm.ls(sl=True, type=['transform', 'mesh']) if m.getShape() and m.getShape().type() == 'mesh']
    if not meshes:
        MGlobal.displayInfo('Please select skinned mesh to save.')
        return

    meshesD, notSkinned = {}, []

    for mesh in meshes:

        if checkName and not nme.extractName(mesh.name()):
            MGlobal.displayError(
                '"' + mesh.name() + '" is not valid name. It\'s againts msv standard naming convention.')
            return

        sclst = detectSkin(mesh)
        if sclst:
            meshesD[mesh.name()] = sclst.name()
        else:
            notSkinned.append(mesh.name())

    # check not skinned
    if notSkinned:
        message = ', '.join(notSkinned) + ' is not skinned.\nMesh will skipped.'
        choice = cmds.confirmDialog(title='Are you sure?', message=message, button=['Continue', 'Cancel'],
                                    defaultButton='Continue', cancelButton='Cancel', dismissString='Cancel')
        if choice == 'Cancel': return

    # define skin directory
    path = cmds.fileDialog2(fileMode=2, caption="Save skin directory", ff="*.sw")
    if not path:
        MGlobal.displayInfo('Please set save skin directory.')
        return
    path = path[0]

    # start export skin
    MGlobal.displayInfo('Start export skin!')
    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
    for meshName, skinClusterName in meshesD.items():
        mesh = pm.PyNode(meshName)
        numOfVertex = cmds.polyEvaluate(meshName, vertex=True)
        infJoints = cmds.skinCluster(skinClusterName, query=True, influence=True)
        fileObj = open(path + '/{}.sw'.format(str(mesh.stripNamespace())), 'w')

        cmds.progressBar(gMainProgressBar, edit=True, beginProgress=True, isInterruptable=False, maxValue=numOfVertex,
                         status='Save skin for "{}"'.format(meshName))

        fileObj.write(str(infJoints) + '\n')
        for i in range(0, numOfVertex):
            vtxName = '%s.vtx[%d]' % (meshName, i)
            trans = cmds.skinPercent(skinClusterName, vtxName, query=True, transform=None)
            jValue = []
            for t in trans:
                weight = cmds.skinPercent(skinClusterName, vtxName, transform=t, normalize=False, query=True)
                valList = (t, weight)
                jValue.append(valList)
            text = '%s,%s\n' % (vtxName.replace(mesh.namespace(), ''), str(jValue))
            fileObj.write(text)

            cmds.progressBar(gMainProgressBar, edit=True, step=1)
        cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)

        print('Skin weight of ' + meshName + ' has been saved successfully.')

    MGlobal.displayInfo('Export skin done!')

def loadSkin(checkName=False, path=None):
    meshes = [m for m in pm.ls(sl=True, type=['transform', 'mesh']) if m.getShape() and m.getShape().type() == 'mesh']
    if not meshes:
        MGlobal.displayInfo('Please select unskinned mesh to load the skinweight.')
        return

    meshesD, skinnedMesh = {}, []

    for mesh in meshes:

        if checkName:
            if not nme.extractName(mesh.name()):
                MGlobal.displayError(
                    '"' + mesh.name() + '" is not valid name. It\'s againts msv standard naming convention.')
                return

        sclst = detectSkin(mesh)
        # print 'detectSkin :',sclst
        if not sclst:
            meshesD[mesh] = str(mesh.stripNamespace()) + '.sw'
        else:
            skinnedMesh.append(mesh.name())

    # check if mesh skinned already
    if skinnedMesh:
        message = ', '.join(skinnedMesh) + ' is skinned already.\nDetach the skin first or it will skipped.'
        choice = cmds.confirmDialog(title='Are you sure?', message=message, button=['Continue', 'Cancel'],
                                    defaultButton='Continue', cancelButton='Cancel', dismissString='Cancel')
        if choice == 'Cancel': return

    # define skin directory
    if path and os.path.exists(path):
        path = path
    else:
        path = cmds.fileDialog2(fileMode=2, okCaption='Load', caption="Load skin directory", ff="*.sw")
        if not path:
            MGlobal.displayInfo('Please set load skin directory.')
            return
        path = path[0]

    skinDataAvailable = [f for f in os.listdir(path) if '.sw' in f]

    # check if skin data not available
    readyMesh, missingMesh = {}, []
    for mesh, skin in meshesD.items():
        if skin in skinDataAvailable:
            readyMesh[mesh] = skin
        else:
            missingMesh.append(mesh)

    if missingMesh:
        message = ', '.join(missingMesh) + ' skin data not found, therefore will skipped.'
        choice = cmds.confirmDialog(title='Are you sure?', message=message, button=['Continue', 'Cancel'],
                                    defaultButton='Continue', cancelButton='Cancel', dismissString='Cancel')
        if choice == 'Cancel': return

    # do load skin
    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
    for mesh, skin in readyMesh.items():
        # print  mesh, ':', skin
        meshName = str(mesh.stripNamespace())
        ns = str(mesh.namespace())
        skinData = open(path + '/' + skin, 'r')

        content = skinData.readlines()
        weightVal = content[1:]
        skinJoints = [mesh.name()] + eval(content[0])
        skinClusterName = cmds.skinCluster(skinJoints, toSelectedBones=True)[0]

        cmds.progressBar(gMainProgressBar, edit=True, beginProgress=True, isInterruptable=False,
                         maxValue=len(weightVal),
                         status='Load skin for "{}"'.format(mesh))
        for val in weightVal:
            value = val[:-1].split(',', 1)
            cmds.skinPercent(skinClusterName, ns + value[0], normalize=True, transformValue=eval(value[1]))
            cmds.progressBar(gMainProgressBar, edit=True, step=1)
        cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)

        if 'geo_' in meshName:
            cmds.rename(skinClusterName, meshName.replace('geo_', 'sclst_'))
        else:
            cmds.rename(skinClusterName, 'sclst_' + meshName)

    MGlobal.displayInfo('Load skin data for all selected mesh done.')
