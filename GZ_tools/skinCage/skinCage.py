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
              'rt_foot': ['rt_foot_1_guide', 'rt_foot_2_guide', 'rt_foot_3_guide'],
              'lt_hand': ['lt_hand_1_guide', 'lt_hand_2_guide'],
              'rt_hand': ['rt_hand_1_guide', 'rt_hand_2_guide'],
              'lt_fingers': [ ['lt_finger{0}_{1}_guide'.format(i, x+1) for x in range(3)] for i in range(5)],
              'rt_fingers': [ ['rt_finger{0}_{1}_guide'.format(i, x+1) for x in range(3)] for i in range(5)],
              }

    def __init__(self):
        self.__nurbsToPolygons_settings()

    def createHumanCage(self):
        chest_cage, chest_crv = self.__createChestCage()
        head_cage, head_crv = self.__createHeadCage()
        neck_cage = self.__createNeckCage(chest_crv, head_crv)
        spine_cage = self.__createSpineCage()
        arm_cage = self.__createArmCage()
        hip_cage = self.__createHipCage()
        leg_cage = self.__createLegCage()
        foot_cage = self.__createFoot()
        hands_cage = self.__createHands()

        allCages = [chest_cage, head_cage, neck_cage, spine_cage, arm_cage, hip_cage, leg_cage, foot_cage, hands_cage]

        self.humanCage = pm.polyUnite(allCages, ch=False, n='Human_Cage')[0]
        pm.polyMergeVertex(self.humanCage, d=0.01, am=1, ch=False)

        pm.select(self.humanCage)
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
        # return None, None

    def __createSpineCage(self):
        spine_guide = [pm.PyNode(n) for n in self.GUIDES['spine']]
        spineCage = SkinCage.createPolygon(spine_guide, sub_edges=3)

        return spineCage

    def __createHipCage(self):
        spine_guide = pm.PyNode(self.GUIDES['spine'][0])
        lt_leg_guide = pm.PyNode(self.GUIDES['lt_leg'][0])
        rt_leg_guide = pm.PyNode(self.GUIDES['rt_leg'][0])

        spine_crv = pm.duplicate(spine_guide, rr=True)[0]
        spine_crv.setParent(world=True)

        lt_leg_pos = [cv.getPosition(space='world') for cv in lt_leg_guide.getShape().cv]
        rt_leg_pos = [cv.getPosition(space='world') for cv in rt_leg_guide.getShape().cv]
        lt_hip, rt_hip = lt_leg_pos[:-1], rt_leg_pos[:-1]
        rt_hip.reverse()
        hip_pos = [lt_hip[0]*(0,1,1)] + lt_hip + [rt_hip[0]*(0,1,1)] + rt_hip
        hip_crv = pm.curve(p=hip_pos, d=1)
        pm.closeCurve(hip_crv, ch=False, ps=1, rpo=1, bb=0.5, bki=0, p=0.1)

        loftCurves = [spine_crv, hip_crv]
        upperCage = SkinCage.createPolygon(loftCurves, sub_edges=3)

        lt_lowerHip_pos = [lt_leg_pos[x] for x in (0,-1,-2)]
        rt_lowerHip_pos = [rt_leg_pos[x] for x in (0,-1,-2)]
        lowerHipCenter_pos = [ hip_pos[0], ((lt_lowerHip_pos[1] + rt_lowerHip_pos[1]) * 0.5 ) * (0,1,1), hip_pos[8] ]
        lt_crv = pm.curve(p=lt_lowerHip_pos, d=1)
        rt_crv = pm.curve(p=rt_lowerHip_pos, d=1)
        crv = pm.curve(p=lowerHipCenter_pos, d=1)
        lowerCage = SkinCage.createPolygon([lt_crv, crv, rt_crv], sub_edges=1)

        hipCage = pm.polyUnite([upperCage, lowerCage], ch=False)[0]
        pm.polyMergeVertex(hipCage, d=0.1, am=1, ch=False)

        cmds.polyNormal(hipCage.name(), normalMode=0, userNormalMode=0, ch=0)

        pm.delete(loftCurves, lt_crv, rt_crv, crv)

        return hipCage

    def __createArmCage(self):
        lt_arm_guide = [pm.PyNode(n) for n in self.GUIDES['lt_arm']]
        rt_arm_guide = [pm.PyNode(n) for n in self.GUIDES['rt_arm']]
        lt_armCage = SkinCage.createPolygon(lt_arm_guide, sub_edges=4)
        rt_armCage = SkinCage.createPolygon(rt_arm_guide, sub_edges=4)

        cmds.polyNormal( lt_armCage.name(), normalMode=0, userNormalMode=0, ch=0)

        for arm in [lt_armCage, rt_armCage]:
            SkinCage.insertEdgesLoop(arm.name() + '.e[37]', weight=0.9)
            SkinCage.insertEdgesLoop(arm.name() + '.e[88]', weight=0.1)
            SkinCage.insertEdgesLoop(arm.name() + '.e[101]', weight=0.9)
            SkinCage.pDeleteEdgesLoop(arm.name() + '.e[46]')

        armCage = pm.polyUnite([lt_armCage, rt_armCage], ch=False)[0]

        return armCage

    def __createLegCage(self):
        lt_leg_guide = [pm.PyNode(n) for n in self.GUIDES['lt_leg']]
        rt_leg_guide = [pm.PyNode(n) for n in self.GUIDES['rt_leg']]

        lt_legCage = SkinCage.createPolygon(lt_leg_guide, sub_edges=4)
        rt_legCage = SkinCage.createPolygon(rt_leg_guide, sub_edges=4)

        cmds.polyNormal(lt_legCage.name(), normalMode=0, userNormalMode=0, ch=0)

        for leg in [lt_legCage, rt_legCage]:
            SkinCage.insertEdgesLoop(leg.name() + '.e[4]', weight=0.9)
            SkinCage.insertEdgesLoop(leg.name() + '.e[89]', weight=0.1)
            SkinCage.insertEdgesLoop(leg.name() + '.e[99]', weight=0.9)
            SkinCage.pDeleteEdgesLoop(leg.name() + '.e[34]')

        legCage = pm.polyUnite([lt_legCage, rt_legCage], ch=False)[0]

        return legCage

    def __createFoot(self):
        footCages = []
        for side in 'lr':
            leg_guide = pm.PyNode(self.GUIDES[side+'t_leg'][-1])
            foot_guide = [ pm.PyNode(n) for n in self.GUIDES[side+'t_foot'] ]

            leg_pos = [ cv.getPosition(space='world') for cv in leg_guide.getShape().cv ]
            heel_pos = [ cv.getPosition(space='world') for cv in foot_guide[0].getShape().cv ]

            # heel cage
            leg_crv = pm.curve(p=leg_pos[2:] + [leg_pos[0]], d=1)
            heel_crv = pm.curve(p=heel_pos[2:] + [heel_pos[0]], d=1)
            heelCage = SkinCage.createPolygon([leg_crv, heel_crv], sub_edges=1)
            if side == 'l':
                cmds.polyNormal(heelCage.name(), normalMode=0, userNormalMode=0, ch=0)
            footCages.append(heelCage)
            pm.delete(leg_crv, heel_crv)

            # heel cap
            heelCap = SkinCage.createPolygonCap(foot_guide[0])
            footCages.append(heelCap)
            if side == 'l':
                cmds.polyNormal(heelCap, normalMode=0, userNormalMode=0, ch=0)

            # foot
            pos1 = leg_pos[:3]
            pos2 = heel_pos[:3]
            pos2.reverse()
            crv = pm.curve(p = pos1 + pos2, d=1)
            pm.closeCurve(crv, ch=False, ps=1, rpo=1, bb=0.5, bki=0, p=0.1)
            footCage = SkinCage.createPolygon([crv] + foot_guide[1:], sub_edges=1)
            footCages.append(footCage)
            pm.delete(crv)
            if side == 'l':
                cmds.polyNormal(footCage.name(), normalMode=0, userNormalMode=0, ch=0)

            SkinCage.insertEdgesLoop(footCage.name() + '.e[16]', weight=0.9)
            SkinCage.insertEdgesLoop(footCage.name() + '.e[6]', weight=0.1)
            SkinCage.pDeleteEdgesLoop(footCage.name() + '.e[7]')

            # toe
            pos = [ cv.getPosition(space='world') for cv in foot_guide[-1].cv ]
            pos1 = pos[:3]
            pos2 = pos[3:]
            pos2.reverse()
            crvs = [ pm.curve(p=p, d=1) for p in (pos1, pos2) ]
            toeCage = SkinCage.createPolygon(crvs, sub_edges=1)
            footCages.append(toeCage)
            pm.delete(crvs)
            if side == 'l':
                cmds.polyNormal(toeCage.name(), normalMode=0, userNormalMode=0, ch=0)

        footCages = pm.polyUnite(footCages, ch=False)[0]
        pm.polyMergeVertex(footCages, d=0.1, am=1, ch=False)

        return footCages

    def __createHands(self):
        allCages = []
        for side in 'lr':
            arm_guide = pm.PyNode(self.GUIDES[side + 't_arm'][-1])
            hand_guide = [pm.PyNode(n) for n in self.GUIDES[side + 't_hand']]
            fingers_guide = [[pm.PyNode(f) for f in fng] for fng in self.GUIDES[side + 't_fingers']]

            # create palm cage
            palmCage = SkinCage.createPolygon([arm_guide] + hand_guide, sub_edges=1)
            if side == 'l':
                cmds.polyNormal(palmCage.name(), normalMode=0, userNormalMode=0, ch=0)
            SkinCage.pPolySplit(palmCage.name(), edges=[(23, 0.5), (24, 0.5)])
            SkinCage.pPolySplit(palmCage.name(), edges=[(3, 0.5), (1, 0.5)])
            SkinCage.pPolySplit(palmCage.name(), edges=[(7, 0.5), (5, 0.5)])
            SkinCage.pPolySplit(palmCage.name(), edges=[(38, 0.5), (39, 0.5)])
            pm.delete([palmCage.f[x] for x in (3, 4)])
            allCages.append(palmCage)

            # create finger base
            hand_guide = [pm.PyNode(n) for n in self.GUIDES[side + 't_hand']]
            basePos = [ cv.getPosition(space='world') for cv in hand_guide[-1].getShape().cv ]
            basePos.insert(3, SkinCage.createPosBetween(basePos[2], basePos[3]))
            basePos.insert(5, SkinCage.createPosBetween(basePos[4], basePos[5]))
            basePos.insert(9, SkinCage.createPosBetween(basePos[8], basePos[9]))
            basePos.append(SkinCage.createPosBetween(basePos[0], basePos[-1]))
            midPos = [ SkinCage.createPosBetween(basePos[x], basePos[y]) for x, y in zip((3,4,5),(11,10,9))]

            # create fingers cage
            finger1Pos = basePos[0:4] + [midPos[0]] + [basePos[-1]]
            finger2Pos = [basePos[-1]] + [midPos[0]] + basePos[3:5] + [midPos[1]] + [basePos[10]]
            finger3Pos = [basePos[10]] + [midPos[1]] + basePos[4:6] + [midPos[2]] + [basePos[9]]
            finger4Pos = [basePos[9]] + [midPos[2]] + basePos[5:9]
            fingerBase = []
            for pos in [finger1Pos, finger2Pos, finger3Pos, finger4Pos]:
                crv = pm.curve(p=pos, d=1)
                pm.closeCurve(crv, ch=False, ps=1, rpo=1, bb=0.5, bki=0, p=0.1)
                fingerBase.append(crv)
            fingerCages = []
            for x, fingers in enumerate(fingers_guide[1:]):
                curves = [fingerBase[x]] + fingers
                for crv in curves: pm.rebuildCurve(crv, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=1, kep=1, kt=0, s=4, d=1, tol=0.0001)
                fingerCage = SkinCage.createPolygon(curves, sub_edges=1)
                fingerCages.append(fingerCage)
                SkinCage.pPolyBevel(fingerCage.name()+'.e[10]', offset=0.05, loop=True)
                SkinCage.pPolyBevel(fingerCage.name()+'.e[7]', offset=0.05, loop=True)
                SkinCage.insertEdgesLoop(fingerCage.name()+'.e[31]', weight=0.1)
                if side == 'l':
                    cmds.polyNormal(fingerCage.name(), normalMode=0, userNormalMode=0, ch=0)
            pm.delete(fingerBase)
            allCages += fingerCages

            # finger0 cage
            pos1 = [ cv.getPosition(space='world') for cv in arm_guide.getShape().cv ][0:3]
            pos2 = [ cv.getPosition(space='world') for cv in hand_guide[0].getShape().cv ][0:3]
            pos2.reverse()
            finger0base = pm.curve(p=pos1+pos2, d=1)
            pm.closeCurve(finger0base, ch=False, ps=1, rpo=1, bb=0.5, bki=0, p=0.1)
            finger0Cage = SkinCage.createPolygon([finger0base] + fingers_guide[0], sub_edges=1)
            SkinCage.pPolyBevel(finger0Cage.name() + '.e[10]', offset=0.05, loop=True)
            SkinCage.pPolyBevel(finger0Cage.name() + '.e[7]', offset=0.05, loop=True)
            # SkinCage.insertEdgesLoop(finger0Cage.name() + '.e[31]', weight=0.5)
            if side == 'l':
                cmds.polyNormal(finger0Cage.name(), normalMode=0, userNormalMode=0, ch=0)
            pm.delete(finger0base)
            allCages.append(finger0Cage)

            # create finger cap
            fingerCaps = []
            for fingers in fingers_guide:
                capCrv = fingers[-1]
                p1 = [ cv.getPosition(space='world') for cv in capCrv.getShape().cv ][0:3]
                p2 = [ cv.getPosition(space='world') for cv in capCrv.getShape().cv ][3:]
                p2.reverse()
                crv = [ pm.curve(p=p, d=1) for p in (p1,p2)]
                cap = SkinCage.createPolygon(crv, sub_edges=1)
                fingerCaps.append(cap)
                if side == 'l':
                    cmds.polyNormal(cap.name(), normalMode=0, userNormalMode=0, ch=0)
                pm.delete(crv)
            allCages += fingerCaps

        handsCage = pm.polyUnite(allCages, ch=False, n='Hands_Cage')[0]
        pm.polyMergeVertex(handsCage, d=0.01, am=1, ch=False)

        return handsCage

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
    def createPolygonCap(curve):
        curve = pm.PyNode(curve)
        cvs = curve.cv
        div = len(cvs) / 4
        pos1 = [ cv.getPosition(space='world') for cv in cvs[0:div] ]
        pos2 = [ cv.getPosition(space='world') for cv in cvs[div:(div*2)] ]
        pos3 = [ cv.getPosition(space='world') for cv in cvs[(div*2):(div*3)] ]
        pos4 = [ cv.getPosition(space='world') for cv in cvs[(div*3):] ] + [pos1[0]]
        birailCurves = [pm.curve(p=pos, d=1) for pos in [pos1, pos3, pos2, pos4]]

        cap = SkinCage.pBirail(birailCurves, 1, 1)
        pm.delete(birailCurves)

        return cap

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
    def pPolySplit(mesh, edges=[]):
        # edges ex: ([1618, 0], [1619, 0.5])
        cmds.polySplit(mesh, ch=False, s=1, sma=0, ief=0, insertpoint=edges)

    @staticmethod
    def pPolyBevel(edge, offset=0.2, loop=True, segments=1):
        cmds.select(edge)
        if loop:
            cmds.SelectEdgeLoopSp()
        cmds.polyBevel(offset=offset, segments=segments, ch=False)

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
    def pDeleteEdgesLoop(edge):
        cmds.select(edge)
        cmds.SelectEdgeLoopSp()
        cmds.polyDelEdge(cv=True, ch=False)

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

    @staticmethod
    def createPosBetween(posStart=None, posEnd=None, ratio=0.5):
        pos1 = posStart
        pos2 = posEnd
        if hasattr(pos1, 'getTranslation'):
            pos1 = pos1.getTranslation(space='world')
        elif hasattr(pos1, 'getPosition'):
            pos1 = pos1.getPosition(space='world')
        else:
            pos1 = pm.dt.Point(pos1)

        if hasattr(pos2, 'getTranslation'):
            pos2 = pos2.getTranslation(space='world')
        elif hasattr(pos2, 'getPosition'):
            pos2 = pos2.getPosition(space='world')
        else:
            pos2 = pm.dt.Point(pos2)

        grp = pm.group(em=True)
        loc = pm.spaceLocator()
        loc.setParent(grp)

        vec = pos2 - pos1
        length = vec.length()
        vec.normalize()

        position = vec * (length * ratio)

        loc.setTranslation(position, space='world')
        grp.setTranslation(pos1)

        positionResult = loc.getTranslation(space='world')
        pm.delete(grp)

        return positionResult

def run():
    if cmds.objExists('Human_Cage'):
        cmds.delete('Human_Cage')
    scg = SkinCage()
    scg.createHumanCage()
    # scg.createPolygonCap('lt_foot_1_guide')

if __name__ == '__main__':
    run()