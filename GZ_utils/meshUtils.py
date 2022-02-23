from maya import cmds

bshp= 'eyelid_MSH_blendShape'
source, target = 'eyelid_MSH_OLD', 'Eyelash_mesh'

targets = [ 'Blink_L',
            'Blink_R',
            'UpperLidRaiser_R',
            'BrowLowerer_L',
            'BrowLowerer_R',
            'CheekRaiser_L',
            'CheekRaiser_R',
            'EyeDown_L',
            'EyeDown_R',
            'EyeLeft_L',
            'EyeRight_R',
            'EyeRight_L',
            'EyeLeft_R',
            'EyesClosed01_L',
            'EyesClosed01_R',
            'EyesClosed02_L',
            'EyesClosed02_R',
            'EyeUp_L',
            'EyeUp_R',
            'LidTightener_L',
            'LidTightener_R',
            'NoseWrinklerTop_L',
            'NoseWrinklerTop_R',
            'Squint_L',
            'Squint_R',
            'UpperLidRaiser_L',
            'OuterBrowDown_L',
            'OuterBrowDown_R']

# create dummy shapes
sourceDup, targetDup = [ cmds.duplicate(n, returnRootsOnly=True, n=n+'_dummy')[0] for n in (source, target)]
cmds.parent(sourceDup, targetDup, world=True)
sourceShp = [ s for s in cmds.listRelatives(source, shapes=True) if cmds.getAttr(s+'.intermediateObject') != 1 ][0]
sourceDupShp = [ s for s in cmds.listRelatives(sourceDup, shapes=True) if cmds.getAttr(s+'.intermediateObject') != 1 ][0]
cmds.connectAttr(sourceShp+'.outMesh', sourceDupShp+'.inMesh', f=True)

# create wrap
cmds.select(targetDup, sourceDup)
mel.eval('CreateWrap;')
wrap = [ w for w in cmds.listHistory(targetDup) if cmds.nodeType(w) == 'wrap' ][0]
cmds.setAttr(wrap+'.autoWeightThreshold', 0)
cmds.setAttr(wrap+'.falloffMode', 0)
cmds.setAttr(wrap+'.maxDistance', 0)

# create new targets
targetGrp = cmds.createNode('transform', n='newTargets_GRP')
newTargets = []
for tgt in targets:
    for t in targets: cmds.setAttr(bshp + '.' + t, 0)
    cmds.setAttr(bshp + '.' + tgt, 1)
    new = cmds.duplicate(targetDup, returnRootsOnly=True, n=tgt)[0]
    cmds.parent(new, targetGrp)
    newTargets.append(new)
cmds.hide(targetGrp)
for t in targets: cmds.setAttr(bshp + '.' + t, 0)

# add new Blendshape
newBshp = cmds.blendShape(target, frontOfChain=True, n=target + '_blendShape')[0]

for x, newTgt in enumerate(newTargets):
    last_used_index = cmds.blendShape(target, q=True, weightCount=True)
    new_target_index = 0 if last_used_index == 0 else last_used_index + 1
    cmds.select(newTgt)
    cmds.blendShape(newBshp, e=True, target=(target, new_target_index, newTgt, 1.0))

# clean up
cmds.delete(sourceDup, sourceDup + 'Base', targetDup, targetGrp)


