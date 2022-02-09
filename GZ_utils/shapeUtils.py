from maya import cmds

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
    color = COLORS[color] if COLORS.has_key(color) else color
    shapes = cmds.listRelatives(node, shapes=True)

    for shape in shapes:
        cmds.setAttr('{}.overrideEnabled'.format(shape), True)
        cmds.setAttr('{}.overrideColor'.format(shape), color)