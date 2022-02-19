from maya import cmds
import pymel.core as pm

COLORS = dict(gray=2, grayLight=3, white=16,
              yellow=17, yellowLighter=22,
              blue=6, blueDark=5, bluePale=28, blueLighter=29, blueNavi=15, blueSky=18,
              red=13, redDark=4,
              green=7, greenLime=26, greenPale=27, greenLight=25, greenLighter=23, greenNeon=14, greenNeonLite=19,
              purple=30, purpleDark=8, purpleLight=31, purpleNeon=9,
              brown=12, brownDark=11, brownLight=10, brownLighter=24,
              peach=20, skin=21)

def setColor(node, color):
    ''' Set color of the controller.'''
    try:
        color = COLORS[color] if COLORS.has_key(color) else color
    except:
        color = COLORS[color] if color in COLORS else color
    shapes = cmds.listRelatives(node, shapes=True)

    for shape in shapes:
        cmds.setAttr('{}.overrideEnabled'.format(shape), True)
        cmds.setAttr('{}.overrideColor'.format(shape), color)

def parentCurveShape(sel = None, replace=False, keepOriginal=True):
    '''Parent curve's shapes to new transform.'''
    selected = sel or pm.selected()
    tgt = selected.pop(-1)

    if replace: pm.delete(tgt.getShapes())

    if keepOriginal:
        dups = []
        for s in selected:
            dup = pm.duplicate(s, rr=True)[0]
            pm.delete([chd for chd in dup.getChildren() if chd.type() == 'transform' or chd.type() == 'joint'])
            dups.append(dup)
        selected = dups

    data = {}
    for s in selected:
        for shape in s.getShapes():
            data[shape] = [ cv.getPosition(space='world') for cv in shape.cv ]
            pm.parent(shape, tgt, shape=True, r=True)
            shape.rename(tgt.name() + 'Shape')

    # force in place
    for shape, pos in data.items():
        for x, p in enumerate(pos):
            pm.move(shape.cv[x], p, a=True, ws=True)

    pm.delete(selected)