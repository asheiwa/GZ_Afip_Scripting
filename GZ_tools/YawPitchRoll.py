import pymel.core as pm

"""
Create Yaw Pitch Roll
"""
class Create_YawPitchRoll:
    ypr_atr = ["yaw", "pitch", "roll"]
    yap_rotOrd = {'x':5, 'y':2, 'z':0}
    allAxis = ['x', 'y', 'z']
    
    def __init__(self, obj, roll='x'):
        self.Entity = pm.PyNode(obj)
        self._parent = obj.getParent()
        self._rollAx = None
        if pm.listAttr(obj, st="hasYPR"):
            self.fromSelection(obj)
        else:
            self.settingUp_rollAx(roll)
            self.gettingReady()
            self.makingRoll()
            self.making_quatNormalize()
            self.making_quatInvert()
            self.makingYawPitch()
            
    def fromSelection(self, obj):
        self._rollAx = obj.rollAxis.get()
        self.Loc = self.Entity.YPR_loc.get()
        self.LocParent = self.Loc.getParent()
        self.rollDecompose = self.Loc.rollDecompose.get()
        self.multMatRoll = self.Loc.multMatRoll.get()
    
    def delete_YPR(self):
        self.Entity.rollAxis.set(l=0)
        self.Entity.hasYPR.set(l=0)
        self.Entity.deleteAttr("rollAxis")
        self.Entity.deleteAttr("hasYPR")
        self.Entity.deleteAttr("YPR_loc")
        pm.delete(self.rollDecompose)
        pm.delete(self.multMatRoll )
        ### delete all conncetion to yaw pitch roll first
        for y in self.ypr_atr:
            cons = self.Loc.attr(y).listConnections(s=False, d=True, p=True)
            if cons:
                for c in cons:
                    self.Loc.attr(y) // c
        pm.delete(self.LocParent)
        
    def settingUp_rollAx(self, rollAx):
        self.Entity.addAttr("rollAxis", dt="string")
        self.Entity.rollAxis.set(rollAx)
        self._rollAx = rollAx
        self.Entity.rollAxis.set(l=1)
        
    def gettingReady(self):
        ### getting ready
        self.Entity.addAttr("hasYPR", at="bool")
        self.Entity.hasYPR.set(1)
        self.Entity.hasYPR.set(l=True)
        self.LocParent = pm.group(n="{}_YPRLocGp".format(self.Entity.name()), em=True)
        self.Loc = pm.spaceLocator(n="{}_YPRLoc".format(self.Entity.name()))
        for y in self.ypr_atr:
            self.Loc.addAttr(y, at="double")
            self.Loc.attr(y).set(cb=True)
            self.Loc.attr(y).set(k=True)
        pm.delete(pm.parentConstraint(self.Entity, self.LocParent, mo=False))
        pm.delete(pm.parentConstraint(self.Entity, self.Loc, mo=False))
        self.Loc.setParent(self.LocParent)
        pm.parentConstraint(self._parent, self.LocParent, mo=True)
        pm.parentConstraint(self.Entity, self.Loc, mo=False)
        self.Entity.addAttr("YPR_loc", at="message")
        self.Loc.message >> self.Entity.YPR_loc
        
    def makingRoll(self):
        ### making the Roll
        self.rollDecompose = pm.createNode("decomposeMatrix", n="{}_decomRoll".format(self.Entity.name()))
        self.quatEulRoll = pm.createNode("quatToEuler", n="{}_quatEulRoll".format(self.Entity.name()))
        self.quatInvRoll = pm.createNode("quatInvert", n="{}_quatInvertRoll".format(self.Entity.name()))
        self.quatToEulRollInv = pm.createNode("quatToEuler", n="{}_quatToEulRollInv".format(self.Entity.name()))
        self.composeMatRoll = pm.createNode("composeMatrix", n="{}_composeMatRoll".format(self.Entity.name()))
        self.multMatRoll = pm.createNode("multMatrix", n="{}_multMatRoll".format(self.Entity.name()))
        rotOr = self.yap_rotOrd[self._rollAx]
        self.quatEulRoll.inputRotateOrder.set(rotOr)
        self.quatToEulRollInv.inputRotateOrder.set(rotOr)

        quatAx = self._rollAx.upper()
        self.Loc.matrix >> self.rollDecompose.inputMatrix
        self.rollDecompose.outputQuatW >> self.quatEulRoll.inputQuatW
        self.rollDecompose.attr("outputQuat{}".format(quatAx)) >> self.quatEulRoll.attr("inputQuat{}".format(quatAx))

        self.rollDecompose.outputQuatW >> self.quatInvRoll.inputQuatW
        self.rollDecompose.attr("outputQuat{}".format(quatAx)) >> self.quatInvRoll.attr("inputQuat{}".format(quatAx))

        self.quatInvRoll.outputQuat >> self.quatToEulRollInv.inputQuat
        self.quatInvRoll.outputQuat >> self.composeMatRoll.inputQuat
        self.quatToEulRollInv.outputRotate >> self.composeMatRoll.inputRotate

        self.composeMatRoll.outputMatrix >> self.multMatRoll.matrixIn[0]
        self.Loc.matrix >> self.multMatRoll.matrixIn[1]

        self.quatEulRoll.attr("outputRotate{}".format(quatAx)) >> self.Loc.roll

        self.Loc.addAttr("rollDecompose", at="message")
        self.Loc.addAttr("multMatRoll", at="message")
        self.rollDecompose.message >> self.Loc.rollDecompose
        self.multMatRoll.message >> self.Loc.multMatRoll
    
    def making_quatNormalize(self):
        self.normalizeDecompose = pm.createNode("decomposeMatrix", n="{}_decomNormalize".format(self.Entity.name()))
        self.quatNormalize = pm.createNode("quatNormalize", n="{}_quatNormalize".format(self.Entity.name()))
        self.multMatRoll.matrixSum >> self.normalizeDecompose.inputMatrix
        self.normalizeDecompose.outputQuat >> self.quatNormalize.inputQuat
    
    def making_quatInvert(self):
        axisUsed = [x for x in self.allAxis if self._rollAx not in x]
        axisUsedCap = [x.upper() for x in axisUsed]
        self.quatInv = []
        self.quatProd = []
        for a, cap in zip(axisUsed, axisUsedCap):
            quatInv = pm.createNode("quatInvert", n="{}_quatInvertYPR{}".format(self.Entity.name(), cap))
            self.quatNormalize.attr("outputQuat{}".format(cap)) >> quatInv.attr("inputQuat{}".format(cap))
            self.quatNormalize.outputQuatW >> quatInv.inputQuatW
            quatProd = pm.createNode("quatProd", n="{}_quatProdYPR{}".format(self.Entity.name(), cap))
            self.quatNormalize.outputQuat >> quatProd.input2Quat
            quatInv.outputQuat >> quatProd.input1Quat
            self.quatInv.append(quatInv)
            self.quatProd.append(quatProd)
        self.quatProd.reverse()
    
    def makingYawPitch(self):
        axisUsed = [x for x in self.allAxis if self._rollAx not in x]
        self.quatEulYaw = pm.createNode("quatToEuler", n="{}_quatEulYaw".format(self.Entity.name()))
        self.quatEulPitch = pm.createNode("quatToEuler", n="{}_quatEulPitch".format(self.Entity.name()))
        yawOr = self.yap_rotOrd[axisUsed[0]]
        pitchOr = self.yap_rotOrd[axisUsed[1]]
        self.quatEulYaw.inputRotateOrder.set(yawOr)
        self.quatEulPitch.inputRotateOrder.set(pitchOr)
        
        quatEuls = [self.quatEulYaw, self.quatEulPitch]
        axisUsed = [x.upper() for x in axisUsed]
        
        for a, q, quatProd in zip(axisUsed, quatEuls, self.quatProd):
            quatProd.attr("outputQuat{}".format(a)) >> q.attr("inputQuat{}".format(a))
            quatProd.outputQuatW >> q.inputQuatW
        
        self.quatEulYaw.attr("outputRotate{}".format(axisUsed[0])) >> self.Loc.yaw
        self.quatEulPitch.attr("outputRotate{}".format(axisUsed[1])) >> self.Loc.pitch