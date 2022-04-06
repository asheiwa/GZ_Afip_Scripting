import pymel.core as pm
from maya import cmds, mel

class SkinCage:
    GUIDES = {'spine'  : ['spine_1_guide', 'spine_2_guide', 'spine_3_guide'],
              'chest'  : ['chest_1_guide'],
              'neck'   : ['neck_1_guide', 'neck_2_guide', 'neck_3_guide'],
              'head'   : ['head_1_guide', 'head_2_guide', 'head_3_guide'],
              'lt_arm' : ['lt_arm_1_guide', 'lt_arm_2_guide', 'lt_arm_3_guide'],
              'rt_arm' : ['rt_arm_1_guide', 'rt_arm_2_guide', 'rt_arm_3_guide'],
              'lt_leg' : ['lt_leg_1_guide', 'lt_leg_2_guide', 'lt_leg_3_guide'],
              'rt_leg' : ['rt_leg_1_guide', 'rt_leg_2_guide', 'rt_leg_3_guide'],
              'lt_foot': ['lt_foot_1_guide', 'lt_foot_2_guide', 'lt_foot_3_guide'],
              'rt_foot': ['rt_foot_1_guide', 'rt_foot_2_guide', 'rt_foot_3_guide']
              }

    def __init__(self):
        self.__nurbsToPolygons_settings()

    def createHumanCage(self):
        chest_cage, chest_crv = self.__createChestCage()
        head_cage, head_crv = self.__createHeadCage()
        neck_cage = self.__createNeckCage(chest_crv, head_crv)
        # spine_cage = self.__createSpineCage()
        # arm_cage = self.__createArmCage()
        # leg_cage = self.__createLegCage()
        # hip_cage = self.__createHipCage()
        #
        allCages = [chest_cage, head_cage, neck_cage ]
        # allCages = [chest_cage, head_cage, neck_cage, spine_cage, arm_cage, leg_cage, hip_cage]

        self.humanCage = pm.polyUnite(allCages, ch=False, n='Human_Cage')[0]
        pm.polyMergeVertex(self.humanCage, d=0.1, am=1, ch=False)

        pm.select(self.humanCage)
        mel.eval('expandPolyGroupSelection;polySetToFaceNormal;')
        cmds.polySoftEdge(a=180, ch=0)
        cmds.select(cl=True)

    def __createChestCage(self):
        spine3_guide = pm.PyNode(self.GUIDES['spine'][-1])
        chest_guide = pm.PyNode(self.GUIDES['chest'][0])
        lt_arm1_guide = pm.PyNode(self.GUIDES['lt_arm'][0])
        rt_arm1_guide = pm.PyNode(self.GUIDES['rt_arm'][0])
        neck_guide = [ pm.PyNode(n) for n in self.GUIDES['neck'] ]

        # create body start
        spine3_pos = [cv.getPosition(space='world') for cv in spine3_guide.getShape().cv]
        lt_arm1_pos = [cv.getPosition(space='world') for cv in lt_arm1_guide.getShape().cv]
        rt_arm1_pos = [cv.getPosition(space='world') for cv in rt_arm1_guide.getShape().cv]
        frontPos = (spine3_pos[0:4], spine3_pos[13:])
        backPos = spine3_pos[5:12]
        lt_armPos, rt_armPos = (lt_arm1_pos[0:7], rt_arm1_pos[0:7])
        rt_armPos.reverse()
        pos = frontPos[0] + lt_armPos + backPos + rt_armPos + frontPos[1]
        startBody = pm.curve(p=pos, d=1, n='startBody')
        pm.closeCurve(startBody, ch=False, ps=1, rpo=1, bb=0.5, bki=0, p=0.1)

        # create body end
        chest = pm.duplicate(chest_guide, rr=True)[0]

        # create body end
        endBody = pm.duplicate(neck_guide[0], rr=True )[0]

        # create loft curves
        loftCurves = [startBody, chest, endBody]
        pm.parent(loftCurves[1:], world=True)

        # create chest cage
        SkinCage.rebCurves(loftCurves[1:], s=28, d=1)
        SkinCage.smoothCurve([crv.name() for crv in loftCurves[1:]], smooth=1.0)

        chestCage = SkinCage.createPolygon(loftCurves, sub_edges=2)
        border_crv = loftCurves.pop(-1)
        pm.delete(loftCurves)

        armPit1_crv = [ pm.curve(p=spine3_pos[num[0]:num[1]], d=1) for num in [(3,6), (11, 14)]]
        armPit2_crv = [ pm.curve(p=[ arm[x] for x in (0,7,6) ], d=1) for arm in (lt_arm1_pos, rt_arm1_pos) ]
        pm.reverseCurve(armPit2_crv[1], ch=False)
        armPitCage = [ SkinCage.createPolygon([x, y], sub_edges=1) for x, y in zip(armPit1_crv, armPit2_crv) ]
        pm.delete(armPit1_crv, armPit2_crv)

        chestCage = pm.polyUnite([chestCage, armPitCage], ch=False)[0]
        pm.polyMergeVertex(chestCage, d=0.1, am=1, ch=False)

        pm.select(chestCage)
        return chestCage, border_crv

    def __createNeckCage(self, *crv):
        chest_crv, head_crv = crv

        neck_crv = pm.duplicate(self.GUIDES['neck'][1], rr=True)[0]
        neck_crv.setParent(world=True)

        SkinCage.rebCurve(neck_crv, s=28, d=1)
        SkinCage.smoothCurve([neck_crv.name()], smooth=0.5)
        loftCurves = [chest_crv, neck_crv, head_crv]
        neckCage = SkinCage.createPolygon(loftCurves, sub_edges=1)
        pm.delete(loftCurves)

        return neckCage

    def __createHeadCage(self):
        head_guide = [ pm.PyNode(n) for n in self.GUIDES['head'] ]
        head1_pos = [cv.getPosition(space='world') for cv in head_guide[0].getShape().cv]
        head2_pos = [cv.getPosition(space='world') for cv in head_guide[1].getShape().cv]
        head3_pos = [cv.getPosition(space='world') for cv in head_guide[2].getShape().cv]
        frontHead1_pos = head1_pos[8:] + head1_pos[0:3]
        frontHead2_pos = head2_pos[8:] + head2_pos[0:3]
        frontHead3_pos = head3_pos[8:] + head3_pos[0:3]
        loftFront = [ pm.curve(p=pos, d=1) for pos in [frontHead1_pos, frontHead2_pos, frontHead3_pos]]
        loftBack = [pm.curve(p=pos[2:9], d=1) for pos in [head1_pos, head2_pos, head3_pos]]

        SkinCage.rebCurves(loftFront, s=12, d=1)
        SkinCage.rebCurves(loftBack, s=20, d=1)
        SkinCage.smoothCurve([crv.name() for crv in loftFront + loftBack], smooth=0.25)

        frontHeadCage = SkinCage.createPolygon(loftFront, sub_edges=2)
        frontBackCage = SkinCage.createPolygon(loftBack, sub_edges=2)

        top_pos = [cv.getPosition(space='world') for cv in loftFront[-1].getShape().cv ] + \
                  [cv.getPosition(space='world') for cv in loftBack[-1].getShape().cv[1:-1]]
        topHead1 = top_pos[2:11]
        topHead2 = top_pos[10:19]
        topHead3 = top_pos[18:27]
        topHead4 = top_pos[26:] + top_pos[0:3]
        railTop = [pm.curve(p=pos, d=1) for pos in [topHead1, topHead3, topHead4, topHead2]]
        topHeadCage = SkinCage.pBirail(railTop, 1, 1)
        cmds.polyNormal(topHeadCage, normalMode=0, userNormalMode=0, ch=0)

        neck_guide = pm.PyNode(self.GUIDES['neck'][-1])
        neckCrv = pm.duplicate(neck_guide, rr=True)[0]
        neckCrv.setParent(world=True)
        SkinCage.rebCurve(neckCrv, s=8, d=1)
        SkinCage.smoothCurve([neckCrv.name()], smooth=0.25)
        jaw_pos = [cv.getPosition(space='world') for cv in loftFront[0].getShape().cv]
        jaw1 = jaw_pos[0:3]
        jaw2 = jaw_pos[2:11]
        jaw3 = jaw_pos[10:]
        railLow = [pm.curve(p=pos, d=1) for pos in [jaw2, jaw1, jaw3]]
        railLow.insert(1, neckCrv)
        lowHeadCage = SkinCage.pBirail(railLow, 1, 1)

        headCage = pm.polyUnite(frontHeadCage, frontBackCage, topHeadCage, lowHeadCage, ch=False, n='Head_Cage')[0]
        pm.polyMergeVertex(headCage, d=0.1, am=1, ch=False)

        border_pos = [cv.getPosition(space='world') for cv in neckCrv.getShape().cv ][4:] + \
                     [cv.getPosition(space='world') for cv in loftBack[0].getShape().cv][1:-1] + \
                     [cv.getPosition(space='world') for cv in neckCrv.getShape().cv][0:4]

        border_crv = pm.curve(p=border_pos, d=1, n='head_crv')
        pm.closeCurve(border_crv, ch=False, ps=1, rpo=1, bb=0.5, bki=0, p=0.1)

        # SkinCage.insertEdgesLoop('Head_Cage.e[4]')
        # SkinCage.insertEdgesLoop('Head_Cage.e[31]')

        pm.delete(loftFront, loftBack, railTop, railLow)
        return headCage, border_crv

    def __createSpineCage(self):
        spine_guide = [pm.PyNode(n) for n in self.GUIDES['spine']]
        spineCage = SkinCage.createPolygon(spine_guide, sub_edges=3)

        return spineCage

    def __createHipCage(self):
        spine_guide = pm.PyNode(self.GUIDES['spine'][0])
        leg_guide = pm.PyNode(self.GUIDES['leg'][0])

        spine_pos = [cv.getPosition(space='world') for cv in spine_guide.getShape().cv]
        spine_crv = pm.curve(p=spine_pos[0:9], d=1)

        leg_pos = [cv.getPosition(space='world') for cv in leg_guide.getShape().cv]
        start, end = leg_pos[0] * (0, 1, 1), leg_pos[-2] * (0, 1, 1)
        hip_pos = [start] + leg_pos[0:7] + [end]
        leg_crv = pm.curve(p=hip_pos, d=1)

        loftCurves = [spine_crv, leg_crv]
        hipCage = SkinCage.createPolygon(loftCurves, sub_edges=3)

        lowerHip_pos = [leg_pos[x] for x in (0,-1,-2)]
        lowerHipCenter_pos = [p * (0,1,1) for p in lowerHip_pos]
        crv1 = pm.curve(p=lowerHip_pos, d=1)
        crv2 = pm.curve(p=lowerHipCenter_pos, d=1)
        lower_cage = SkinCage.createPolygon([crv1, crv2], sub_edges=1)

        hipCage = pm.polyUnite([hipCage, lower_cage], ch=False)[0]
        pm.polyMergeVertex(hipCage, d=0.1, am=1, ch=False)

        cmds.polyNormal(hipCage.name(), normalMode=0, userNormalMode=0, ch=0)

        pm.delete(loftCurves, crv1, crv2)

        return hipCage

    def __createArmCage(self):
        arm_guide = [pm.PyNode(n) for n in self.GUIDES['arm']]
        armCage = SkinCage.createPolygon(arm_guide, sub_edges=4)

        cmds.polyNormal( armCage.name(), normalMode=0, userNormalMode=0, ch=0)

        return armCage

    def __createLegCage(self):
        leg_guide = [pm.PyNode(n) for n in self.GUIDES['leg']]
        legCage = SkinCage.createPolygon(leg_guide, sub_edges=4)

        cmds.polyNormal(legCage.name(), normalMode=0, userNormalMode=0, ch=0)

        return legCage

    def __nurbsToPolygons_settings(self):
        cmds.nurbsToPolygonsPref(chordHeightRatio = 0.1,
                                 chordHeight = 0.2,
                                 delta3D = 0.1,
                                 edgeSwap = False,
                                 format = 2,
                                 fraction = 0.01,
                                 merge = 0,
                                 minEdgeLen = 0.001,
                                 matchRenderTessellation = 0,
                                 mergeTolerance = 0.1,
                                 polyCount = 200,
                                 polyType = 1,
                                 useChordHeight = False,
                                 useChordHeightRatio = False,
                                 uNumber = 1,
                                 uType = 3,
                                 vNumber = 1,
                                 vType = 3)

    @staticmethod
    def createPolygon(curves, sub_edges=1):
        cmds.nurbsToPolygonsPref(vNumber=sub_edges)
        return pm.loft( curves, ch=False, rn=True, ar=False, r=False, d=1, rsn=True, polygon=1 )[0]

    @staticmethod
    def pBirail(curves, uNumber=1, vNumber=1):
        cmds.nurbsToPolygonsPref(uNumber=uNumber, vNumber=vNumber)
        return pm.doubleProfileBirailSurface(curves, ch=False, bl=0.5, po=1)[0]

    @staticmethod
    def listEdgesNum():
        sel = cmds.ls(sl=True)
        return [ int(s.split('.e[')[-1].replace(']','')) for s in sel ]

    @staticmethod
    def rebCurve(crv, s=12, d=1):
        return pm.rebuildCurve(crv, ch=False, rpo=1, rt=0, end=1, kr=2, kcp=0, kep=1, kt=0, s=s, d=d, tol=0.01)

    @staticmethod
    def rebCurves(curves, s=12, d=1):
        return [ SkinCage.rebCurve(crv, s=s, d=d) for crv in curves ]

    @staticmethod
    def smoothCurve(curves, smooth=1.0):
        periodic = dict()
        for curve in curves:
            periodic[curve] = cmds.getAttr(curve+'.f')

        for k in periodic.keys():
            if periodic[k] != 0:
                pm.closeCurve(k, ch=False, ps=1, rpo=1, bb=0.5, bki=0, p=0.1)

        cmds.select(curves)
        pm.mel.eval('modifySelectedCurves smooth {0} 0;'.format(smooth))

        for k in periodic.keys():
            if periodic[k] != 0:
                pm.closeCurve(k, ch=False, ps=1, rpo=1, bb=0.5, bki=0, p=0.1)

    @staticmethod
    def pBridgeEdge(mesh, edges1, edges2, div=1):
        if hasattr(mesh, 'name'):
            mesh = mesh.name()
        edges1 = [ mesh + '.e[{0}]'.format(x) for x in edges1 ]
        edges2 = [ mesh + '.e[{0}]'.format(x) for x in edges2 ]
        cmds.select(edges1)
        cmds.select(edges2, add=True)
        # cmds.polyBridgeEdge(sv1=1, sv2=1, divisions=div, ch=False)
        mel.eval('performPolyBridgeEdge 0;')
        SkinCage.deleteHistoryUsingDuplicate(mesh)

        cmds.select(mesh)
        return mesh

    @staticmethod
    def insertEdgesLoop(edge=None, weight=0.5):
        if edge:
            cmds.select(edge)
            cmds.SelectEdgeRingSp()
        cmds.polySplitRing(ch=False,
                           splitType=1,
                           weight=weight,
                           smoothingAngle=30,
                           fixQuads=1,
                           insertWithEdgeFlow=1,
                           adjustEdgeFlow=1)

    @staticmethod
    def pDeleteHalf(mesh, edge=0, face=0):
        if hasattr(mesh, 'name'): mesh = mesh.name()
        edge = mesh+'.e[{0}]'.format(edge)
        face = mesh+'.f[{0}]'.format(face)

        cmds.select(edge)
        cmds.SelectEdgeLoopSp()
        cmds.polySplitEdge(op=1, ch=1)
        cmds.select(face)
        cmds.ConvertSelectionToShell()
        cmds.delete()
        cmds.DeleteAllHistory()

    @staticmethod
    def pMirror(mesh):
        if hasattr(mesh, 'name'): mesh = mesh.name()
        cmds.polyMirrorFace(mesh, direction=0, mergeMode=1, ch=False)

    @staticmethod
    def cCurveMirror(curve, LR=['lt','rt']):
        L, R = LR
        if L in curve:
            L_cvs = cmds.ls(curve+'.cv[*]', fl=True)
            R_cvs = cmds.ls(curve.replace(L,R)+'.cv[*]', fl=True)
            for lcv, rcv in zip(L_cvs, R_cvs):
                pos = cmds.pointPosition(lcv, world=True)
                cmds.move(pos[0] * -1, pos[1], pos[2], rcv, ws=True, a=True)
        elif R in curve:
            R_cvs = cmds.ls(curve+'.cv[*]', fl=True)
            L_cvs = cmds.ls(curve.replace(R,L)+'.cv[*]', fl=True)
            for lcv, rcv in zip(L_cvs, R_cvs):
                pos = cmds.pointPosition(rcv, world=True)
                cmds.move(pos[0] * -1, pos[1], pos[2], lcv, ws=True, a=True)
        else:
            openCurve = cmds.getAttr(curve+'.f')

            if openCurve == 0:
                cvs = cmds.ls(curve+'.cv[*]', fl=True)
                num = len(cvs)
                mid = num / 2

                left = [x for x in range(mid + 1, num)]
                right = [x for x in range(mid)]
                right.reverse()

                # center
                cv = curve + '.cv[{}]'.format(mid)
                pos = cmds.pointPosition(cv, world=True)
                cmds.move(0, pos[1], pos[2], cv, ws=True, a=True)

                for l, r in zip(left, right):
                    cv1, cv2 = curve + '.cv[{}]'.format(l), curve + '.cv[{}]'.format(r)
                    pos = cmds.pointPosition(cv1, world=True)
                    cmds.move(pos[0]*-1, pos[1], pos[2], cv2, ws=True, a=True)

            else:
                cvs = cmds.ls(curve+'.cv[*]', fl=True)
                num = len(cvs)
                mid = num / 2

                center = (0, mid)
                left = [x for x in range(1, mid)]
                right = [x for x in range(mid + 1, num)]
                right.reverse()

                for i in center:
                    cv = curve+'.cv[{}]'.format(i)
                    pos = cmds.pointPosition( cv, world=True )
                    cmds.move(0, pos[1], pos[2], cv, ws=True, a=True )

                for l, r in zip(left, right):
                    cv1, cv2 = curve + '.cv[{}]'.format(l), curve + '.cv[{}]'.format(r)
                    pos = cmds.pointPosition(cv1, world=True)
                    cmds.move(pos[0]*-1, pos[1], pos[2], cv2, ws=True, a=True)

                cmds.select(cl=True)

    @staticmethod
    def deleteHistoryUsingDuplicate(mesh):
        if hasattr(mesh, 'name'): mesh = mesh.name()

        clean = cmds.duplicate(mesh, rr=True)[0]
        cmds.delete(mesh)
        cmds.rename(clean, mesh)

        return clean

    @staticmethod
    def pSymmetrize():
        cmds.select("Human_Cage.e[443]")
        mel.eval('activateTopoSymmetry("Human_Cage.e[443]", {"Human_Cage.e[422]"}, {"Human_Cage"}, "edge", "dR_symmetrize", 1);')

if __name__ == '__main__':
    if cmds.objExists('Human_Cage'):
        cmds.delete('Human_Cage')
    scg = SkinCage()
    scg.createHumanCage()