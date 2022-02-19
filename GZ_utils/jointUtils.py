import math

from maya import cmds
import maya.mel as mel
import pymel.core as pm
from maya import OpenMaya as om

from GZ_utils import xformUtils as xfm

def selectJoints(filter=None):
    '''Select all joints under selected node.'''
    cmds.select(hi=True)
    bind = cmds.ls(sl=True, type='joint')
    bind = [ b for b in bind if cmds.listRelatives(b, c=True, type='joint') ]
    if filter:
        bind = [ b for b in bind if filter not in b ]
    cmds.select(bind)
    if not bind:
        om.MGlobal.displayInfo('Select an object to select all joints children.')

def alignJoints(joints=None, upTarget=None, vis=True, primaryAxis='x', aimOneByOne=False, mirror=False):
    """
    This function to align axis of joint chain
    @param joints: list of PyNode Joint
    @param upTarget: PyNode transform
    @param vis: Bool, vector visual aid on creation
    @param primaryAxis: axis used for aim to child joint. only "x" and "y" for now.
    """
    currentSelected = pm.selected()

    joints = joints or currentSelected
    if type(upTarget) == str and pm.objExists(upTarget):
        upT = pm.PyNode(upTarget)
    else:
        upT = upTarget

    if not upTarget and len(joints) < 3: return '<< UP TARGET IS NEEDED FOR UP AXIS >>'

    compareVec = None
    for x, jnt in enumerate(joints[0:(len(joints) - 1)]):
        # for x, jnt in enumerate(joints[0:2]):
        if type(upTarget) == list:
            if not aimOneByOne:
                # print '>> aim to closest'
                upT = xfm.getClosestTransform(jnt, upTarget)
            else:
                if x < len(upTarget):
                    upT = upTarget[x]
                else:
                    upT = None
                # print '>> aim one by one : {0} --> {1}'.format(jnt, upT)

        # get parent and children
        par = jnt.getParent()
        childs = jnt.getChildren()

        # get up opp target
        if upT != None:
            oppTarget = upT
        elif par:
            oppTarget = par
        else:
            oppTarget = joints[2]

        # unparent joint and its children, and get aim target
        aimTarget = None
        jnt.setParent(w=True)
        for c in childs:
            c.setParent(w=True)
            if type(c) == pm.nt.Joint:
                aimTarget = c

        # print jnt, oppTarget, aimTarget

        # obtain jnt position
        pos = jnt.getTranslation(space='world')
        if primaryAxis == 'x':
            # xVec
            xVec = aimTarget.getTranslation(space='world') - pos
            if mirror: xVec = pos - aimTarget.getTranslation(space='world')
            if vis: xfm.vectorVis(xVec, jnt, 'xVec')
            # oppVec
            oppVec = oppTarget.getTranslation(space='world') - pos
            if mirror: oppVec = pos - oppTarget.getTranslation(space='world')
            if vis: xfm.vectorVis(oppVec, jnt, 'oppVec')
            # check paralel
            if xVec.isParallel(oppVec):
                if par: jnt.setParent(par)
                if childs: pm.parent(childs, jnt)
                return '<< UP TARGET IS NEEDED FOR UP AXIS >>'
            # zVec
            yVec = oppVec.cross(xVec)
            if compareVec and 0 > yVec.dot(compareVec): yVec = xVec.cross(oppVec)  # to force up axis the same
            compareVec = yVec
            if vis: xfm.vectorVis(yVec, jnt, 'yVec')
            # yVec
            zVec = yVec.cross(xVec)
            if vis: xfm.vectorVis(zVec, jnt, 'zVec')

        elif primaryAxis == 'y':
            # yVec
            yVec = aimTarget.getTranslation(space='world') - pos
            if mirror: yVec = pos - aimTarget.getTranslation(space='world')
            if vis: xfm.vectorVis(yVec, jnt, 'yVec')
            # oppVec
            oppVec = oppTarget.getTranslation(space='world') - pos
            if mirror: oppVec = pos - oppTarget.getTranslation(space='world')
            if vis: xfm.vectorVis(oppVec, jnt, 'oppVec')
            # check paralel
            if yVec.isParallel(oppVec):
                if par: jnt.setParent(par)
                if childs: pm.parent(childs, jnt)
                return '<< UP TARGET IS NEEDED FOR UP AXIS >>'
            # xVec
            xVec = yVec.cross(oppVec)
            if compareVec and 0 > xVec.dot(compareVec): xVec = oppVec.cross(yVec)  # to force up axis the same
            compareVec = xVec
            if vis: xfm.vectorVis(xVec, jnt, 'xVec')
            # zVec
            zVec = yVec.cross(xVec)
            if vis: xfm.vectorVis(zVec, jnt, 'zVec')
        else:
            return 'only "x" and "y" accepted.'

        # create matrix
        jntM = pm.dt.Matrix(xVec, yVec, zVec, pos).homogenize()
        jnt.setMatrix(jntM)

        # reparent all
        if par: jnt.setParent(par)
        pm.makeIdentity(jnt, apply=True, t=False, r=True, s=False, jo=False, n=False)
        if childs:
            pm.parent(childs, jnt)

    joints[-1].jointOrient.set(0, 0, 0)

    pm.select(cl=True)
    if currentSelected: pm.select(currentSelected)



# Create Joints by on curves
def createByCurves(curves=None, name='jntCrv', num=5, upTarget=None, primaryAxis='x', aimOneByOne=False, mirror=False):
    ''' create joint by curves ( must list of PyNode curve) '''

    curves = curves or pm.selected()
    curvesList = []

    if not curves:
        print("There's no selected nurbs curve's and curves argument is 'None'.")
        return

    if type(upTarget) == str and not pm.objExists(upTarget):
        print("There's no locator or transform named {0} for up target.".format(upTarget))
        return

    if type(curves) == str and pm.objExists(curves):
        curvesList = [pm.PyNode(curves)]
    elif type(curves) == list:
        for c in curves:
            if pm.objExists(c): curvesList.append(pm.PyNode(c))
    elif type(curves) == pm.nt.Transform:
        curvesList = [curves]

    finalCurvesList = []
    for c in curvesList:
        if type(c.getShape()) == pm.nt.NurbsCurve:
            finalCurvesList.append(c)

    div = (1.0 / num)
    finalJointList = []
    for crv in finalCurvesList:
        pm.select(cl=True)
        # start create joint chain
        joints = []
        for x in range(num + 1):
            pos = pm.pointOnCurve(crv, pr=(x * div), p=True, turnOnPercentage=True)
            jnt = pm.joint(position=pos, radius=0.5, n=name)
            joints.append(jnt)
            finalJointList.append(jnt)

        # if upTarget is define
        alignJoints(joints, upTarget, False, primaryAxis, aimOneByOne, mirror)

        pm.select(cl=True)

    return finalJointList
