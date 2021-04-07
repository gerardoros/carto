# -*- coding: utf-8 -*-
"""
/***************************************************************************
 gen_doc_calvecat
                                 A QGIS plugin
 gen_doc_calvecat
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-12-11
        git sha              : $Format:%H$
        copyright            : (C) 2020 by 1
        email                : 1
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QDate, QRegExp
from qgis.PyQt.QtGui import QIcon, QIntValidator, QRegExpValidator
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .gen_doc_calvecat_dialog import gen_doc_calvecatDialog
import os.path
import requests
import json
import re
from qgis.core import *



class gen_doc_calvecat:
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
        self.dlg = gen_doc_calvecatDialog(parent = iface.mainWindow())
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'gen_doc_calvecat_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&gen_doc_calvecat')
        self.abrePredio6 = False
        self.directorioAGuardar6 = None
        self.cve_catastral6 = None

        self.canvas = iface.mapCanvas()

        # eventos
        self.dlg.btnBrowse_5.clicked.connect(self.selectDirectory5)
        self.dlg.btnGenerar_5.clicked.connect(self.generarDoc5)
        self.dlg.btnSeleccionar_5.clicked.connect(self.activarSeleccion5)
        self.dlg.exit_signal.connect(self.closeEvent)

        self.dlg.fldCveCat_5.textChanged.connect(self.lineEditToUpper5)

        #validaciones
        rx = QRegExp("[a-zA-Z0-9]{31}")
        val = QRegExpValidator(rx)
        self.dlg.fldCveCat_5.setValidator(val)

        self.onlyInt = QIntValidator()
        self.dlg.fldNomfolio.setValidator(self.onlyInt)
        self.onlyInt = QIntValidator()
        self.dlg.fldCodPostal.setValidator(self.onlyInt)

        
        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        

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
        return QCoreApplication.translate('gen_doc_calvecat', message)


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

        icon_path = ':/plugins/gen_doc_calvecat/icon.png'
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
                self.tr(u'&gen_doc_calvecat'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        self.obtenerXCapas5()

        self.xManzana.selectionChanged.connect(self.seleccionaClave5)
        self.xPredGeom.selectionChanged.connect(self.seleccionaClave5)
        self.xPredNum.selectionChanged.connect(self.seleccionaClave5)
        self.xConst.selectionChanged.connect(self.seleccionaClave5)
        self.xHoriGeom.selectionChanged.connect(self.seleccionaClave5)
        self.xHoriNum.selectionChanged.connect(self.seleccionaClave5)
        self.xVert.selectionChanged.connect(self.seleccionaClave5)
        self.xCvesVert.selectionChanged.connect(self.seleccionaClave5)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    def selectDirectory5(self):
        # self.archivo = QtGui.QFileDialog.getOpenFileName(self, 'Abir Archivo')

        options = QFileDialog.Options()
        options |= QFileDialog.Directory
        options |= QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self.dlg, "Elige un directorio", options=options)

        if directory:
            self.directorioAGuardar6 = directory
            self.dlg.fldDirectorio_5.setText(directory)


    def generarDoc5(self):
        #
        cve_catastral6 = str(self.dlg.fldCveCat_5.text())
        nom_folio = str(self.dlg.fldNomfolio.text())
        dom_notificaciones = str(self.dlg.fldDomNoti.text())
        area = str(self.dlg.fldAreaApro.text()) 
        colonia = str(self.dlg.fldColPredio.text())
        codigo = str(self.dlg.fldCodPostal.text())        
       

        if not (cve_catastral6 and nom_folio and dom_notificaciones and area and colonia and codigo and self.directorioAGuardar6):
            self.UTI.mostrarAlerta("Por favor llene los campos.", QMessageBox.Critical,
                               "Constancia de identificacion catastral")
            return


        url = self.CFG.urlManifestacion
        headers = {'Content-Type': 'application/json', 'Authorization': self.UTI.obtenerToken()}

        payload = {"claveCatastral": cve_catastral6,
                    "nombrefolio": nom_folio,
                    "notificaciones": dom_notificaciones,
                    "area": area,
                    "colonia": colonia,
                    "codigo": codigo}

        payload = json.dumps(payload)

        try:
            response = requests.post(url, headers=headers, data=payload)
            d = response.headers['content-disposition']
            fname = re.findall("filename=(.+)", d)[0].strip('"')
            ruta = f"{self.directorioAGuardar6}/{fname}"
            f = open(ruta, 'wb')
            f.write(response.content)
            f.close()
            self.cambiarStatus5("Archivo guardado", "ok")

        except requests.exceptions.RequestException:
            self.UTI.mostrarAlerta("No se ha podido conectar al servidor v1", QMessageBox.Critical,
                                   "Constancia de identificacion catastral")  # Error en la peticion de consulta
        self.cancelaSeleccion5()


    def seleccionaClave5(self):

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
            elif capaActiva.id() == self.ACA.obtenerIdCapa('cves_verticales'):
                features = self.xCvesVert.selectedFeatures()

            if len(features) == 0:
                self.cambiarStatus5("Seleccione una geometria valida", "error")
                self.cancelaSeleccionYRepinta5()
                return
            if len(features) != 1:
                self.cambiarStatus5("Seleccione una sola geometria", "error")
                self.cancelaSeleccionYRepinta5()
                return
            else:
                self.cambiarStatus5("Predio seleccionado", "ok")

                feat = features[0]
                self.cve_catastral6 = feat['cve_cat']
                self.dlg.fldCveCat_5.setText(self.cve_catastral6)
                self.dlg.btnSeleccionar_5.setEnabled(True)
        else:
            self.UTI.mostrarAlerta("Elija una capa.", QMessageBox.Critical,
                                   "Constancia de identificacion catastral")  # Error en la peticion de consulta

    def activarSeleccion5(self):
        if not self.abrePredio6:
            self.iface.actionSelect().trigger()
            self.canvas.setCursor(self.UTI.cursorRedondo)
            self.dlg.btnSeleccionar_5.setEnabled(False)
            self.abrePredio6 = True

    def cancelaSeleccion5(self):
        if self.abrePredio6:
            self.dlg.btnSeleccionar_5.setEnabled(True)
            # regresa herramienta de seleccion normal
            self.iface.actionPan().trigger()
            self.cambiarStatus5("Listo...", "ok")
            self.abrePredio6 = False

    def cancelaSeleccionYRepinta5(self):
        self.dlg.btnSeleccionar_5.setEnabled(True)

        self.xPredGeom.removeSelection()
        self.xHoriGeom.removeSelection()
        self.xCvesVert.removeSelection()
        self.xManzana.removeSelection()
        self.xPredNum.removeSelection()
        self.xConst.removeSelection()
        self.xHoriNum.removeSelection()
        self.xVert.removeSelection()
        self.canvas.refresh()
        # regresa herramienta de seleccion normal
        self.iface.actionPan().trigger()
        self.abrePredio6 = False

    # recibimos el closeEvent del dialog
    def closeEvent(self, msg):
        if msg:
            self.cancelaSeleccionYRepinta5()

    def cambiarStatus5(self, texto, estado):

        self.dlg.lbEstatusCedula_6.setText(texto)

        if estado == "ok":  # abriendo
            self.dlg.lbEstatusCedula_6.setStyleSheet('color: green')
        elif estado == "error":  # Seleccione un solo predio
            self.dlg.lbEstatusCedula_6.setStyleSheet('color: red')
        else:
            self.dlg.lbEstatusCedula_6.setStyleSheet('color: black')


    def lineEditToUpper5(self):
        self.dlg.fldCveCat_5.setText(self.dlg.fldCveCat_5.text().upper())

    def obtenerXCapas5(self):

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
