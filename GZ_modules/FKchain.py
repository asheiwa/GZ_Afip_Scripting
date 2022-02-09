from maya import cmds
from maya.api.OpenMaya import MGlobal

from GZ_utils import xformUtils as xfm

class FkChain(object):
    def __init__(self, **kwargs):
        self.ctrl    = kwargs['ctrl'] if kwargs.has_key('ctrl') else None
        self.joints  = kwargs['joints'] if kwargs.has_key('joints') else None
        self.suffix  = kwargs['suffix'] if kwargs.has_key('suffix') else None
        self.replace = kwargs['replace'] if kwargs.has_key('replace') else None

        self.fkControls = []

        self.build()

    def build(self):
        if not self.ctrl or not self.joints:
            return MGlobal.displayInfo('Please define ctrl and joints.')

        self.fkControls = []
        for jnt in self.joints:
            c = cmds.duplicate(self.ctrl)[0]
            if self.replace: c = cmds.rename(c, jnt.replace(self.replace[0], self.replace[1]))
            if self.suffix: c = cmds.rename(c, '{}_{}'.format(jnt,self.suffix))
            mtx = cmds.xform(jnt, q=True, m=True, ws=True)
            cmds.xform(c, m=mtx, ws=True)
            xfm.addOffset(c)
            self.fkControls.append(c)

        # parenting
        for x in range(len(self.fkControls)):
            if x != 0:
                offset = xfm.getParent(self.fkControls[x])
                parent = self.fkControls[x-1]
                cmds.parent(offset, parent)

        # constraint
        for c, j in zip(self.fkControls, self.joints):
            cmds.parentConstraint(c, j, mo=False)

    def __str__(self):
        return "{self.__class__.__name__}: '{self.fkControls}'".format(self=self)


def run():
    joints = cmds.ls('fml_un_R_cape*')
    fkchain = FkChain(joints=joints, ctrl='temp_ctrl', replace=['_un','_ac'], suffix='FK')
    print(fkchain)

if __name__ == '__main__':
    run()



