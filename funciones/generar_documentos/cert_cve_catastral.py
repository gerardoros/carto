# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CertCveCatastral
                                 A QGIS plugin
 Certificado clave catastral
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-11-27
        git sha              : $Format:%H$
        copyright            : (C) 2020 by oliver
        email                : oliver
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QRegExp
from qgis.PyQt.QtGui import QIcon, QRegExpValidator
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .cert_cve_catastral_dialog import CertCveCatastralDialog
import os.path
import json
import requests
import re
from qgis.core import *

class CertCveCatastral:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale

        self.dlg = CertCveCatastralDialog()

        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'CertCveCatastral_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Cert Cve Catastral')
        self.canvas = iface.mapCanvas()

        #eventos
        self.dlg.btnBrowse.clicked.connect(self.selectDirectory)
        self.dlg.btnGenerar.clicked.connect(self.generarDoc)
        self.dlg.btnSeleccionar.clicked.connect(self.activarSeleccion)

        rx = QRegExp("[0-9]{32}")
        val = QRegExpValidator(rx)
        self.dlg.fldCveCat.setValidator(val)


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('CertCveCatastral', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/cert_cve_catastral/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u''),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Cert Cve Catastral'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""
        self.obtenerXCapas()

        self.xManzana.selectionChanged.connect(self.seleccionaClave)
        self.xPredGeom.selectionChanged.connect(self.seleccionaClave)
        self.xPredNum.selectionChanged.connect(self.seleccionaClave)
        self.xConst.selectionChanged.connect(self.seleccionaClave)
        self.xHoriGeom.selectionChanged.connect(self.seleccionaClave)
        self.xHoriNum.selectionChanged.connect(self.seleccionaClave)
        self.xVert.selectionChanged.connect(self.seleccionaClave)
        self.xCvesVert.selectionChanged.connect(self.seleccionaClave)



        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    def selectDirectory(self):
        # self.archivo = QtGui.QFileDialog.getOpenFileName(self, 'Abir Archivo')

        options = QFileDialog.Options()
        options |= QFileDialog.Directory
        options |= QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectoryUrl(self.dlg, "Elige un directorio", options=options)

        if directory:
            self.directorioAGuardar = directory.path()
            self.dlg.fldDirectorio.setText(directory.path())

    def generarDoc(self):

        self.cve_catastral = self.dlg.fldCveCat.text()

        url = self.CFG.urlCertCveCat
        headers = {'Content-Type': 'application/json', 'Authorization': self.UTI.obtenerToken()}
        try:
            response = requests.get(url + self.cve_catastral, headers=headers)
            d = response.headers['content-disposition']
            fname = re.findall("filename=(.+)", d)[0].strip('"')
            ruta = f"{self.directorioAGuardar }/{fname}"
            f = open( ruta, 'wb')
            f.write(response.content)
            f.close()
            self.cambiarStatus("Archivo guardado", "ok")
            return

        except requests.exceptions.RequestException:
            self.UTI.mostrarAlerta("No se ha podido conectar al servidor v1", QMessageBox.Critical,
                                   "Certificacion clave catastral")  # Error en la peticion de consulta
            return



    def activarSeleccion(self):
        self.iface.actionSelect().trigger()
        self.canvas.setCursor(self.UTI.cursorRedondo)
        self.dlg.btnSeleccionar.setEnabled(False)


    def seleccionaClave(self):

        capaActiva = self.iface.activeLayer()
        features = []
        if capaActiva:
            # saber cual capa esta activa, a cual se le dio click
            if capaActiva.id() == self.ACA.obtenerIdCapa('predios.geom'):
                features = self.xPredGeom.selectedFeatures()

                # validar si el predio contiene algun condominio
                condVCve = self.xCvesVert.getFeatures()
                condHori = self.xHoriGeom.getFeatures()

                # -- buscar si el predio seleccionado contiene condominios
                # -* ya sean verticales u horizontales
                for p in features:
                    geomP = p.geometry()

                    # verifica si tiene claves de verticales
                    for cv in condVCve:
                        geom = cv.geometry()
                        if geom.within(geomP):
                            cond = True
                            break

                    # verifica si tiene horizontales
                    for cv in condHori:
                        geom = cv.geometry().buffer(-0.000001, 1)
                        if geom.within(geomP):
                            cond = True
                            break

            elif capaActiva.id() == self.ACA.obtenerIdCapa('horizontales.geom'):
                features = self.xHoriGeom.selectedFeatures()
                cond = True
            elif capaActiva.id() == self.ACA.obtenerIdCapa('cves_verticales'):
                features = self.xCvesVert.selectedFeatures()
                cond = True

            if len(features) == 0:
                self.cambiarStatus("Seleccione una geometria", "error")
                return
            if len(features) != 1:
                self.cambiarStatus("Seleccione una sola geometria", "error")
                return
            else:
                self.cambiarStatus("Predio seleccionado", "ok")

                feat = features[0]
                self.cve_catastral = feat['cve_cat']
                self.dlg.fldCveCat.setText(self.cve_catastral)
                self.dlg.btnSeleccionar.setEnabled(True)
        else:
            self.UTI.mostrarAlerta("Elija una capa.", QMessageBox.Critical,
                                   "Certificacion clave catastral")  # Error en la peticion de consulta


    def cambiarStatus(self, texto, estado):

        self.dlg.lbEstatusCedula.setText(texto)

        if estado == "ok": # abriendo
            self.dlg.lbEstatusCedula.setStyleSheet('color: green')
        elif estado == "error": # Seleccione un solo predio
            self.dlg.lbEstatusCedula.setStyleSheet('color: red')
        else:
            self.dlg.lbEstatusCedula.setStyleSheet('color: black')


    def obtenerXCapas(self):

        # carga las capas en caso de no existir
        # self.UTI.cargarCapaVacio()

        xMan = QSettings().value('xManzana')
        xPredG = QSettings().value('xPredGeom')
        xPredN = QSettings().value('xPredNum')
        xCon = QSettings().value('xConst')
        xHoriG = QSettings().value('xHoriGeom')
        xHoriN = QSettings().value('xHoriNum')
        xVe = QSettings().value('xVert')
        xCv = QSettings().value('xCvesVert')

        self.xManzana = QgsProject.instance().mapLayer(xMan)
        self.xPredGeom = QgsProject.instance().mapLayer(xPredG)
        self.xPredNum = QgsProject.instance().mapLayer(xPredN)
        self.xConst = QgsProject.instance().mapLayer(xCon)
        self.xHoriGeom = QgsProject.instance().mapLayer(xHoriG)
        self.xHoriNum = QgsProject.instance().mapLayer(xHoriN)
        self.xVert = QgsProject.instance().mapLayer(xVe)
        self.xCvesVert = QgsProject.instance().mapLayer(xCv)
