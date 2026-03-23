
def classFactory(iface):  # pylint: disable=invalid-name
    """Load VWorld class from file VWorld.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .v_world import VWorld
    return VWorld(iface)
