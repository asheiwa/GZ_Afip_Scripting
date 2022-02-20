from maya import cmds
from maya import OpenMaya
from ngSkinTools2 import  api
from ngSkinTools2.api import init_layers, Layers

def getNgSkinNode(skinCluster):
    ngNode = [ node for node in cmds.listConnections(skinCluster) if cmds.nodeType(node) == 'ngst2SkinLayerData']
    return ngNode[0] if ngNode else None

def hasNgSkinNode(skinCluster):
    return False if getNgSkinNode(skinCluster) == None else True

def initNgSkin(skincluster):
    layers = init_layers(skincluster)
    if not layers.list():
        layers.add("base weights")

    return  layers

def copySkin(source=None, target=None, vertexID=False):
    sel = cmds.ls(sl=True)
    if len(sel) == 2: source, target = sel
    if not source or not target:
        return OpenMaya.MGlobal.displayInfo('Please select skinned source mesh and then target mesh to copy the skin.')

    # get source skinCluster
    sclstSrc = api.target_info.get_related_skin_cluster(source)
    influSrc = cmds.skinCluster(sclstSrc, q=True, influence=True)

    # get target skinCluster
    sclstTgt = api.target_info.get_related_skin_cluster(target)
    if not sclstTgt:
        sclstTgt = cmds.skinCluster(influSrc, target, tsb=True)[0]
        sclstTgt = cmds.rename(sclstTgt, 'sclst_'+target)
    influTgt = cmds.skinCluster(sclstTgt, q=True, influence=True)
    print('influTgt :', influTgt)

    # make sure all source influences added to skinCluster target
    notAdded = [ influ for influ in influSrc if influ not in influTgt ]
    for influ in notAdded:
        cmds.skinCluster(sclstTgt, edit=True, addInfluence=influ, weight=0)

    # init ng in source
    isSourceHasNg = hasNgSkinNode(sclstSrc)
    if not isSourceHasNg:
        initNgSkin(sclstSrc)

    # transfer layer
    infl_config = api.InfluenceMappingConfig.transfer_defaults()
    infl_config.use_label_matching = False
    infl_config.use_distance_matching = True
    infl_config.use_name_matching = False
    useVertexId = api.VertexTransferMode.vertexId if vertexID else api.VertexTransferMode.closestPoint
    api.transfer_layers(source, target, vertex_transfer_mode=useVertexId, influences_mapping_config=infl_config)

    # clean up
    cmds.delete(getNgSkinNode(sclstTgt))
    if not isSourceHasNg:
        cmds.delete(getNgSkinNode(sclstSrc))
    cmds.select(target)

    OpenMaya.MGlobal.displayInfo('Skin copied.')
