import maya.api.OpenMaya as om


# check name confliction
def check_names_conflicted():
    selection_list.add('*')
    all_nodes = selection_list.getSelectionStrings()
    name_conflict = [n for n in all_nodes if '|' in n]
    if name_conflict:
        cmds.select(name_conflict)
        om.MGlobal.displayWarning('There are {0} nodes\'s name conflicted.'.format(len(name_conflict)))
    else:
        om.MGlobal.displayInfo('All node\'s names are unique.')


check_names_conflicted()







