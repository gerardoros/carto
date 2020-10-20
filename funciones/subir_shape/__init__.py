# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SubirShape
                                 A QGIS plugin
 Modulo para subir shp a postgres
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2020-09-09
        copyright            : (C) 2020 by Oliver
        email                : foo@bar.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load SubirShape class from file SubirShape.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .subir_shape import SubirShape
    return SubirShape(iface)
