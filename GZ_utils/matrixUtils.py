from maya import cmds

def matrixContraints(parent=None, target=None):
    ''' matrix constraint '''
    # fetch selections
    sel = cmds.ls(sl=True)
    parent = sel[0] if len(sel) >= 2 else parent
    target = sel[1] if len(sel) >= 2 else target

    # create mult matrix
    multMatrix = cmds.createNode('multMatrix', n=target+'_multMatrix')

    # get offset matrix
    worldMatrix = cmds.getAttr(target + '.worldMatrix[0]')
    worldInvMatrix = cmds.getAttr(parent + '.worldInverseMatrix[0]')
    cmds.setAttr(multMatrix + '.matrixIn[0]', worldMatrix, type="matrix")
    cmds.setAttr(multMatrix + '.matrixIn[1]', worldInvMatrix, type="matrix")
    offsetMatrix = cmds.getAttr(multMatrix + '.matrixSum')

    # connect to mult matrix
    cmds.setAttr(multMatrix+'.matrixIn[0]', offsetMatrix, type="matrix")
    cmds.connectAttr(parent+'.worldMatrix[0]', multMatrix+'.matrixIn[1]', f=True)
    cmds.connectAttr(target+'.parentInverseMatrix[0]', multMatrix+'.matrixIn[2]', f=True)

    # connect to target
    decomMatrix = cmds.createNode('decomposeMatrix', n=target + '_decomposeMatrix')
    cmds.connectAttr(multMatrix+'.matrixSum', decomMatrix+'.inputMatrix', f=True)
    for a in 'xyz':
        cmds.connectAttr(decomMatrix+'.outputTranslate'+a.upper(), target+'.t'+a, f=True)
        cmds.connectAttr(decomMatrix+'.outputRotate'+a.upper(), target+'.r'+a, f=True)

    return multMatrix


cmds.select('joint2', 'loc2')
res = matrixContraints()
