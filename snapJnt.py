# snapJnt
import pymel.core as pm

tgtJnt = pm.PyNode('FrontShirt_01_snapJnt')
snapJnt = [ pm.PyNode(n) for n in ('ROOTSHJnt', 'Spine_01SHJnt', 'Spine_02SHJnt', 'Spine_03SHJnt', 'Spine_TopSHJnt') ]
mtxAdd = pm.PyNode('FrontShirt_01_01_Ctrl')

multMat = []
for x, jnt in enumerate(snapJnt):
    M = pm.createNode('multMatrix', n='{}_SnapJnt{}_multMat'.format(jnt, x))
    M.matrixIn[0].set(mtxAdd.wm.get())    
    jnt.wm >> M.matrixIn[1]
    tgtJnt.parentInverseMatrix >> M.matrixIn[2] 
    multMat.append(M)

wtAddMat = pm.createNode('wtAddMatrix', n='{}_SnapJnt_wtAdd'.format(jnt))

pm.select(multMat)

for x, M in enumerate(multMat):
    M.matrixSum >> wtAddMat.attr('wtMatrix[{}].matrixIn'.format(x))
    
dcom = pm.createNode('decomposeMatrix', n='{}_SnapJnt_decomMat'.format(jnt))
wtAddMat.matrixSum >> dcom.inputMatrix

dcom.outputTranslate >> tgtJnt.translate

eulToQuatCons = pm.createNode('eulerToQuat', n='{}_SnapJnt_eulToQuatConst'.format(jnt))
quatInv = pm.createNode('quatInvert', n='{}_SnapJnt_quatInvConst'.format(jnt))
quatProd = pm.createNode('quatProd', n='{}_SnapJnt_quatProdConst'.format(jnt))
quatToEulCons = pm.createNode('quatToEuler', n='{}_SnapJnt_eulToQuatConst'.format(jnt))

tgtJnt.jointOrient >> eulToQuatCons.inputRotate
eulToQuatCons.outputQuat >> quatInv.inputQuat
dcom.outputQuat >> quatProd.input1Quat
quatInv.outputQuat >> quatProd.input2Quat
quatProd.outputQuat >> quatToEulCons.inputQuat
quatToEulCons.outputRotate >> tgtJnt.rotate