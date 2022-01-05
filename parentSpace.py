# This script is for creating "SpineChest_IK_ctrl" parentSpace on Sterling and Tyrus - HOM

from maya.OpenMaya import MGlobal
import pymel.core as pm

offsetGrp = pm.PyNode('SpineChest_IK_ctrl_cons_grp')
ctrl = pm.PyNode('SpineChest_IK_ctrl')
fkik = pm.PyNode('spine_attribute_ctrl')
cons = offsetGrp.connections(s=True, d=False, type='parentConstraint')[0]

parentSpacesAttr = 'parentSpace'
parentSpaces = [pm.PyNode(n) for n in ('world_ctrl', 'spine_mid_IK_bend_ctrl', 'root_ctrl')]
enNames = ['World', 'Mid Spine', 'Root']

cons = pm.parentConstraint(parentSpaces, offsetGrp, mo=True)
ctrl.addAttr(parentSpacesAttr, at='enum', en=enNames, k=True, dv=1)
for x, target in enumerate(parentSpaces):
    floatLogic = pm.createNode('floatLogic', n='{}_{}_floatLogic'.format(ctrl, target))
    ctrl.attr(parentSpacesAttr) >> floatLogic.floatA
    floatLogic.floatB.set(x)

    mult = pm.createNode('multDoubleLinear', n='{}_{}_mult'.format(ctrl, target))
    floatLogic.outBool >> mult.input1
    fkik.fkIk >> mult.input2

    for at in cons.getWeightAliasList():
        if target.name() in at.longName():
            mult.output >> at

MGlobal.displayInfo('Parent space for "{}" is created.'.format(ctrl))