# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Master
                                 A QGIS plugin
 Master
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2018-04-27
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Master
        email                : Master
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
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.utils import iface
from qgis.core import *
# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .Master_dialog import MasterDialog
import os.path, requests, json

from .funciones.configuracion import Configuracion
from .funciones.consulta import ActualizacionCatastralV3
from .funciones.dibujo import DibujoV3
from .funciones.eliminacion import EliminacionV3
from .funciones.topologia import TopologiaV3
from .funciones.utilidades import utilidades
from .funciones.fusiondivision import DivisionFusion
from .funciones.cargamasiva import Integracion

from .funciones.revisioncampo import AsignacionCampo
from .funciones.revisioncampo import AsignacionRevision
from .funciones.revisioncampo import CedulaPadron
from .funciones.revisioncampo import AsignacionPadron
from .funciones.revisioncampo import IntermedioCedulaRevision

from .funciones.asignatareas import AsignaTareas
from .funciones.adminusers import AdminUsers

class Master:
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
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Master_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = MasterDialog(parent = iface.mainWindow())
        self.banderaInicial = True

        var = QSettings()
        if var.value('logeado') == 'True':
            # Declare instance attributes
            self.actions = []
            self.menu = self.tr(u'&Master')
            # TODO: We are going to let the user set this up in a future iteration
            self.toolbar = self.iface.addToolBar(u'Master')
            self.toolbar.setObjectName(u'Master')


        self.CFG = Configuracion.Configuracion()
        self.UTI = utilidades.Utilidad()
        self.UTI.CFG = self.CFG

        self.headers = {'Content-Type': 'application/json'}

        # consulta informacion del usuario logueado
        usuario = self.UTI.decodeRot13(QSettings().value('usuario'))

        resultado = self.consumeWSGeneral(url_cons = self.CFG.url_MA_getInfoUser + str(usuario))

        if not resultado:
            return
        self.dlg.btnAsigTareas.hide()
        var.setValue("datoUsuario", resultado)
        # obtiene todos los permisos del usuario
        # ----- P E N D I E N T E ----

        #self.dlg.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        #self.CFG = Configuracion
        
        # Consulta de cartografia
        self.ACA = ActualizacionCatastralV3.ActualizacionCatastralV3(iface)
        self.UTI.ACA = self.ACA
        
        # Division y fusion
        self.DFS = DivisionFusion.DivisionFusion(iface, self.ACA)
        
        # Dibujo
        self.DBJ = DibujoV3.DibujoV3(iface)
        
        # Eliminacion de geometrias
        self.ELM = EliminacionV3.EliminacionV3(iface)

        # Verificacion de Topologias
        self.TPG = TopologiaV3.TopologiaV3(iface, self.ACA)

        # Integracion (Carga masiva)
        self.CMS = Integracion.Integracion(iface)
        
        # Asignaciones de campo, revision y padron
        self.ASCM = AsignacionCampo.AsignacionCampo(iface, self.UTI)
        self.ASRV = AsignacionRevision.AsignacionRevision(iface, self.UTI)
        self.ASPA = AsignacionPadron.AsignacionPadron(iface, self.UTI)

        # Intermediarios de asignaciones para Padron y gabinete
        self.INTEPAD = IntermedioCedulaRevision.IntermedioCedulaRevision(iface, self, 'PAD')
        self.INTEREV = IntermedioCedulaRevision.IntermedioCedulaRevision(iface, self, 'REV')


        #------------ DESACTIVAMOS LAS OPERACIONES Y MANDAMOS A VERIFICAR SUS ROLES
        self.comproveRoles()
        self.asignActionsByRoles(iface)

        # ------------ EVENTO DE BOTONES -------------
        self.dlg.btnAsigTareas.clicked.connect(self.irAAsignaTareas)
        self.dlg.btnConsulta.clicked.connect(self.irAConsulta)
        self.dlg.btnDibujo.clicked.connect(self.irADibujo)
        self.dlg.btnEliminar.clicked.connect(self.irAEliminar)
        self.dlg.btnTopologia.clicked.connect(self.irATopologia)
        self.dlg.btnFusDiv.clicked.connect(self.irAFusionDivision)
        self.dlg.btnCargaMasiva.clicked.connect(self.irACargaMasiva)
        self.dlg.btnAsigCampo.clicked.connect(self.irAAsignacionCampo)
        self.dlg.btnAsigRev.clicked.connect(self.irAAsignacionRevision)
        self.dlg.btnAsigPad.clicked.connect(self.irAAsignacionPadron)

        self.dlg.btnInterPad.clicked.connect(self.irAIntermediarioPad)
        self.dlg.btnInterRev.clicked.connect(self.irAIntermediarioRev)

        self.dlg.btnAdminUsers.clicked.connect(self.irAAdminUsuarios)
        
        #self.dlg.btnAsigCampo.setEnabled(False)
        #self.dlg.btnAsigRev.setEnabled(False)

    #---------METODO QUE DESABILITA TODAS LAS ACCIONES DE LOS BOTONES
    def comproveRoles(self):

        # ------------ PRUEBA PARA DESHABILITAR LOS BOTONES -------
        self.dlg.btnAsigTareas.setEnabled(False)
        self.dlg.btnConsulta.setEnabled(False)
        self.dlg.btnDibujo.setEnabled(False)
        self.dlg.btnEliminar.setEnabled(False)
        self.dlg.btnTopologia.setEnabled(False)
        self.dlg.btnFusDiv.setEnabled(False)
        self.dlg.btnCargaMasiva.setEnabled(False)
        self.dlg.btnAsigCampo.setEnabled(False)
        self.dlg.btnAsigRev.setEnabled(False)
        self.dlg.btnAsigPad.setEnabled(False)
        self.dlg.btnInterPad.setEnabled(False)
        self.dlg.btnInterRev.setEnabled(False)
        self.dlg.btnAdminUsers.setEnabled(False)

    #--------MEOTOD QUE COMPRUEBA LAS VERIIFCACIONES DE LOS BOTONES
    def asignActionsByRoles(self, iface):
        var = QSettings()
        print('EStado del user: '+ var.value('logeado'))
        if var.value('logeado') == 'True':
            response = self.consumeWSGeneral("http://192.168.0.21:8080/autentificacion/api/account/permisos-carto")
            print(response)
            for rol in response["roles"]:
                if rol == 'ASIGNACION_TAREAS':
                    self.dlg.btnAsigTareas.setEnabled(True)
                if rol == 'CONSULTA':
                    self.dlg.btnConsulta.setEnabled(True)
                if rol == 'DIBUJO':
                    self.dlg.btnDibujo.setEnabled(True)
                if rol == 'ELIMINAR':
                    self.dlg.btnEliminar.setEnabled(True)
                if rol == 'TOPOLOGIA':
                    self.dlg.btnTopologia.setEnabled(True)
                if rol == 'FUSION_SUBDIVISION':
                    self.dlg.btnFusDiv.setEnabled(True)
                if rol == 'CARGA_MASIVA':
                    self.dlg.btnCargaMasiva.setEnabled(True)
                if rol == 'ASIGNACION_CAMPO':
                    self.dlg.btnAsigCampo.setEnabled(True)
                if rol == 'ASIGNACION_REVISION':
                    self.dlg.btnAsigRev.setEnabled(True)
                if rol == 'ASIGNACION_PADRON':
                    self.dlg.btnAsigPad.setEnabled(True)
                if rol == 'INTERMEDIO_REVISION':
                    self.dlg.btnInterRev.setEnabled(True)
                if rol == 'INTERMEDIO_PADRON':
                    self.dlg.btnInterPad.setEnabled(True)
                if rol == 'ADMIN_USERS':
                    self.dlg.btnAdminUsers.setEnabled(True)
        else:
            self.comproveRoles()
#------------------ no se hace nada con este metodo -----------------------------------
    def borrar (self):

        # valida si ya se ha agregado el grupo
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup('consulta')
        if group is None:

            root = QgsProject.instance().layerTreeRoot() 
            root.addGroup('consulta')
            root.addGroup('referencia') 

        # nuevaCapa = QgsVectorLayer(QSettings().value('sAreasInscritas'), 'areas_inscritas', 'memory')

        listNC = []
        listNC.append(QgsVectorLayer(QSettings().value('sAreasInscritas'), 'areas_inscritas', 'memory'))
        listNC.append(QgsVectorLayer(QSettings().value('sCvesVert'), 'cves_verticales', 'memory'))
        listNC.append(QgsVectorLayer(QSettings().value('sVert'), 'verticales', 'memory'))
        listNC.append(QgsVectorLayer(QSettings().value('sHoriNum'), 'horizontales.num', 'memory'))
        listNC.append(QgsVectorLayer(QSettings().value('sHoriGeom'), 'horizontales.geom', 'memory'))
        listNC.append(QgsVectorLayer(QSettings().value('sConst'), 'construcciones', 'memory'))
        listNC.append(QgsVectorLayer(QSettings().value('sPredNum'), 'predios.num', 'memory'))
        listNC.append(QgsVectorLayer(QSettings().value('sPredGeom'), 'predios.geom', 'memory'))
        listNC.append(QgsVectorLayer(QSettings().value('sManzana'), 'manzana', 'memory'))

        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup('consulta')

        for l in listNC:
            
            self.UTI.formatoCapa(l.name(), l)

            QgsProject.instance().addMapLayers([l], False)

            capaArbol = QgsLayerTreeLayer(l)
            group.insertChildNode(0, capaArbol)

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
        return QCoreApplication.translate('Master', message)

#-----------------------------------------------------

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
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

#-----------------------------------------------------

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/Master/icon.png'

        var = QSettings()
        if var.value('logeado') == 'True':

            self.add_action(
                icon_path,
                text=self.tr(u'Master'),
                callback=self.run,
                parent=self.iface.mainWindow())

#-----------------------------------------------------

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Master'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

#-----------------------------------------------------

    def run(self):
        """Run method that performs all the real work"""
        #self.irAConsulta()
        #self.ACA.pintarCapas()
        #self.irAFusionDivision()
        '''
        if self.banderaInicial:
            capaManzana = QgsProject.instance().mapLayer(self.ACA.obtenerIdCapa('manzana'))
            capaPredsG = QgsProject.instance().mapLayer(self.ACA.obtenerIdCapa('predios.geom'))
            capaPredN = QgsProject.instance().mapLayer(self.ACA.obtenerIdCapa('predios.num'))
            capaConst = QgsProject.instance().mapLayer(self.ACA.obtenerIdCapa('construcciones'))
            capaHoriG = QgsProject.instance().mapLayer(self.ACA.obtenerIdCapa('horizontales.geom'))
            capaHoriN = QgsProject.instance().mapLayer(self.ACA.obtenerIdCapa('horizontales.num'))
            capaVert = QgsProject.instance().mapLayer(self.ACA.obtenerIdCapa('verticales'))
            capaCvert = QgsProject.instance().mapLayer(self.ACA.obtenerIdCapa('cves_verticales'))
            
            self.banderaInicial = False
            '' '
            capaManzana.selectionChanged.connect(self.ELM.cargarEliminar)
            capaPredsG.selectionChanged.connect(self.ELM.cargarEliminar)
            capaPredN.selectionChanged.connect(self.ELM.cargarEliminar)
            capaConst.selectionChanged.connect(self.ELM.cargarEliminar)
            capaHoriG.selectionChanged.connect(self.ELM.cargarEliminar)
            capaHoriN.selectionChanged.connect(self.ELM.cargarEliminar)
            capaVert.selectionChanged.connect(self.ELM.cargarEliminar)
            capaCvert.selectionChanged.connect(self.ELM.cargarEliminar)
            '''
        # show the dialog
        #self.irAConsulta()
        #self.ACA.pintarCapas()
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        #self.irAConsulta()

        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            
            pass

#-----------------------------------------------------------------------

    def irAAsignaTareas(self):

        # Asignacion de tareas
        self.AST = AsignaTareas.AsignaTareas(iface)
        self.AST.CFG = self.CFG
        self.AST.UTI = self.UTI

        self.AST.run()

#-----------------------------------------------------------------------

    def irAConsulta(self):

        self.ACA.CFG = self.CFG
        self.ACA.UTI = self.UTI
        self.ACA.DFS = self.DFS
        self.ACA.DBJ = self.ACA
        self.ACA.ELM = self.ELM
        self.ACA.DFS = self.DFS
        self.ACA.TPG = self.TPG
        self.ACA.CMS = self.CMS

        self.ACA.run()

#--------------------------------------------------------------------------

    def irADibujo(self):

        self.DBJ.CFG = self.CFG
        self.DBJ.UTI = self.UTI
        self.DBJ.DFS = self.DFS
        self.DBJ.ACA = self.ACA
        self.DBJ.ELM = self.ELM
        self.DBJ.DFS = self.DFS
        self.DBJ.TPG = self.TPG

        self.DBJ.run()

#------------------------------------------------------------------------

    def irAEliminar(self):

        self.ELM.CFG = self.CFG
        self.ELM.UTI = self.UTI
        self.ELM.DFS = self.DFS
        self.ELM.DBJ = self.DBJ
        self.ELM.ACA = self.ACA
        self.ELM.DFS = self.DFS
        self.ELM.TPG = self.TPG

        self.ELM.run()

#-----------------------------------------------------------------------------

    def irATopologia(self):

        self.TPG.CFG = self.CFG
        self.TPG.UTI = self.UTI
        self.TPG.DFS = self.DFS
        self.TPG.DBJ = self.DBJ
        self.TPG.ELM = self.ELM
        self.TPG.DFS = self.DFS
        self.TPG.CMS = self.CMS

        self.TPG.run()

#--------------------------------------------------------------------------

    def irAFusionDivision(self):

        self.DFS.CFG = self.CFG
        self.DFS.UTI = self.UTI
        self.DFS.DFS = self.DFS
        self.DFS.DBJ = self.DBJ
        self.DFS.ELM = self.ELM
        self.DFS.ACA = self.ACA
        self.DFS.TPG = self.TPG

        self.DFS.run()

##############################################################################

    def irACargaMasiva(self):

        self.CMS.UTI = self.UTI
        self.CMS.ACA = self.ACA

        self.CMS.run()

###############################################################################

    def irAAsignacionCampo(self):

        self.ASCM.CFG = self.CFG
        self.ASCM.ACA = self.ACA

        self.ASCM.run()

####################################################################################

    def irAAsignacionRevision(self):

        self.ASRV.CFG = self.CFG
        self.ASRV.ACA = self.ACA

        self.ASRV.run()

####################################################################################

    def irAAsignacionPadron(self):

        self.ASPA.CFG = self.CFG
        self.ASPA.ACA = self.ACA

        self.ASPA.run()

####################################################################################

    def irAIntermediarioPad(self):

        self.INTEPAD.CFG = self.CFG
        self.INTEPAD.ACA = self.ACA
        self.INTEPAD.UTI = self.UTI

        self.INTEPAD.run()

####################################################################################

    def irAIntermediarioRev(self):

        self.INTEREV.CFG = self.CFG
        self.INTEREV.ACA = self.ACA
        self.INTEREV.UTI = self.UTI

        self.INTEREV.run()

####################################################################################
    
    def irAAdminUsuarios(self):

        #Administracion de usuarios
        self.ADU = AdminUsers.AdminUsers(iface)

        self.ADU.CFG = self.CFG
        self.ADU.UTI = self.UTI

        self.ADU.run()


    # --- S E R V I C I O S   W E B  ---

    # - consume ws 
    def consumeWSGeneral(self, url_cons = ""):

        url = url_cons
        data = ""

        try:
            self.headers['Authorization'] = self.UTI.obtenerToken()
            response = requests.get(url, headers = self.headers)
        except requests.exceptions.RequestException as e:
            self.UTI.mostrarAlerta("Error de servidor, 'consumeWSGeneral(Master)' '" + str(e) + "'", QMessageBox().Critical, "Error de servidor")
            return

        if response.status_code == 200:
            data = response.content
            
        elif response.status_code == 403:
            self.UTI.mostrarAlerta('Sin Permisos para ejecutar la accion', QMessageBox().Critical, "Sistema Cartográfico")
            return None
           
        else:
            self.UTI.mostrarAlerta('Error en peticion "consumeWSGeneral(Master)":\n' + response.text, QMessageBox().Critical, "Error de servidor")
            return

        return json.loads(data.decode("utf-8"))

    # --- S E R V I C I O S   W E B   CIERRA ---
