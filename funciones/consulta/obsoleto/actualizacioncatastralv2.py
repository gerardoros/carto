# -*- coding: utf-8 -*-

from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt, QSettings, QSize
from PyQt5.QtGui import QIcon, QColor, QCursor, QPixmap
from PyQt5.QtWidgets import QAction, QMessageBox, QTableWidgetItem
from PyQt5 import QtWidgets
# Initialize Qt resources from file resources.py
from .resources import *
from qgis.core import *
from qgis.utils import iface
from qgis.gui import QgsLayerTreeView
from PyQt5 import QtGui
# Import the code for the DockWidget
from .actualizacioncatastralv2_dockwidget import actualizacioncatastralv2DockWidget
import os.path
import os, json, requests
from osgeo import ogr, osr
from .Cedula_MainWindow import CedulaMainWindow

class actualizacioncatastralv2:

    def __init__(self, iface):

        # Save reference to the QGIS interface
        self.iface = iface

        self.CFG = None
        self.UTI = None
        self.DFS = None
        self.DBJ = None
        self.ELM = None
        self.DFS = None
        self.TPG = None

        self.pluginIsActive = False
        self.dockwidget = None
        self.dockwidget = actualizacioncatastralv2DockWidget()

        self.dockwidget.setMinimumSize(QSize(359, 0))
        self.dockwidget.setMaximumSize(QSize(360, 1000))

        self.dockwidget.botonEditar.clicked.connect(self.actualizarFeature)
        self.dockwidget.botonActualizarRef.clicked.connect(self.actualizarFeatureRef)
        self.dockwidget.botonCancelarReferencia.clicked.connect(self.rollbackCapa)
        self.dockwidget.botonCargar.clicked.connect(self.pintarCapas)
        self.dockwidget.comboLocalidad.currentIndexChanged.connect(self.obtenerSectoresPorLocalidad)
        self.dockwidget.comboSector.currentIndexChanged.connect(self.obtenerManzanasPorSector)
        self.dockwidget.comboManzana.currentIndexChanged.connect(self.obtenerIdManzana)
        self.dockwidget.botonCargarReferencia.clicked.connect(self.intermediarioReferencia)
        self.dockwidget.botonActivarEdicion.clicked.connect(self.activarEdicion)
        self.dockwidget.botonActualizarServiciosCalles.clicked.connect(self.actualizarServiciosCalles)

        self.diccServiciosCalle = {}

        self.capaEnEdicion = ''
        QSettings().setValue('capaRefEdicion', 'None')
        self.manzanaPrincipal = None
        self.tablasReferencias = {
        'Estado' : 'e_estado',
        'Region Catastral' : 'e_region_carto',
        'Municipios' : 'e_municipio',
        'Secciones' : 'e_seccion',		
        'Localidades' : 'e_localidad',
        'Sectores' : 'e_sector',
        'Manzanas' : 'e_manzana',
        'Predios' : 'e_predio',
        'Calles' : 'vw_calle',
        'Colonias' : 'e_colonia',
        'Codigo Postal' : 'e_cp',
        'Zona Uno' : 'e_zona_uno',
        'Zona Dos' : 'e_zona_dos',
        'Area de Valor' : 'e_area_valor'
        }

        # -- evento boton de abrir cedula --
        self.dockwidget.btnAbrirCedula.setIcon(QtGui.QIcon('add.png'))
        self.dockwidget.btnAbrirCedula.clicked.connect(self.abrirCedula)
        # -- evento boton de cancelar apertura de cedula --
        self.dockwidget.btnCancelAperCedula.clicked.connect(self.cancelarCedula)
        self.canvas = iface.mapCanvas()
        self.cursorRedondo = QCursor(QPixmap(["16 16 3 1",
                                "      c None",
                                ".     c #FF0000",
                                "+     c #FFFFFF",
                                "                ",
                                "       +.+      ",
                                "      ++.++     ",
                                "     +.....+    ",
                                "    +.     .+   ",
                                "   +.   .   .+  ",
                                "  +.    .    .+ ",
                                " ++.    .    .++",
                                " ... ...+... ...",
                                " ++.    .    .++",
                                "  +.    .    .+ ",
                                "   +.   .   .+  ",
                                "   ++.     .+   ",
                                "    ++.....+    ",
                                "      ++.++     ",
                                "       +.+      "]))

        # --  diseño del cursor --
        self.abrePredio = False
        # -- lista -- 
        self.dockwidget.lista = {}

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
        self.pluginIsActive = False

 ########################################################################################################

    def run(self):
        
        self.obtenerXCapas()

        if self.capasCompletas():

            if not self.pluginIsActive:
                self.pluginIsActive = True

                if self.dockwidget == None:

                    self.dockwidget = actualizacioncatastralv2DockWidget()

                # connect to provide cleanup on closing of dockwidget
                self.dockwidget.closingPlugin.connect(self.onClosePlugin)

                # show the dockwidget
                # TODO: fix to allow choice of dock location
                self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
                

                self.cuerpo = {"incluirGeom": "true", "pagina": None, "bbox": "false", "pin": "false", "geomWKT": None, "epsg": None, "properties": None, "epsgGeomWKT": None, "itemsPagina": None, "nombre": "x"}
                self.headers = {'Content-Type': 'application/json'}
                self.payload = json.dumps(self.cuerpo)

                self.dockwidget.comboSector.clear()
                self.dockwidget.comboLocalidad.clear()
                self.dockwidget.comboManzana.clear()

                #Inicializacionde IdManzana
                self.idManzana = ' '

                #Modo desarrollor
                self.modoDesarrollo = True
                self.cargaRapida = True
                #01001001020004054011
                #01001001020004027003
                #01001001020004063010

                if self.capaEnEdicion != '':

                    self.dockwidget.comboCapasEdicion.setEnabled(False)
                    self.dockwidget.botonActivarEdicion.setEnabled(False)
                    self.dockwidget.botonActualizarRef.setEnabled(True)
                    self.dockwidget.botonCancelarReferencia.setEnabled(True)

                else:

                    self.dockwidget.comboCapasEdicion.setEnabled(True)
                    self.dockwidget.botonActivarEdicion.setEnabled(True)
                    self.dockwidget.botonActualizarRef.setEnabled(False)
                    self.dockwidget.botonCancelarReferencia.setEnabled(False)

                if self.capaEnEdicion == self.obtenerIdCapa('Calles'):
                    self.dockwidget.tablaServiciosCalles.setVisible(True)
                    self.dockwidget.botonActualizarServiciosCalles.setVisible(True)
                    self.dockwidget.tituloServiciosCalles.setVisible(True)
                else:
                    self.dockwidget.tablaServiciosCalles.setVisible(False)
                    self.dockwidget.botonActualizarServiciosCalles.setVisible(False)
                    self.dockwidget.tituloServiciosCalles.setVisible(False)

                #Acciones iniciales
                if self.modoDesarrollo:
                    self.obtenerIdManzana()
                    #self.pintarCapas()

                else:
                    try:
                        self.obtenerLocalidades()

                    except:
                        self.UTI.mostrarAlerta("Error al cargar localidades\nError de servidor", QMessageBox().Information, "Cargar Localidades")

                #Asignar eventos de cambio de seleccion
                

                self.xManzana.selectionChanged.connect(self.cargarTablita)
                self.xPredGeom.selectionChanged.connect(self.cargarTablita)
                self.xPredNum.selectionChanged.connect(self.cargarTablita)
                self.xConst.selectionChanged.connect(self.cargarTablita)
                self.xHoriGeom.selectionChanged.connect(self.cargarTablita)
                self.xHoriNum.selectionChanged.connect(self.cargarTablita)
                self.xVert.selectionChanged.connect(self.cargarTablita)
                self.xCvesVert.selectionChanged.connect(self.cargarTablita)


                self.llenarComboReferencias()
                self.dockwidget.show()
                
        else:
            self.UTI.mostrarAlerta('No existen las capas necesarias para la consulta de manzanas', QMessageBox().Critical, 'Consulta de manzanas')
            return


#######################################################################################################################
    
    #validar posicion valida de combo
    def validarCombox(self):
        return (self.dockwidget.comboLocalidad.count() > 0 and self.dockwidget.comboSector.count() > 0 and self.dockwidget.comboManzana.count()) or self.modoDesarrollo

##########################################################################
    def obtenerIdManzana(self):
        
        
        #Obtener el identificador de la manzana
        if self.modoDesarrollo:
           
            #self.idManzana = '01001001020004016031' #Esta es la chida
            #self.idManzana = '01001001020004026039' #Cortita y chiquita
            #self.idManzana = '01001001020004026040' #Cortita y chiquita
            self.idManzana = '01001001020004060004' 
                             #01001001020  4026040
            #self.idManzana = '01001001020004060004'  #La larga que le gusta a mi jefe
            
            #01001001020004026039
            #01001001020  4026039

            #self.idManzana = '01001001020004017005' #esta es la mala krnal
            #self.idManzana =  '010010010204050001' #Esta calamos guardado
            #self.idManzana = '01001001020004026040'
            #self.idManzana = '01001001020004021016'
            

        else:
            index = self.dockwidget.comboManzana.currentIndex()
            self.idManzana = self.dockwidget.comboManzana.itemData(index)
            
        
########################################################################################################################

    #Llenar primer combo
    def obtenerLocalidades(self):

        self.dockwidget.comboLocalidad.clear()

        try:
            headers = {'Content-Type': 'application/json', 'Authorization' : self.UTI.obtenerToken()}
            respuesta = requests.get(self.CFG.urlLocalidades, headers = headers)
        except requests.exceptions.RequestException:
            self.UTI.mostrarAlerta("Error de servidor", QMessageBox().Critical, "Cargar Localidades")
            print('ERROR: LOC000')

        lenJson = len(list(respuesta.json()))

        if lenJson > 0:
            for localidad in respuesta.json():
                self.dockwidget.comboLocalidad.addItem(str(localidad['label']) + " " + localidad['other'], str(localidad['value']) )
        else:
            self.UTI.mostrarAlerta("No existen localidades registradas", QMessageBox().Information, "Cargar Localidades")

#################################################################################################################################

    #Llenar segundo combo
    def obtenerSectoresPorLocalidad(self):

        if self.dockwidget.comboLocalidad.count() > 0:

            index = self.dockwidget.comboLocalidad.currentIndex()
            idSector = self.dockwidget.comboLocalidad.itemData(index)
            
            self.dockwidget.comboSector.clear()

            try:
                headers = {'Content-Type': 'application/json', 'Authorization' : self.UTI.obtenerToken()}
                respuesta = requests.get(self.CFG.urlSectores + idSector + '/sector/', headers = headers)
            except requests.exceptions.RequestException:
                self.UTI.mostrarAlerta("Error de servidor", QMessageBox().Critical, "Cargar Sectores")
                print('ERROR: SEC000')

            lenJson = len(list(respuesta.json()))

            if lenJson > 0:

                for sector in respuesta.json():

                    self.dockwidget.comboSector.addItem(sector['label'], sector['value']) #Cambiar value por label
            else:
                self.UTI.mostrarAlerta("No existen sectores en la localidad", QMessageBox().Information, "Cargar Sectores")
            

################################################################################################################################

    def llenarComboReferencias(self):
        self.dockwidget.comboCapaReferencia.clear()
        self.dockwidget.comboCapaReferencia.addItem('Estado', 'e_estado')
        self.dockwidget.comboCapaReferencia.addItem('Region Catastral', 'e_region_carto')
        self.dockwidget.comboCapaReferencia.addItem('Municipios', 'e_municipio')
        self.dockwidget.comboCapaReferencia.addItem('Secciones', 'e_seccion')
        self.dockwidget.comboCapaReferencia.addItem('Localidades', 'e_localidad')
        self.dockwidget.comboCapaReferencia.addItem('Sectores', 'e_sector')
        self.dockwidget.comboCapaReferencia.addItem('Manzanas', 'e_manzana')
        self.dockwidget.comboCapaReferencia.addItem('Predios', 'e_predio')
        self.dockwidget.comboCapaReferencia.addItem('Calles', 'vw_calle')
        self.dockwidget.comboCapaReferencia.addItem('Colonias', 'e_colonia')
        self.dockwidget.comboCapaReferencia.addItem('Codigo Postal', 'e_cp')
        self.dockwidget.comboCapaReferencia.addItem('Zona Uno', 'e_zona_uno')
        self.dockwidget.comboCapaReferencia.addItem('Zona Dos', 'e_zona_dos')
        self.dockwidget.comboCapaReferencia.addItem('Area de Valor', 'e_area_valor')


#################################################################################################################################
    #Llenar tercer combo
    def obtenerManzanasPorSector(self):
    
        if self.dockwidget.comboSector.count() > 0:

            index = self.dockwidget.comboSector.currentIndex()
            idSector = self.dockwidget.comboSector.itemData(index)

            self.dockwidget.comboManzana.clear()

            try:
                headers = {'Content-Type': 'application/json', 'Authorization' : self.UTI.obtenerToken()}
                respuesta = requests.get(self.CFG.urlManzanas + idSector + '/manzana/', headers = headers)
            except requests.exceptions.RequestException:
                self.UTI.mostrarAlerta("Error de servidor", QMessageBox().Critical, "Cargar Manzanas")
                print('ERROR: MAN000')

            lenJson = len(list(respuesta.json()))

            if lenJson > 0:
                for manzana in respuesta.json():
                    self.dockwidget.comboManzana.addItem(manzana['label'], manzana['other'])#Cambiar other por label
            else:
                self.UTI.mostrarAlerta("No existen manzanas en el sector", QMessageBox().Information, "Cargar Manzanas")

#####################################################################################################

    def intermediarioReferencia(self):
        nameCapa = self.dockwidget.comboCapaReferencia.currentText()

        try:
            bound = self.obtenerBoundingBox().asWkt()
        except:
            self.UTI.mostrarAlerta('No se ha cargado ninguna Manzana', QMessageBox().Critical, 'Cargar referencia')
            return

        if self.dockwidget.checkTodasGeom.isChecked():
            bound = None

        self.pintarCapasReferencia(nameCapa, bound, False)


##############################################################################################

#####################################################################################################

    def obtenerBoundingBox(self):
        
        self.manzanaPrincipal = self.xManzana

        if self.manzanaPrincipal == None:
            return

        listaManzanas = list(self.manzanaPrincipal.getFeatures())
        geometria = QgsGeometry()

        rango = len(listaManzanas)
        geometria = listaManzanas[0].geometry()

        for i in range(0, rango):
            geometria = geometria.combine(listaManzanas[i].geometry())

        geoTemp = (QgsGeometry.fromWkt(geometria.boundingBox().asWktPolygon())).buffer(60, 0)

        return geoTemp



#####################################################################################################

    #Pintar todas las capas
    def pintarCapas(self):

        QSettings().setValue('listaEliminada', [])
        root = QgsProject.instance().layerTreeRoot()

        group = root.findGroup('ERRORES DE TOPOLOGIA')
        if not group is None:
            for child in group.children():
                dump = child.dump()
                id = dump.split("=")[-1].strip()
                QgsProject.instance().removeMapLayer(id)
            root.removeChildNode(group)

        #try:
        if self.validarCombox():

            self.vaciarCapa(self.xManzana)
            self.vaciarCapa(self.xPredGeom)
            self.vaciarCapa(self.xPredNum)
            self.vaciarCapa(self.xConst)
            self.vaciarCapa(self.xHoriGeom)
            self.vaciarCapa(self.xHoriNum)
            self.vaciarCapa(self.xVert)
            self.vaciarCapa(self.xCvesVert)

            if self.cargaRapida:
                if not self.pintarUnaCapa(self.xManzana):
                    return
                self.zoomManzana()
                
                if not self.pintarUnaCapa(self.xPredGeom):
                    return

                if not self.pintarNum(self.xPredNum):
                    return

                if not self.pintarUnaCapa(self.xHoriGeom):
                    return

                if not self.pintarNum(self.xHoriNum):
                    return
                

            else:
                if not self.pintarUnaCapa(self.xManzana):
                    return
                self.zoomManzana()
                
                if not self.pintarUnaCapa(self.xPredGeom):
                    return

                if not self.pintarNum(self.xPredNum):
                    return
                
                if not self.pintarUnaCapa(self.xConst):
                    return
                
                if not self.pintarUnaCapa(self.xHoriGeom):
                    return

                if not self.pintarNum(self.xHoriNum):
                    return

                if not self.pintarUnaCapa(self.xVert):
                    return
                
                if not self.pintarUnaCapa(self.xCvesVert):
                    return
            
            print ("Capas cargadas con exito")

        else:
            self.UTI.mostrarAlerta('No se han seleccionado manzanas para cargar', QMessageBox.Critical, 'Capas de consulta')

##############################################################################################################

    def pintarCapasCampo(self):
        self.vaciarCapa(self.xManzana)
        self.vaciarCapa(self.xPredGeom)
        self.vaciarCapa(self.xPredNum)
        self.vaciarCapa(self.xConst)
        self.vaciarCapa(self.xHoriGeom)
        self.vaciarCapa(self.xHoriNum)
        self.vaciarCapa(self.xVert)
        self.vaciarCapa(self.xCvesVert)

        
        if not self.pintarUnaCapa(self.xManzana):
            return
        self.zoomManzana()
        
        if not self.pintarUnaCapa(self.xPredGeom):
            return

        if not self.pintarNum(self.xPredNum):
            return
        
        if not self.pintarUnaCapa(self.xHoriGeom):
            return

        if not self.pintarNum(self.xHoriNum):
            return

        if not self.pintarUnaCapa(self.xVert):
            return
        
        if not self.pintarUnaCapa(self.xCvesVert):
            return
        
        print ("Capas cargadas con exito")

########################################################################################################

    def pintarUnaCapa(self, mem_layer):
        
        nombreCapa = mem_layer.name()
        print ("Cargando... " + nombreCapa)
    

        if mem_layer == None:
            self.UTI.mostrarAlerta('No existe la capa ' + str(nombreCapa), QMessageBox().Critical, 'Cargar capas')
            return False
        
        data = self.obtenerAPintar(mem_layer.id())

        

        type(data)
        srid = QSettings().value("srid")
        inSpatialRef = osr.SpatialReference()
        inSpatialRef.ImportFromEPSG(int(srid))
        outSpatialRef = osr.SpatialReference()
        outSpatialRef.ImportFromEPSG(int(srid))
        coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
        if not bool(data):
            self.UTI.mostrarAlerta("Error de servidor", QMessageBox().Critical, "Cargar capa de consulta")
            print('ERROR: CAP000')

        #Obtenemos todos los atributos del JSON
        #print(data)
        if data['features'] == []:
            print('no se han traido ', nombreCapa)
            return True
        
        varKeys = data['features'][0]['properties']

        keys = list(varKeys.keys())

        properties = []
        geoms = []

        

        for feature in data['features']:

            geom = feature['geometry']
            
            property = feature['properties']
            geom = json.dumps(geom)
            geometry = ogr.CreateGeometryFromJson(geom)
            geometry.Transform(coordTrans)
            geoms.append(geometry.ExportToWkt())
            l = []
            for i in range(0, len(keys)):
                l.append(property[keys[i]])
            properties.append(l)

        prov = mem_layer.dataProvider()
        feats = [ QgsFeature() for i in range(len(geoms)) ]

        for i, feat in enumerate(feats):
            feat.setAttributes(properties[i])
            feat.setGeometry(QgsGeometry.fromWkt(geoms[i]))

        prov.addFeatures(feats)

        if nombreCapa == 'predios.geom':
            self.cargarPrediosEnComboDividir(feats)

        mem_layer.triggerRepaint()
        return True

####################################################################################################

    def pintarNum(self, mem_layer):

        nombreCapa = mem_layer.name()
        print ("Cargando... " + nombreCapa)
    

        if mem_layer == None:
            self.UTI.mostrarAlerta('No existe la capa ' + str(nombreCapa), QMessageBox().Critical, 'Cargar capas')
            return False

        data = self.obtenerAPintar(mem_layer.id())

        etiquetaField = ""
        colorCapa = ""
        if mem_layer.id() == self.obtenerIdCapa("predios.num"):
            etiquetaField = "numExt"
            colorCapa = QColor(0,255,0)
        elif mem_layer.id() == self.obtenerIdCapa("horizontales.num"):
            etiquetaField = "num_ofi"
            colorCapa = QColor(198,140,33)

        type(data)
        srid = QSettings().value("srid")
        inSpatialRef = osr.SpatialReference()
        inSpatialRef.ImportFromEPSG(int(srid))
        outSpatialRef = osr.SpatialReference()
        outSpatialRef.ImportFromEPSG(int(srid))
        coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
        if not bool(data):
            return True
            #self.UTI.mostrarAlerta("Error de servidor", QMessageBox().Critical, "Cargar capa de consulta")
            #print('ERROR: NUM000')

        
        
        #Obtenemos todos los atributos del JSON
        polys = []
        listNum = []

        print ('==============', data)
        for feature in data:
            wkt = feature['geomNum']
            listNum.append(feature[etiquetaField])
            gem = QgsGeometry.fromWkt(wkt)
            polys.append(gem)

        mem_layer.startEditing()

        prov = mem_layer.dataProvider()
        feats = [ QgsFeature() for i in range(len(polys)) ]

        for i, feat in enumerate(feats):  
            feat.setGeometry(polys[i])
            prov.addFeature(feat)
            #feat[etiquetaField] = listNum[i]
            #mem_layer.updateFeature(feat)
            mem_layer.changeAttributeValue(feat.id(), 0, listNum[i])
            
        mem_layer.commitChanges()

        settings = QgsPalLayerSettings()
        settings.fieldName = etiquetaField
        settings.enabled = True
        settings.isExpression = False
        
        settings.centroidWhole = True

        textFormat = QgsTextFormat()
        textFormat.setColor(colorCapa)
        textFormat.setSize(8)
        textFormat.setNamedStyle('Bold')

        settings.setFormat(textFormat)

        #settings.placement= QgsPalLayerSettings.OverPoint
        labeling = QgsVectorLayerSimpleLabeling(settings)

        mem_layer.setLabeling(labeling)
        mem_layer.setLabelsEnabled(True)

        mem_layer.triggerRepaint()

        return True
        
#####################################################################################################

    def vaciarCapa(self, mem_layer):

        if mem_layer == None:
            return

        mem_layer.setReadOnly(False)
        #Obtenemos los fields antes de eliminar las features
        inFields = mem_layer.dataProvider().fields()
        #Habilitamos opcion de editado
        mem_layer.startEditing()
        #Iteramos para eliminar Features
        for f in mem_layer.getFeatures():
            mem_layer.deleteFeature(f.id())
        
        #Reasignamos los fields al VectorLayer
        mem_layer.dataProvider().addAttributes(inFields.toList())
        #Guardamos los cambios
        mem_layer.setReadOnly(True)
        mem_layer.commitChanges()

###################################################################################

    def zoomManzana(self):
    
        mem_layer = self.xManzana

        if mem_layer == None:
            return

        listaManzanas = list(mem_layer.getFeatures())
        geometria = QgsGeometry()

        rango = len(listaManzanas)

        if rango == 0:
            return

        geometria = listaManzanas[0].geometry()
        final = QgsGeometry()

        for i in range(0, rango):
            geometria = geometria.combine(listaManzanas[i].geometry())

        features = list(mem_layer.getFeatures())
        f = features[0]
        bbox = geometria.boundingBox()
        iface.mapCanvas().setExtent(bbox)
        iface.mapCanvas().refresh()

############################################################################################

    
    def esCapaReferencia(self, idCapa):

        if idCapa == self.obtenerIdCapa('Area de Valor'):
            return True
        elif idCapa == self.obtenerIdCapa('Zona Uno'):
            return True
        elif idCapa == self.obtenerIdCapa('Zona Dos'):
            return True
        elif idCapa == self.obtenerIdCapa('Codigo Postal'):
            return True
        elif idCapa == self.obtenerIdCapa('Colonias'):
            return True
        elif idCapa == self.obtenerIdCapa('Calles'):
            return True
        elif idCapa == self.obtenerIdCapa('Sectores'):
            return True
        elif idCapa == self.obtenerIdCapa('Localidades'):
            return True
        elif idCapa == self.obtenerIdCapa('Secciones'):
            return True
        elif idCapa == self.obtenerIdCapa('Municipios'):
            return True
        elif idCapa == self.obtenerIdCapa('Region Catastral'):
            return True
        elif idCapa == self.obtenerIdCapa('Estado'):
            return True
        
        else:
            return False

###############################################################################################

    def obtenerAPintar(self, idCapa):

        url = ' '
        if self.traducirIdCapa(idCapa) == 'manzana':
            url = self.CFG.urlConsultaManzana
        elif self.traducirIdCapa(idCapa) == 'predios.geom':
            url = self.CFG.urlConsultaPrediosGeom
        elif self.traducirIdCapa(idCapa) == 'predios.num':
            url = self.CFG.urlConsultaPrediosNum
        elif self.traducirIdCapa(idCapa) == 'construcciones':
            url = self.CFG.urlConsultaConstrucciones
        elif self.traducirIdCapa(idCapa) == 'horizontales.geom':
            url = self.CFG.urlConsultaHorizontalesGeom
        elif self.traducirIdCapa(idCapa) == 'horizontales.num':
            url = self.CFG.urlConsultaHorizontalesNum
        elif self.traducirIdCapa(idCapa) == 'verticales':
            url = self.CFG.urlConsultaVerticales
        elif self.traducirIdCapa(idCapa) == 'cves_verticales':
            url = self.CFG.urlConsultaClavesV

        #idManzana = self.dockwidget.comboManzana.currentText()
        try:
            headers = {'Content-Type': 'application/json', 'Authorization' : self.UTI.obtenerToken()}

            if self.traducirIdCapa(idCapa) == 'predios.num' or self.traducirIdCapa(idCapa) == 'horizontales.num':
                response = requests.get(url + self.idManzana, headers = headers)
            else:
                response = requests.post(url + self.idManzana, headers = headers, data = self.payload)



        except requests.exceptions.RequestException:
            self.UTI.mostrarAlerta("Error de servidor", QMessageBox().Critical, "Error de servidor")
            print('ERROR OAP000')
            return
        data = ""
        if response.status_code == 200:
            
            data = response.content

        else:
            self.UTI.mostrarAlerta('Error en peticion:\n' + response.text, QMessageBox().Critical, "Cargar capa")
            print('ERROR: CAP001')

        #if self.traducirIdCapa(idCapa) == 'horizontales.geom':
        #    print(json.loads(data.decode('utf-8')))

        #print(json.loads(data.decode('utf-8')))
        return json.loads(data.decode('utf-8'))


        #Metodo que crea un elemento QMessageBox
    
#########################################################################################################
    
    def cargarTablita(self):
        
        self.capaActiva = iface.activeLayer()
        self.vaciarTablita()
        
        self.comboConstEsp = QtWidgets.QComboBox()

        header = self.dockwidget.tablaEdicion.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        #header.setStretchLastSection(True)
        
        self.dockwidget.labelCapaEdicion.setText('---')
        if self.capaActiva == None:
            #self.UTI.mostrarAlerta("No tienes ninguna capa activa", QMessageBox().Critical, 'Edicion de atributos')
            self.cambiarStatus("No se ha seleccionado ninguna capa", "error")

        else:

            self.seleccion = self.capaActiva.selectedFeatures()
            self.listaEtiquetas = []
            self.dockwidget.labelCapaEdicion.setText(self.traducirIdCapa( self.capaActiva.id()))
            
            if (len(self.seleccion) == 1):

                self.cambiarStatus("Edicion Activa", "ok")
                campos = self.capaActiva.fields()   
                nombres = [campo.name() for campo in campos]
                self.tipConst = 0

                if self.capaActiva.id() == self.obtenerIdCapa('manzana'):
                    self.listaAtributos = ['clave']
                    self.listaEtiquetas = ['Clave']
                elif self.capaActiva.id() == self.obtenerIdCapa('predios.geom'):
                    self.listaAtributos = ['clave']
                    self.listaEtiquetas = ['Clave']
                elif self.capaActiva.id() == self.obtenerIdCapa('predios.num'):
                    self.listaAtributos = ['numExt']
                    self.listaEtiquetas = ['Numero exterior']
                elif self.capaActiva.id() == self.obtenerIdCapa('construcciones'):
                    ixCveConstEsp = campos.lookupField('cve_const_esp')
                    self.tipConst = self.seleccion[0].attributes()[ixCveConstEsp]
                    headers = {'Content-Type': 'application/json', 'Authorization' : self.UTI.obtenerToken()}
                    respuesta = requests.get(self.CFG.urlTipoConstEsp, headers = headers)
                    diccionarioConst = {}
                    if respuesta.status_code == 200:
                        for clave in respuesta.json():
                            self.comboConstEsp.addItem(str(clave['cveConstEsp']) + " - " + clave['descripcion'], str(clave['cveConstEsp']) )
                            diccionarioConst[clave['cveConstEsp']] = str(clave['cveConstEsp']) + " - " + clave['descripcion']
                    else:
                        self.UTI.mostrarAlerta("No se han podido cargar los tipos de construccion especial\nError de servidor", QMessageBox().Critical, "Cargar tipos de construccion especial")

                    if  self.tipConst != None:
                        self.listaAtributos = ['nom_volumen', 'cve_const_esp']
                        self.listaEtiquetas = ['Nombre de volumen', 'Tipo de construccion']
                    else:
                        self.listaAtributos = ['nom_volumen', 'num_niveles']
                        self.listaEtiquetas = ['Nombre de volumen', 'Numero de niveles']
                elif self.capaActiva.id() == self.obtenerIdCapa('horizontales.geom'):
                    self.listaAtributos = ['clave']
                    self.listaEtiquetas = ['Clave']
                elif self.capaActiva.id() == self.obtenerIdCapa('horizontales.num'):
                    self.listaAtributos = ['num_ofi']
                    self.listaEtiquetas = ['Numero Oficial']
                elif self.capaActiva.id() == self.obtenerIdCapa('verticales'):
                    self.listaAtributos = ['clave']
                    self.listaEtiquetas = ['Clave']
                elif self.capaActiva.id() == self.obtenerIdCapa('cves_verticales'):
                    self.listaAtributos = ['clave']
                    self.listaEtiquetas = ['Clave']

                if self.capaActiva.id() == self.obtenerIdCapa('construcciones'):
                    for x in range(0, len(self.listaAtributos)):
                                
                        self.dockwidget.tablaEdicion.insertRow(x)
                        item = QtWidgets.QTableWidgetItem(self.listaEtiquetas[x])
                        self.dockwidget.tablaEdicion.setItem(x, 0 , item)#self.capaActual.getFeatures().attributes()[x])
                        item.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled )
                        textoItem = str( self.seleccion[0][self.listaAtributos[x]])
                        #print(textoItem)
                        if self.tipConst != None: 
                            if x == 1:
                                self.dockwidget.tablaEdicion.setCellWidget(1,1,self.comboConstEsp)
                                textito = self.seleccion[0].attributes()[ixCveConstEsp]
                                index = self.comboConstEsp.findText(diccionarioConst[textito], QtCore.Qt.MatchFixedString)
                                if index >= 0:
                                    self.comboConstEsp.setCurrentIndex(index)
                            else:

                                self.dockwidget.tablaEdicion.setItem(x, 1 , QtWidgets.QTableWidgetItem(textoItem)) 
                        else:
                            self.dockwidget.tablaEdicion.setItem(x, 1 , QtWidgets.QTableWidgetItem(textoItem))
                else:
                    for x in range(0, len(self.listaAtributos)):
                                
                        self.dockwidget.tablaEdicion.insertRow(x)
                        item = QtWidgets.QTableWidgetItem(self.listaEtiquetas[x])
                        self.dockwidget.tablaEdicion.setItem(x, 0 , item)#self.capaActual.getFeatures().attributes()[x])
                        item.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled )
                        textoItem = str( self.seleccion[0][self.listaAtributos[x]])
                        self.dockwidget.tablaEdicion.setItem(x, 1 , QtWidgets.QTableWidgetItem(textoItem))

            else:
                self.cambiarStatus("Debes seleccionar exactamente un elemento", "error")

        # -- abrir cedula -- 
        if self.abrePredio:

            listElim = []

            for key, value in self.dockwidget.lista.items():
                if self.dockwidget.lista[key].isVisible() == False:
                    listElim.append(key)



            for key in listElim:
                del self.dockwidget.lista[key]

            capaActiva = iface.activeLayer()
            features = []
            cond = False

            # saber cual capa esta activa, a cual se le dio click
            if capaActiva.id() == self.obtenerIdCapa('predios.geom'):
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
                        geom = cv.geometry().buffer(-0.000001,1)
                        if geom.within(geomP):
                            cond = True
                            break

            elif capaActiva.id() == self.obtenerIdCapa('horizontales.geom'):
                features = self.xHoriGeom.selectedFeatures()
                cond = True
            elif capaActiva.id() == self.obtenerIdCapa('cves_verticales'):
                features = self.xCvesVert.selectedFeatures()
                cond = True

            if len(features) == 0:
                self.cambiarStatusCedula("Seleccione una geometria", "error")
                return
            if len(features) != 1:
                self.cambiarStatusCedula("Seleccione una sola geometria", "error")
                return
            else:
                self.cambiarStatusCedula("Abriendo cedula...", "ok")

                feat = features[0]

                if len(feat['cve_cat']) < 25:
                    self.UTI.mostrarAlerta('La clave catastral tiene un formato incorrecto, guarde la manzana e intente de nuevo', QMessageBox().Warning, 'Cedula Catastral')
                    return

                

                #validar si la clave ya existe
                for key, value in self.dockwidget.lista.items():
                    if str(key) == str(feat['cve_cat'][0:25]):
                        self.UTI.createAlert('La Clave: \'' + str(feat['cve_cat'][0:25]) + '\' se encuentra abierta', QMessageBox.Information, 'Cedula Catastral')
                        self.cancelaAperturaCedula()
                        return

                # limite de cedulas abiertas
                if len(self.dockwidget.lista) == 5:
                    self.UTI.createAlert('Excedio el limite de cedulas abiertas', QMessageBox().Warning, 'Cedula Catastral')
                    return

                # abrir Cedula
                self.dockwidget.lista[str(feat['cve_cat'])[0:25]] = CedulaMainWindow(str(feat['cve_cat']), cond = cond, CFG = self.CFG, UTI = self.UTI)
                self.dockwidget.lista[str(feat['cve_cat'])[0:25]].show()
                
            self.cancelaAperturaCedula()

#########################################################################################################

    def actualizarFeature(self):

        if  self.dockwidget.tablaEdicion.rowCount() > 0:       

            if self.validarEdicion():
                
                self.UTI.mostrarAlerta('Se actualizo correctamente', QMessageBox().Information, 'Edicion de atributos')
                self.cargarTablita()
            
        else:
            self.UTI.mostrarAlerta("Necesitas seleccionar una capa", QMessageBox.Warning, 'Edicion de atributos')

#############################################################################################################################

    def vaciarTablita(self):
        
        self.dockwidget.tablaEdicion.clearContents()
        self.dockwidget.tablaEdicion.setRowCount(0)
            
        for row in range(0, self.dockwidget.tablaEdicion.rowCount()):        
            self.dockwidget.tablaEdicion.removeRow(row) 

###########################################################################################################################

    def cargarTablitaRef(self):

        self.capaActiva = iface.activeLayer()
        self.vaciarTablitaRef()
        
        if self.capaActiva.id() == self.capaEnEdicion:

            self.comboTipoAs = QtWidgets.QComboBox()
            self.comboTipoVia = QtWidgets.QComboBox()
            self.comboCveVus = QtWidgets.QComboBox()

            self.comboTipoAs.clear()
            self.comboTipoVia.clear()
            self.comboCveVus.clear()

            idCapa = self.capaActiva.id()

            header = self.dockwidget.tablaEdicionRef.horizontalHeader()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
            #header.setStretchLastSection(True)
            
            self.dockwidget.labelCapaEdicionRef.setText('---')



            if idCapa != self.obtenerIdCapa('Manzanas' )and idCapa != ('Predios'):

                self.seleccion = self.capaActiva.selectedFeatures()
                self.listaEtiquetas = []
                self.dockwidget.labelCapaEdicionRef.setText( self.traducirIdCapa( self.capaActiva.id()))
                
                if (len(self.seleccion) == 1):

                    self.cambiarStatusRef("Edicion Activa", "ok")
                    campos = self.capaActiva.fields()   
                    nombres = [campo.name() for campo in campos]
                    self.tipConst = 0

                    if self.capaActiva.id() == self.obtenerIdCapa('Area de Valor'): #Areas de valor
                        self.listaAtributos = ['valor', 'descripcion', 'cve_vus']
                        self.listaEtiquetas = ['Valor', 'Descripcion', 'vus']

                        headers = {'Content-Type': 'application/json', 'Authorization' : self.UTI.obtenerToken()}

                        respuesta = requests.get(self.CFG.urlValoresTerrenos, headers = headers)
                        self.diccCveVus = {}
                        if respuesta.status_code == 200:
                            for resp in respuesta.json():

                                self.comboCveVus.addItem(str(resp['descripcion']), str(resp['cveVus']))
                                self.diccCveVus[str(resp['cveVus'])] = str(resp['descripcion'])
                        
                        else:
                            self.UTI.mostrarAlerta("No se han podido cargar los tipos de cvevus\nError de servidor", QMessageBox().Critical, "Cargar tipos de asentamiento")


                    elif self.capaActiva.id() == self.obtenerIdCapa('Zona Uno') or self.capaActiva.id() == self.obtenerIdCapa('Zona Dos'): #Zonas
                        self.listaAtributos = ['descripcion']
                        self.listaEtiquetas = ['Descripcion']

                    elif self.capaActiva.id() == self.obtenerIdCapa('Predios'): #Zonas
                        self.listaAtributos = ['clave']
                        self.listaEtiquetas = ['Clave']

                    elif self.capaActiva.id() == self.obtenerIdCapa('Colonias'): #Codigo Postal
                        self.listaAtributos = ['cve_col', 'id_tipo_asentamiento', 'descripcion']
                        self.listaEtiquetas = ['Clave', 'Tipo de Asentamiento', 'Descripcion']

                        headers = {'Content-Type': 'application/json', 'Authorization' : self.UTI.obtenerToken()}

                        respuesta = requests.get(self.CFG.urlTipoAsentamiento, headers = headers)
                        self.comboTipoAs.addItem('NULL','Ninguno')
                        self.diccionarioTipoAs = {}
                        self.diccionarioTipoAs['NULL'] = 'Ninguno'
                        if respuesta.status_code == 200:
                            for resp in respuesta.json():

                                self.comboTipoAs.addItem(str(resp['descripcion']), str(resp['id']))
                                self.diccionarioTipoAs[str(resp['id'])] = str(resp['descripcion'])
                                
                        
                        else:
                            self.UTI.mostrarAlerta("No se han podido cargar los tipos de asentamiento\nError de servidor", QMessageBox().Critical, "Cargar tipos de asentamiento")


                    elif self.capaActiva.id() == self.obtenerIdCapa('Codigo Postal'): #Colonia
                        self.listaAtributos = ['cve_cp']
                        self.listaEtiquetas = ['CP']

                    elif self.capaActiva.id() == self.obtenerIdCapa('Calles'): #Calles
                        self.listaAtributos = ['valor', 'longitud', 'id_cve_vialidad', 'tipo_vector_calle', 'calle']
                        self.listaEtiquetas = ['Valor', 'Longitud', 'Clave vialidad', 'Tipo de Vector', 'Calle']

                        headers = {'Content-Type': 'application/json', 'Authorization' : self.UTI.obtenerToken()}

                        respuesta = requests.get(self.CFG.urlTipoVialidad, headers = headers)
                        self.comboTipoVia.addItem('Ninguno','NULL')
                        self.diccionarioTipoVia = {}
                        self.diccionarioTipoVia['NULL'] = 'Ninguno'
                        if respuesta.status_code == 200:

                            for resp in respuesta.json():
                                
                                self.comboTipoVia.addItem(str(resp['cTipoVialidad']), str(resp['id']))
                                self.diccionarioTipoVia[str(resp['id'])] = str(resp['cTipoVialidad'])

                        else:
                            self.UTI.mostrarAlerta("No se han podido cargar los tipos de asentamiento\nError de servidor", QMessageBox().Critical, "Cargar tipos de vialidad")


                    elif self.capaActiva.id() == self.obtenerIdCapa('Sectores'): #Sector
                        self.listaAtributos = ['clave', 'nombre']
                        self.listaEtiquetas = ['Clave', 'Nombre']
                    
                    elif self.capaActiva.id() == self.obtenerIdCapa('Localidades'): #Localidades
                        self.listaAtributos = ['clave', 'nombre']
                        self.listaEtiquetas = ['Clave', 'Nombre']
                    
                    elif self.capaActiva.id() == self.obtenerIdCapa('Secciones'): #Secciones
                        self.listaAtributos = ['clave', 'nombre']
                        self.listaEtiquetas = ['Clave', 'Nombre']

                    elif self.capaActiva.id() == self.obtenerIdCapa('Municipios'): #Municipios
                        self.listaAtributos = ['clave', 'nombre']
                        self.listaEtiquetas = ['Clave', 'Nombre']

                    elif self.capaActiva.id() == self.obtenerIdCapa('Region Catastral'): #Region Catastral
                        self.listaAtributos = ['clave', 'nombre']
                        self.listaEtiquetas = ['Clave', 'Nombre']

                    elif self.capaActiva.id() == self.obtenerIdCapa('Estado'): #Estado
                        self.listaAtributos = ['clave', 'nombre']
                        self.listaEtiquetas = ['Clave', 'Nombre']


                    for x in range(0, len(self.listaAtributos)):
                        self.dockwidget.tablaEdicionRef.insertRow(x)

                        item = QtWidgets.QTableWidgetItem(self.listaEtiquetas[x])
                        self.dockwidget.tablaEdicionRef.setItem(x, 0 , item)#self.capaActual.getFeatures().attributes()[x])
                        item.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled )

                        textoItem = str( self.seleccion[0][self.listaAtributos[x]])

                        self.dockwidget.tablaEdicionRef.setItem(x, 1 , QtWidgets.QTableWidgetItem(textoItem))


                    if self.capaActiva.id() == self.obtenerIdCapa( 'Colonias'):

                        self.dockwidget.tablaEdicionRef.setCellWidget(1,1,self.comboTipoAs)

                        idCve = str(self.seleccion[0]['id_tipo_asentamiento'])
                        if idCve == None:
                            idCve = 'NULL'


                        textito = self.diccionarioTipoAs[idCve]
                        index = self.comboTipoAs.findText(str(textito), QtCore.Qt.MatchFixedString)
                        if index >= 0:
                            self.comboTipoAs.setCurrentIndex(index)

                    elif self.capaActiva.id() == self.obtenerIdCapa( 'Area de Valor'):

                        self.dockwidget.tablaEdicionRef.setCellWidget(2,1,self.comboCveVus)

                        idCve = str(self.seleccion[0]['cve_vus'])

                        textito = self.diccCveVus[idCve]
                        index = self.comboCveVus.findText(str(textito), QtCore.Qt.MatchFixedString)
                        if index >= 0:
                            self.comboCveVus.setCurrentIndex(index)



                    elif self.capaActiva.id() == self.obtenerIdCapa('Calles'): #Calles

                        self.dockwidget.tablaEdicionRef.setCellWidget(2,1,self.comboTipoVia)

                        idCve = str(self.seleccion[0]['id_cve_vialidad'])
                        if idCve == None:
                                idCve = 'NULL'

                        textito = self.diccionarioTipoVia[idCve]

                        index = self.comboTipoVia.findText(str(textito), QtCore.Qt.MatchFixedString)
                        if index >= 0:
                            self.comboTipoVia.setCurrentIndex(index)
                        
                        longitud = self.seleccion[0].geometry().length()
                        item = QtWidgets.QTableWidgetItem(str(longitud))
                        item.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled )
                        self.dockwidget.tablaEdicionRef.setItem(1, 1 , item)
                        idCalle = self.seleccion[0]['id']

                        if not str(idCalle) in self.diccServiciosCalle.keys():
            
                            headers = {'Content-Type': 'application/json', 'Authorization' : self.UTI.obtenerToken()}

                            self.dockwidget.tablaServiciosCalles.clearContents()
                            self.dockwidget.tablaServiciosCalles.setRowCount(0)
                            if idCalle != None:
                                idCalle = str(idCalle)
                                respuesta = requests.get(self.CFG.urlServCalle + idCalle, headers = headers)

                                if respuesta.status_code == 200:
                                    datos = respuesta.json()

                                    for x in range(0, len(list(datos))):

                                        self.dockwidget.tablaServiciosCalles.insertRow(x)
                                        check = QTableWidgetItem(datos[x]['descripcion'])
                                        check.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                                        if datos[x]['disponible'] == False:
                                            check.setCheckState(QtCore.Qt.Unchecked)
                                        else:
                                            check.setCheckState(QtCore.Qt.Checked)
                                        self.dockwidget.tablaServiciosCalles.setItem(x,0,check)

                                        item2 = QTableWidgetItem(datos[x]['servicio'])
                                        self.dockwidget.tablaServiciosCalles.setItem(x,1,item2)
                        
                        else:
                            listaServicios = self.diccServiciosCalle[str(idCalle)]

                            for x in range(0, len(listaServicios)):
                                self.dockwidget.tablaServiciosCalles.insertRow(x)

                                estado = listaServicios[x][0]
                                check = QTableWidgetItem(listaServicios[x][1])
                                item2 = QTableWidgetItem(listaServicios[x][2])

                                check.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                                if estado == '0':
                                    check.setCheckState(QtCore.Qt.Unchecked)
                                else:
                                    check.setCheckState(QtCore.Qt.Checked)

                                self.dockwidget.tablaServiciosCalles.setItem(x,0,check)
                                self.dockwidget.tablaServiciosCalles.setItem(x,1,item2)


                else:
                    self.cambiarStatusRef("Debes seleccionar exactamente un elemento", "error")

            else:
                self.cambiarStatusRef("No se permite editar la capa seleccionada", "error")

#########################################################################################################

    def actualizarFeatureRef(self):

        if  self.dockwidget.tablaEdicionRef.rowCount() > 0:       

            if self.validarEdicionRef():
                
                self.UTI.mostrarAlerta('Se actualizo correctamente', QMessageBox().Information, 'Edicion de atributos')
                self.cargarTablitaRef()
            
        else:
            self.UTI.mostrarAlerta("Se requiere seleccionar exactamente un elemento a editar", QMessageBox.Warning, 'Edicion de atributos')

#############################################################################################################################

    def vaciarTablitaRef(self):
        
        self.dockwidget.tablaEdicionRef.clearContents()
        self.dockwidget.tablaEdicionRef.setRowCount(0)
            
        self.dockwidget.tablaServiciosCalles.clearContents()
        self.dockwidget.tablaServiciosCalles.setRowCount(0)

        #for row in range(0, self.dockwidget.tablaEdicionRef.rowCount()):        
        #    self.dockwidget.tablaEdicionRef.removeRow(row) 

####################################################################################################################


    def cambiarStatus(self, texto, estado):

        self.dockwidget.labelStatusEdicion.setText(texto)

        self.dockwidget.labelStatusEdicion.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        
        if estado == "ok":
            estilo = """color: rgb(1, 230, 1);
font: 10pt "Bahnschrift";"""
        elif estado == "error":
            estilo = """color: rgb(255, 0, 0);
font: 10pt "Bahnschrift";"""
        elif estado == "warning":
            estilo = """color: rgb(255, 255, 0);
font: 10pt "Bahnschrift";"""

        self.dockwidget.labelStatusEdicion.setStyleSheet(estilo)

############################################################################################################################

    def cambiarStatusCedula(self, texto, estado):

        self.dockwidget.lbEstatusCedula.setText(texto)

        if estado == "ok": # abriendo
            self.dockwidget.lbEstatusCedula.setStyleSheet('color: green')
        elif estado == "error": # Seleccione un solo predio
            self.dockwidget.lbEstatusCedula.setStyleSheet('color: red')
        else:
            self.dockwidget.lbEstatusCedula.setStyleSheet('color: black')



###################################################################################################################

    def cambiarStatusRef(self, texto, estado):

        self.dockwidget.labelStatusEdicionRef.setText(texto)

        self.dockwidget.labelStatusEdicionRef.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        
        if estado == "ok":
            estilo = """color: rgb(1, 230, 1);
font: 10pt "Bahnschrift";"""
        elif estado == "error":
            estilo = """color: rgb(255, 0, 0);
font: 10pt "Bahnschrift";"""
        elif estado == "warning":
            estilo = """color: rgb(255, 255, 0);
font: 10pt "Bahnschrift";"""

        self.dockwidget.labelStatusEdicionRef.setStyleSheet(estilo)

#########################################################################################################################

    def validarEdicion(self):

        nombreCapa = self.traducirIdCapa( self.capaActiva.id())
        feat = self.capaActiva.selectedFeatures()[0]
        banderaCompleta = True
        self.capaActiva.startEditing()

        if nombreCapa == 'manzana':
            texto = "Nada"
            
            try:
                texto = self.dockwidget.tablaEdicion.item(0, 1).text()
            except: #Error al obtenre texto
                banderaCompleta = False
            if self.UTI.esEntero(texto): #Cuando es entero
                if len(texto) == 3: #Validacion de longitud
                    feat['clave'] = texto
                else:
                    banderaCompleta = False
            else: #Cuando no es numerico
                banderaCompleta = False
            
            if not banderaCompleta: #Mensaje de error
                self.UTI.mostrarAlerta('La clave debe estar compuesta por exactamente 3 numeros', QMessageBox().Critical, 'Error de entrada')

        #.....predios geom....#
        elif nombreCapa == 'predios.geom':
            texto = "Nada"
            
            try:
                texto = self.dockwidget.tablaEdicion.item(0, 1).text()
            except: #Error al obtenre texto
                banderaCompleta = False
            if self.UTI.esEntero(texto): #Cuando es entero
                if len(texto) == 2: #Validacion de longitud
                    feat['clave'] = texto
                else:
                    banderaCompleta = False
            else: #Cuando no es numerico
                banderaCompleta = False
            
            if not banderaCompleta: #Mensaje de error
                self.UTI.mostrarAlerta('La clave debe estar compuesta por exactamente 2 numeros', QMessageBox().Critical, 'Error de entrada')

        #.....predios geom....#
        elif nombreCapa == 'predios.num':
            texto = "Nada"
            
            try:
                texto = self.dockwidget.tablaEdicion.item(0, 1).text()
            except: #Error al obtenre texto
                banderaCompleta = False

            lenText = len(texto.strip())

            if lenText < 21 and lenText > 0: #Validacion de longitud
                feat['numExt'] = texto
            else:
                banderaCompleta = False

            if not banderaCompleta: #Mensaje de error
                self.UTI.mostrarAlerta('El numero oficial no debe exceder los 20 caracteres', QMessageBox().Critical, 'Error de entrada')
        
        #.....predios geom....#
        elif nombreCapa == 'horizontales.geom':
            texto = "Nada"
            
            try:
                texto = self.dockwidget.tablaEdicion.item(0, 1).text()
            except: #Error al obtenre texto
                banderaCompleta = False
            if self.UTI.esEntero(texto): #Cuando es entero
                if len(texto) == 6: #Validacion de longitud
                    feat['clave'] = texto
                else:
                    banderaCompleta = False
            else: #Cuando no es numerico
                banderaCompleta = False
            
            if not banderaCompleta: #Mensaje de error
                self.UTI.mostrarAlerta('La clave debe estar compuesta por exactamente 6 numeros', QMessageBox().Critical, 'Error de entrada')    

        #.....predios geom....#
        elif nombreCapa == 'horizontales.num':
            texto = "Nada"
            
            try:
                texto = self.dockwidget.tablaEdicion.item(0, 1).text()
            except: #Error al obtenre texto
                banderaCompleta = False

            lenText = len(texto.strip())
            if lenText < 21 and lenText > 0: #Validacion de longitud
                feat['num_ofi'] = texto
            else:
                banderaCompleta = False
            
            if not banderaCompleta: #Mensaje de error
                self.UTI.mostrarAlerta('El numero oficial no debe exceder los 20 caracteres', QMessageBox().Critical, 'Error de entrada')

        #.....verticales geom....#
        elif nombreCapa == 'verticales':
            texto = "Nada"
            
            try:
                texto = self.dockwidget.tablaEdicion.item(0, 1).text()
            except: #Error al obtenre texto
                banderaCompleta = False
            if self.UTI.esEntero(texto): #Cuando es entero
                if len(texto) == 2: #Validacion de longitud
                    feat['clave'] = texto
                else:
                    banderaCompleta = False
            else: #Cuando no es numerico
                banderaCompleta = False
            
            if not banderaCompleta: #Mensaje de error
                self.UTI.mostrarAlerta('La clave debe estar compuesta por exactamente 2 numeros', QMessageBox().Critical, 'Error de entrada') 

        #.....clvaees verticales....#
        elif nombreCapa == 'cves_verticales':
            texto = "Nada"
            
            try:
                texto = self.dockwidget.tablaEdicion.item(0, 1).text()
            except: #Error al obtenre texto
                banderaCompleta = False
            if self.UTI.esEntero(texto): #Cuando es entero
                if len(texto) == 4: #Validacion de longitud
                    feat['clave'] = texto
                else:
                    banderaCompleta = False
            else: #Cuando no es numerico
                banderaCompleta = False
            
            if not banderaCompleta: #Mensaje de error
                self.UTI.mostrarAlerta('La clave debe estar compuesta por exactamente 4 numeros', QMessageBox().Critical, 'Error de entrada')


        elif nombreCapa == 'construcciones': #Con Construcciones

            bandera1 = True
              #Combo de construccion especial
            try:
                texto = self.dockwidget.tablaEdicion.item(0, 1).text()
                if len(texto) > 0 and len(texto) <=3:
                    feat['nom_volumen'] = texto
                else:
                    bandera1 = False
            except:
                bandera1 = False

            if not bandera1:
                self.UTI.mostrarAlerta('El nombre de volumen no debe exceder los 3 caracteres', QMessageBox().Critical, 'Error de entrada')
            
            bandera2 = True

            if feat['cve_const_esp'] != None:
                comboIndex2 = self.comboConstEsp.currentIndex()
                feat['cve_const_esp'] = self.comboConstEsp.itemData(comboIndex2)
                
            else:
                #try:
                texto = self.dockwidget.tablaEdicion.item(1, 1).text()
                try:
                    if len(texto) > 0 and int(texto) < 999 and self.UTI.esEntero(texto):
                        feat['num_niveles'] = texto
                    else:
                        bandera2 = False
                except:
                    bandera2 = False

            if not bandera2:
                self.UTI.mostrarAlerta('El numero de niveles debe ser numerico y no exceder 999', QMessageBox().Critical, 'Error de entrada')

            banderaCompleta = bandera1 and bandera2

        self.capaActiva.updateFeature(feat)
        self.capaActiva.triggerRepaint()
        self.capaActiva.commitChanges()

        return banderaCompleta

#####################################################################################################

    def validarEdicionRef(self):

        nombreCapa = self.traducirIdCapa( self.capaActiva.id())
        feat = self.capaActiva.selectedFeatures()[0]
        banderaCompleta = True

        self.capaActiva.setReadOnly(False)
        self.capaActiva.startEditing()

        #----------------------Area de valor------------------#
        if nombreCapa == 'Area de Valor':

            texto = "Nada"

            banderaValor = True

            try:
                texto = self.dockwidget.tablaEdicionRef.item(0, 1).text()
            except: #Error al obtenre texto
                banderaValor = False
            if self.UTI.esFloat(texto): #Cuando es entero
                if len(texto) < 12: #Validacion de longitud
                    feat['valor'] = float(texto)
                else:
                    banderaValor = False
            else: #Cuando no es numerico
                banderaValor = False
            
            banderaDesc = True

            try:
                texto = self.dockwidget.tablaEdicionRef.item(1, 1).text()
            except: #Error al obtenre texto
                banderaDesc = False
            if len(texto) <= 256: #Validacion de longitud
                feat['descripcion'] = texto
            else:
                banderaDesc = False


            if not banderaValor:
                self.UTI.mostrarAlerta('El valor debe ser un numero decimal cuya longitud de texto no exceda 12 caracteres', QMessageBox().Critical, 'Error de entrada')

            if not banderaDesc:
                self.UTI.mostrarAlerta('La descripcion no debe exceder 256 caracteres', QMessageBox().Critical, 'Error de entrada')

            banderaCompleta = banderaValor and banderaDesc

            if banderaCompleta:
                indexCveVus = self.comboCveVus.currentIndex()
                feat['cve_vus'] = self.comboCveVus.itemData(indexCveVus)

        
        #----------------------Area de valor------------------#
        elif nombreCapa == 'Zona Uno':

            texto = "Nada"

            try:
                texto = self.dockwidget.tablaEdicionRef.item(0, 1).text()
            except: #Error al obtenre texto
                banderaCompleta = False
            if len(texto) <= 50: #Validacion de longitud
                feat['descripcion'] = texto
            else:
                banderaCompleta = False

            
            if not banderaCompleta:
                self.UTI.mostrarAlerta('La descripcion no debe exceder 50 caracteres', QMessageBox().Critical, 'Error de entrada')

        #----------------------Area de valor------------------#
        elif nombreCapa == 'Zona Dos':

            texto = "Nada"

            try:
                texto = self.dockwidget.tablaEdicionRef.item(0, 1).text()
            except: #Error al obtenre texto
                banderaCompleta = False
            if len(texto) <= 50: #Validacion de longitud
                feat['descripcion'] = texto
            else:
                banderaCompleta = False

            
            if not banderaCompleta:
                self.UTI.mostrarAlerta('La descripcion no debe exceder 50 caracteres', QMessageBox().Critical, 'Error de entrada')

        #----------------------Codigo Postal------------------#
        elif nombreCapa == 'Codigo Postal':

            texto = "Nada"

            try:
                texto = self.dockwidget.tablaEdicionRef.item(0, 1).text()
            except: #Error al obtenre texto
                banderaCompleta = False
            if self.UTI.esEntero(texto): #Cuando es entero
                if len(texto) == 5: #Validacion de longitud
                    feat['cve_cp'] = texto
                else:
                    banderaCompleta = False
            else: #Cuando no es numerico
                banderaCompleta = False
            
            if not banderaCompleta:
                self.UTI.mostrarAlerta('El codigo postal debe estar compuesto por 5 numeros', QMessageBox().Critical, 'Error de entrada')

        #----------------------Codigo Postal------------------#
        elif nombreCapa == 'Colonias':

            texto = "Nada"

            banderaClave = True
            banderaDesc = True

            try:
                texto = self.dockwidget.tablaEdicionRef.item(0, 1).text()
            except: #Error al obtenre texto
                banderaClave = False
            if len(texto) == 4: #Validacion de longitud
                feat['cve_col'] = texto
            else:
                banderaClave = False

            
            try:
                texto = self.dockwidget.tablaEdicionRef.item(2, 1).text()
            except: #Error al obtenre texto
                banderaDesc = False
            if len(texto) <= 64: #Validacion de longitud
                feat['descripcion'] = texto
            else:
                banderaDesc = False

            if not banderaClave:
                self.UTI.mostrarAlerta('La longitud de la clave debe ser de 4 caracteres', QMessageBox().Critical, 'Error de entrada')

            if not banderaDesc:
                self.UTI.mostrarAlerta('La longitud de la descripcion no debe exceder 64 caracteres', QMessageBox().Critical, 'Error de entrada')

            banderaCompleta = banderaClave and banderaDesc

            if banderaCompleta:
                indexComboAs = self.comboTipoAs.currentIndex()
                feat['id_tipo_asentamiento'] = self.comboTipoAs.itemData(indexComboAs)
                
         #----------------------Codigo Postal------------------#
        
        #-------------------------Calles------------------------#
        elif nombreCapa == 'Calles':

            texto = "Nada"

            banderaTipo = True
            banderaCalle = True
            banderaValor = True

            #Comparar la clave
            try:
                texto = self.dockwidget.tablaEdicionRef.item(0, 1).text()
            except: #Error al obtenre texto
                banderaValor = False

            if self.UTI.esFloat(texto): #Cuando es entero
                if len(texto) < 12: #Validacion de longitud
                    
                    feat['valor'] = float(texto)
                    
                else:
                    banderaValor = False
            else: #Cuando no es numerico
                banderaValor = False


            try:
                texto = self.dockwidget.tablaEdicionRef.item(4, 1).text()
            except: #Error al obtenre texto
                banderaCalle = False
            if len(texto) <= 256: #Validacion de longitud
                feat['calle'] = texto
            else:
                banderaCalle = False

            
            try:
                texto = self.dockwidget.tablaEdicionRef.item(3, 1).text()
            except: #Error al obtenre texto
                banderaTipo = False
            if len(texto) <= 64: #Validacion de longitud
                feat['tipo_vector_calle'] = texto
            else:
                banderaTipo = False


            if not banderaValor:
                self.UTI.mostrarAlerta('El valor debe ser decimal y no exceder los 12 caracteres de longitud', QMessageBox().Critical, 'Error de entrada')

            if not banderaCalle:
                self.UTI.mostrarAlerta('La longitud de la calle no debe exceder 256 caracteres', QMessageBox().Critical, 'Error de entrada')

            if not banderaTipo:
                self.UTI.mostrarAlerta('La longitud del tipo de vector no debe exceder 64 caracteres', QMessageBox().Critical, 'Error de entrada')

            banderaCompleta = banderaValor and banderaTipo and banderaTipo

            if banderaCompleta:
                indexComboVia = self.comboTipoVia.currentIndex()
                feat['id_cve_vialidad'] = self.comboTipoVia.itemData(indexComboVia)
                feat['c_tipo_vialidad'] = self.comboTipoVia.currentText()
                feat['longitud'] = float(self.dockwidget.tablaEdicionRef.item(1, 1).text())


        #----------------------Codigo Postal------------------#
        elif nombreCapa == 'Sectores':

            texto = "Nada"

            banderaClave = True
            banderaNom = True

            #Comparar la clave
            try:
                texto = self.dockwidget.tablaEdicionRef.item(0, 1).text()
            except: #Error al obtenre texto
                banderaClave = False
            if self.UTI.esEntero(texto): #Cuando es entero
                if len(texto) == 3: #Validacion de longitud
                    feat['clave'] = texto
                else:
                    banderaClave = False
            else: #Cuando no es numerico
                banderaClave = False
            
            #Comparar el nombre
            try:
                texto = self.dockwidget.tablaEdicionRef.item(1, 1).text()
            except: #Error al obtenre texto
                banderaNom = False
            if len(texto) <= 256: #Validacion de longitud
                feat['nombre'] = texto
            else:
                banderaNom = False

            #Banderas
            if not banderaClave:
                self.UTI.mostrarAlerta('La clave debe estar compuesta por 3 numeros', QMessageBox().Critical, 'Error de entrada')

            if not banderaNom:
                self.UTI.mostrarAlerta('La longitud del nombre no debe exceder 256 caracteres', QMessageBox().Critical, 'Error de entrada')

            banderaCompleta = banderaClave and banderaNom

        #----------------------Codigo Postal------------------#
        elif nombreCapa == 'Localidades':

            texto = "Nada"

            banderaClave = True
            banderaNom = True

            #Comparar la clave
            try:
                texto = self.dockwidget.tablaEdicionRef.item(0, 1).text()
            except: #Error al obtenre texto
                banderaClave = False
            if self.UTI.esEntero(texto): #Cuando es entero
                if len(texto) == 4: #Validacion de longitud
                    feat['clave'] = texto
                else:
                    banderaClave = False
            else: #Cuando no es numerico
                banderaClave = False
            
            #Comparar el nombre
            try:
                texto = self.dockwidget.tablaEdicionRef.item(1, 1).text()
            except: #Error al obtenre texto
                banderaNom = False
            if len(texto) <= 256: #Validacion de longitud
                feat['nombre'] = texto
            else:
                banderaNom = False

            #Banderas
            if not banderaClave:
                self.UTI.mostrarAlerta('La clave debe estar compuesta por 4 numeros', QMessageBox().Critical, 'Error de entrada')

            if not banderaNom:
                self.UTI.mostrarAlerta('La longitud del nombre no debe exceder 256 caracteres', QMessageBox().Critical, 'Error de entrada')

            banderaCompleta = banderaClave and banderaNom

        #----------------------Codigo Postal------------------#
        elif nombreCapa == 'Secciones':

            texto = "Nada"

            banderaClave = True
            banderaNom = True

            #Comparar la clave
            try:
                texto = self.dockwidget.tablaEdicionRef.item(0, 1).text()
            except: #Error al obtenre texto
                banderaClave = False
            if self.UTI.esEntero(texto): #Cuando es entero
                if len(texto) == 2: #Validacion de longitud
                    feat['clave'] = texto
                else:
                    banderaClave = False
            else: #Cuando no es numerico
                banderaClave = False
            
            #Comparar el nombre
            try:
                texto = self.dockwidget.tablaEdicionRef.item(1, 1).text()
            except: #Error al obtenre texto
                banderaNom = False
            if len(texto) <= 64: #Validacion de longitud
                feat['nombre'] = texto
            else:
                banderaNom = False

            #Banderas
            if not banderaClave:
                self.UTI.mostrarAlerta('La clave debe estar compuesta por 2 numeros', QMessageBox().Critical, 'Error de entrada')

            if not banderaNom:
                self.UTI.mostrarAlerta('La longitud del nombre no debe exceder 64 caracteres', QMessageBox().Critical, 'Error de entrada')

            banderaCompleta = banderaClave and banderaNom

        #----------------------Codigo Postal------------------#
        elif nombreCapa == 'Municipios':

            texto = "Nada"

            banderaClave = True
            banderaNom = True

            #Comparar la clave
            try:
                texto = self.dockwidget.tablaEdicionRef.item(0, 1).text()
            except: #Error al obtenre texto
                banderaClave = False
            if self.UTI.esEntero(texto): #Cuando es entero
                if len(texto) == 3: #Validacion de longitud
                    feat['clave'] = texto
                else:
                    banderaClave = False
            else: #Cuando no es numerico
                banderaClave = False
            
            #Comparar el nombre
            try:
                texto = self.dockwidget.tablaEdicionRef.item(1, 1).text()
            except: #Error al obtenre texto
                banderaNom = False
            if len(texto) <= 256: #Validacion de longitud
                feat['nombre'] = texto
            else:
                banderaNom = False

            #Banderas
            if not banderaClave:
                self.UTI.mostrarAlerta('La clave debe estar compuesta por 3 numeros', QMessageBox().Critical, 'Error de entrada')

            if not banderaNom:
                self.UTI.mostrarAlerta('La longitud del nombre no debe exceder 256 caracteres', QMessageBox().Critical, 'Error de entrada')

            banderaCompleta = banderaClave and banderaNom

        #----------------------Codigo Postal------------------#
        elif nombreCapa == 'Region Catastral':

            texto = "Nada"

            banderaClave = True
            banderaNom = True

            #Comparar la clave
            try:
                texto = self.dockwidget.tablaEdicionRef.item(0, 1).text()
            except: #Error al obtenre texto
                banderaClave = False
            if self.UTI.esEntero(texto): #Cuando es entero
                if len(texto) == 3: #Validacion de longitud
                    feat['clave'] = texto
                else:
                    banderaClave = False
            else: #Cuando no es numerico
                banderaClave = False
            
            #Comparar el nombre
            try:
                texto = self.dockwidget.tablaEdicionRef.item(1, 1).text()
            except: #Error al obtenre texto
                banderaNom = False
            if len(texto) <= 64: #Validacion de longitud
                feat['nombre'] = texto
            else:
                banderaNom = False

            #Banderas
            if not banderaClave:
                self.UTI.mostrarAlerta('La clave debe estar compuesta por 3 numeros', QMessageBox().Critical, 'Error de entrada')

            if not banderaNom:
                self.UTI.mostrarAlerta('La longitud del nombre no debe exceder 64 caracteres', QMessageBox().Critical, 'Error de entrada')

            banderaCompleta = banderaClave and banderaNom

        #----------------------Codigo Postal------------------#
        elif nombreCapa == 'Estado':

            texto = "Nada"

            banderaClave = True
            banderaNom = True

            #Comparar la clave
            try:
                texto = self.dockwidget.tablaEdicionRef.item(0, 1).text()
            except: #Error al obtenre texto
                banderaClave = False
            if self.UTI.esEntero(texto): #Cuando es entero
                if len(texto) == 2: #Validacion de longitud
                    feat['clave'] = int(texto)
                else:
                    banderaClave = False
            else: #Cuando no es numerico
                banderaClave = False
            
            #Comparar el nombre
            try:
                texto = self.dockwidget.tablaEdicionRef.item(1, 1).text()
            except: #Error al obtenre texto
                banderaNom = False
            if len(texto) <= 64: #Validacion de longitud
                feat['nombre'] = texto
            else:
                banderaNom = False


            banderaCompleta = banderaClave and banderaNom

            #Banderas
            if not banderaClave:
                self.UTI.mostrarAlerta('La clave debe estar compuesta por 2 numeros', QMessageBox().Critical, 'Error de entrada')

            if not banderaNom:
                self.UTI.mostrarAlerta('La longitud del nombre no debe exceder 64 caracteres', QMessageBox().Critical, 'Error de entrada')

        self.capaActiva.updateFeature(feat)
        self.capaActiva.triggerRepaint()
        self.capaActiva.commitChanges()
        self.capaActiva.setReadOnly(False)
        return banderaCompleta

##########################################################################################################


    def pintarCapasReferencia(self, nameCapa, bound, edicion):
        #Nombre de la capa de acuerdo al valor del ComboBox de capas a cargar
        

        self.vaciarTablitaRef()
        self.manzanaPrincipal = self.xManzana

        if self.manzanaPrincipal == None:
            self.UTI.mostrarAlerta("Debes cargar una manzana primero", QMessageBox().Critical, "Pintar capas de referencia")
            return


        if nameCapa == '':
            nameCapa = self.dockwidget.comboCapaReferencia.currentText()

        
        idCapa = self.obtenerIdCapa(nameCapa)
        capaAPintar = QgsProject.instance().mapLayer(idCapa)

        data = self.obtenerCapasDeReferencia(self.tablasReferencias[nameCapa], bound)

        vaciada = False

        if capaAPintar != None:
            if self.capaEnEdicion == self.obtenerIdCapa(nameCapa) and edicion == False:
                self.UTI.mostrarAlerta('La capa se encuentra en modo edicion, debes guardarla para volver a cargarla', QMessageBox().Critical, 'Cargar Capas')
            else:
                vaciada = True
                self.vaciarCapa(capaAPintar)

        if capaAPintar == None or edicion or vaciada:
            
            type(data)
            srid = 32614
            inSpatialRef = osr.SpatialReference()
            inSpatialRef.ImportFromEPSG(int(srid))
            outSpatialRef = osr.SpatialReference()
            outSpatialRef.ImportFromEPSG(int(srid))
            coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
            if not bool(data):
                self.UTI.mostrarAlerta('Error de servidor', QMessageBox().Critical, "Cargar capa de referencia")
                print('ERROR: REF000')
            
            if data['features'] != []:

                varKeys = data['features'][0]['properties']

                keys = list(varKeys.keys())
                properties = []
                geoms = []
                for feature in data['features']:
                    geom = feature['geometry']
                    
                    if geom == None:
                        continue

                    property = feature['properties']
                    geom = json.dumps(geom)
                    geometry = ogr.CreateGeometryFromJson(geom)
                    geometry.Transform(coordTrans)
                    geoms.append(geometry.ExportToWkt())
                    l = []
                    for i in range(0, len(keys)):
                        l.append(property[keys[i]])
                    properties.append(l)


            if nameCapa != 'Calles':    
                if data['features'] != []:
                    fields = ""
                    for k in keys:
                        fields = fields + "&field=" + k + ":string(15)"

                    uriFigura = 'Polygon'

                    uri = str(uriFigura)+"?crs=epsg:" + str(srid) + fields + "&index=yes"
                else:
                    uri = self.obtenerCampos(nameCapa)

            else:
                stringCalles = self.obtenerCamposCalles()
                uri = stringCalles

            if capaAPintar == None:
                mem_layer = QgsVectorLayer(uri, nameCapa, 'memory')
            else:
                mem_layer = capaAPintar

            mem_layer.selectionChanged.connect(self.cargarTablitaRef)
            self.setearIdReferencia(nameCapa, mem_layer.id())

            mem_layer.setReadOnly(not edicion)

            if data['features'] != []:
                prov = mem_layer.dataProvider()
                feats = [ QgsFeature() for i in range(len(geoms)) ]
                for i, feat in enumerate(feats):
                    feat.setAttributes(properties[i])
                    feat.setGeometry(QgsGeometry.fromWkt(geoms[i]))

                if nameCapa != 'Manzanas' and nameCapa != 'Predios':
                    prov.addFeatures(feats)
                
                else:
                    for feat in feats:
                        bandera = True
                        for manzana in self.manzanaPrincipal.getFeatures():
                            if feat.geometry().intersects(manzana.geometry()):
                                bandera = False
                                break
                        if bandera:                
                            prov.addFeatures([feat])


            etiquetaField = ""

            if nameCapa == 'Estado':
                etiquetaField = 'nombre'
            elif nameCapa == 'Region Catastral':
                etiquetaField = 'clave'
            elif nameCapa == 'Municipios':
                etiquetaField = 'nombre'
            elif nameCapa == 'Secciones':
                etiquetaField = 'clave'
            elif nameCapa == 'Localidades':
                etiquetaField = 'nombre'
            elif nameCapa == 'Sectores':
                etiquetaField = 'nombre'
            elif nameCapa == 'Manzanas':
                etiquetaField = 'clave'
            elif nameCapa == 'Predios':
                etiquetaField = 'clave'
            elif nameCapa == 'Calles':
                etiquetaField = 'calle'
            elif nameCapa == 'Colonias':
                etiquetaField = 'descripcion'
            elif nameCapa == 'Codigo Postal':
                etiquetaField = 'cve_cp'
            elif nameCapa == 'Zona Uno':
                etiquetaField = 'clave'
            elif nameCapa == 'Zona Dos':
                etiquetaField = 'clave'
            elif nameCapa == 'Area de Valor':
                etiquetaField = 'valor'


            placeo = QgsPalLayerSettings.AroundPoint

            if nameCapa == 'Calles':
                placeo = QgsPalLayerSettings.Line  

            settings = QgsPalLayerSettings()
            settings.placement = placeo
            settings.fieldName = etiquetaField
            settings.enabled = True
            settings.isExpression = True
            
            settings.centroidWhole = True

            textFormat = QgsTextFormat()
            textFormat.setSize(8)
            textFormat.setNamedStyle('Bold')

            settings.setFormat(textFormat)

            #settings.placement= QgsPalLayerSettings.OverPoint
            labeling = QgsVectorLayerSimpleLabeling(settings)

            mem_layer.setLabeling(labeling)
            mem_layer.setLabelsEnabled(True)

            mem_layer.triggerRepaint()
            root = QgsProject.instance().layerTreeRoot()
            if not edicion:
                grupo = root.findGroup('referencia')
            else:
                grupo = root.findGroup('edicion')
                
                self.capaEnEdicion = self.obtenerIdCapa(nameCapa)
                QSettings().setValue('capaRefEdicion', self.capaEnEdicion)

            if not vaciada or edicion:
                QgsProject.instance().addMapLayers([mem_layer], False)
                
                mzaNL = QgsLayerTreeLayer(mem_layer)

                grupo.insertChildNode(0, mzaNL)


######################################################################################################

    def obtenerCapasDeReferencia(self, egName, bound):

        index = self.dockwidget.comboCapaReferencia.currentIndex()

        token = self.UTI.obtenerToken()

        pagina = None
        itemsPagina = None

        if egName == 'e_predio':
            pagina = 0
            itemsPagina = 6000

        payload = {"nombre": egName, "epsg": 32614,"bbox": False,"pin": False,"geomWKT": bound, "epsgGeomWKT": 32614,"incluirGeom": True,"pagina": pagina,"itemsPagina": itemsPagina}
        payload = json.dumps(payload)
        headers = {'Content-Type': 'application/json', 'Authorization' : token}

        response = requests.post(self.CFG.urlConsultaReferencia, headers = headers, data = payload)
        if response.status_code == 200:
            data = response.content
            data = json.loads(data.decode('utf-8'))

            return data

        else:
            self.UTI.mostrarAlerta('Error de servidor', QMessageBox.Critical, 'Cargar capas de referencia')

##########################################################################################################
    
    def obtenerCampos(self, nombreCapa):

        listaCampos = {}
        listaTipos = {}

        listaCampos['Estado'] = ['clave', 'cve_cat', 'id', 'nombre']
        listaTipos['Estado'] = ['string(5)', 'string(30)', 'integer', 'string(100)']

        listaCampos['Region Catastral'] = ['clave', 'cve_cat', 'id', 'nombre']
        listaTipos['Region Catastral'] = ['string(5)', 'string(30)', 'integer', 'string(100)']

        listaCampos['Municipios'] = ['clave', 'cve_cat', 'id', 'nombre']
        listaTipos['Municipios'] = ['string(5)', 'string(30)', 'integer', 'string(100)']

        listaCampos['Secciones'] = ['clave', 'cve_cat', 'id', 'nombre']
        listaTipos['Secciones'] = ['string(5)', 'string(30)', 'integer', 'string(100)']

        listaCampos['Localidades'] = ['clave', 'cve_cat', 'id', 'nombre']
        listaTipos['Localidades'] = ['string(5)', 'string(30)', 'integer', 'string(100)']

        listaCampos['Sectores'] = ['clave', 'cve_cat', 'id', 'nombre']
        listaTipos['Sectores'] = ['string(5)', 'string(30)', 'integer', 'string(100)']

        listaCampos['Codigo Postal'] = ['cve_cp', 'id']
        listaTipos['Codigo Postal'] = ['string(5)', 'integer']

        listaCampos['Colonias'] = ['cve_col', 'descripcion', 'id', 'id_tipo_asentamiento']
        listaTipos['Colonias'] = ['string(5)', 'string(50)', 'integer', 'integer']
        
        listaCampos['Zona Uno'] = ['descripcion', 'id']
        listaTipos['Zona Uno'] = ['string(50)', 'integer']

        listaCampos['Zona Dos'] = ['descripcion', 'id']
        listaTipos['Zona Dos'] = ['string(50)', 'integer']

        listaCampos['Area de Valor'] = ['cve_vus', 'descripcion', 'id', 'valor']
        listaTipos['Area de Valor'] = ['string(10)', 'string(50)', 'integer', 'real']

        stringCapa = "Polygon?crs=epsg:" + str(QSettings().value('srid'))

        campos = listaCampos[nombreCapa]
        tipos = listaTipos[nombreCapa]

        for indice in range(0, len(campos)):

            name = campos[indice]
            tipo = tipos[indice]

            stringCapa += '&field='
            stringCapa += name + ':'
            stringCapa += tipo

        stringCapa += '&index=yes'
        
        return stringCapa



###########################################################################################################

    def obtenerCamposCalles(self):

        headers = {'Content-Type': 'application/json', 'Authorization' : self.UTI.obtenerToken()}
        respuesta = requests.post(self.CFG.urlCamposCalles, headers = headers)
        
        stringCapa = "LineString?crs=epsg:" + str(QSettings().value('srid'))

        diccionarioTipo = {}
        diccionarioTipo["STRING"] = 'string'
        diccionarioTipo["INTEGER"] = 'integer'
        diccionarioTipo["DATETIME"] = 'date'
        diccionarioTipo["NUMERIC"] = 'real'
        diccionarioTipo["SMALLINT"] = 'integer'
        diccionarioTipo["BOOLEAN"] = 'string'

        if respuesta.status_code == 200:
            datos = respuesta.json()
            
            for campo in datos:

                longitud = campo['longitud']

                name = campo['name']
                tipo = diccionarioTipo[campo['type']]

                stringCapa += '&field='
                stringCapa += name + ':'
                stringCapa += tipo

                if longitud != None:
                    stringCapa += "("+str(longitud)+")"
                
            stringCapa += '&index=yes'
            return stringCapa
        else:
            print("obtenerCamposCalles", respuesta.status_code)

        

######################################################################################################################
    
    def activarEdicion(self):
        
        try:
            bound = self.obtenerBoundingBox().asWkt()
        except:
            self.UTI.mostrarAlerta('No se ha cargado ninguna Manzana', QMessageBox().Critical, 'Cargar referencia')
            return

        nombreCapa = self.dockwidget.comboCapasEdicion.currentText()
        
        root = QgsProject.instance().layerTreeRoot()
        grupoEdicion = root.findGroup('edicion')
        cargar = False
        if grupoEdicion == None:
            root.insertGroup(0, 'edicion')
            grupoEdicion = root.findGroup('edicion')

        self.quitarDeGrupo(self.obtenerIdCapa(nombreCapa), 'referencia')
        self.pintarCapasReferencia(nombreCapa, None, True)
            #self.ineditarCampos(nombreCapa)

        self.dockwidget.comboCapasEdicion.setEnabled(False)
        self.dockwidget.botonActivarEdicion.setEnabled(False)
        self.dockwidget.botonActualizarRef.setEnabled(True)
        self.dockwidget.botonCancelarReferencia.setEnabled(True)

        if nombreCapa == 'Calles':
            self.dockwidget.tablaServiciosCalles.clear()
            self.dockwidget.tablaServiciosCalles.setVisible(True)
            self.dockwidget.botonActualizarServiciosCalles.setVisible(True)
            self.dockwidget.tituloServiciosCalles.setVisible(True)
        else:
            self.dockwidget.tablaServiciosCalles.setVisible(False)
            self.dockwidget.botonActualizarServiciosCalles.setVisible(False)
            self.dockwidget.tituloServiciosCalles.setVisible(False)


##########################################################################################################

    def quitarDeGrupo(self, idCapa, nombreGrupo):

        root = QgsProject.instance().layerTreeRoot()
        grupo = root.findGroup(nombreGrupo)

        capa = QgsProject.instance().mapLayer(idCapa)
        if capa == None:
            return

        if nombreGrupo == 'edicion':

            capa.setReadOnly(True)

        for child in grupo.children():
            if child.name() == capa.name():
                dump = child.dump()
                id = dump.split("=")[-1].strip()
                QgsProject.instance().removeMapLayer(id)
                break

##################################################################################################

    def existeCapa(self, idCapa):
        capa = QgsProject.instance().mapLayer(idCapa)
        return capa != None
    
#########################################################################################

    def guardarCapaReferencia(self):

        if QSettings().value('posibleGuardarRef') == 'True':
            idCapa = self.capaEnEdicion
            capa = QgsProject.instance().mapLayer(self.capaEnEdicion)
            listaAGuardar = []

            for feat in capa.getFeatures():


                campos = {}
                campos['geomWKT'] = feat.geometry().asWkt()
                campos['srid'] = str(QSettings().value('srid'))
                campos['nombre'] = self.tablasReferencias[self.traducirIdCapa(capa.id())]
                atributos = {}
                nombresAtrbutos = capa.fields()   

                nombres = []

                #for campo in nombresAtrbutos:
                #    if self.traducirIdCapa(idCapa) == 'Calles' and campo.name() == 'c_tipo_vialidad':
                #        continue
                #    nombres.append(campo.name())

                nombres = [campo.name() for campo in nombresAtrbutos]

                for x in range(0, len(nombres)):
                    if self.traducirIdCapa(idCapa) == 'Calles' and nombres[x] == 'c_tipo_vialidad':
                        continue
                    atributo = feat.attributes()[x]
                    
                    if str(feat.attributes()[x]) == "NULL":
                        atributo = None
                    atributos[str(nombres[x])] = atributo
                
                campos['propiedades'] = atributos

                if self.traducirIdCapa(idCapa) == 'Calles' and str(feat['id']) in self.diccServiciosCalle.keys():
                    listaServicios = []
                    for lista in self.diccServiciosCalle[str(feat['id'])]:
                        if lista[0] == '2':
                            listaServicios.append(lista[2])

                    campos['propiedades']['catServicios'] = listaServicios
                
                
                if campos['propiedades']['id'] == None:
                    campos['accion'] = 'new'
                else:
                    campos['accion'] = 'update'
                listaAGuardar.append(campos)


            listaTempRef = QSettings().value('listaEliminadaRef')   
            for feat in listaTempRef:
                listaAGuardar.append(feat)

            jsonParaGuardarAtributos = json.dumps(listaAGuardar)

            print(jsonParaGuardarAtributos)
            payload = jsonParaGuardarAtributos
            headers = {'Content-Type': 'application/json', 'Authorization' : self.UTI.obtenerToken()}
            
            
            try:
                response = requests.post(self.CFG.urlGuardadoRef, headers = headers, data = payload)
            
            except requests.exceptions.RequestException:
                self.UTI.mostrarAlerta("No se ha podido conectar al servidor v1", QMessageBox.Critical, "Guardar Cambios v1")#Error en la peticion de consulta
            
            print(response.status_code)
            if response.status_code == 200:
                self.UTI.mostrarAlerta("Cambios guardados con exito", QMessageBox.Information, "Guardar Cambios")
                QSettings().setValue('listaEliminadaRef', [])
                QSettings().setValue('posibleGuardarRef', 'False') 
                self.dockwidget.comboCapasEdicion.setEnabled(True)
                self.dockwidget.botonActivarEdicion.setEnabled(True)
                self.dockwidget.botonActualizarRef.setEnabled(False)
                self.dockwidget.botonCancelarReferencia.setEnabled(False)
                self.quitarDeGrupo(self.capaEnEdicion, 'edicion')
                self.pintarCapasReferencia(self.traducirIdCapa( self.capaEnEdicion), self.obtenerBoundingBox().asWkt(), False)
                self.capaEnEdicion = ''
                QSettings().setValue('capaRefEdicion', self.capaEnEdicion)
                self.dockwidget.tablaServiciosCalles.setVisible(False)
                self.dockwidget.botonActualizarServiciosCalles.setVisible(False)
                self.dockwidget.tituloServiciosCalles.setVisible(False)
                if self.traducirIdCapa(idCapa) == 'Calles':
                    self.diccServiciosCalle = {}
            else:
                print(response.json())
            
        else:
            self.UTI.mostrarAlerta("Se debe validar la topologia de las capas de referencia antes de guardar", QMessageBox.Critical, "Guardar Cambios v1")#Error en la peticion de consulta
            

#####################################################################################################################

    def rollbackCapa(self):
        self.quitarDeGrupo(self.capaEnEdicion, 'edicion')
        #self.vaciarCapa(self.capaEnEdicion);
        traduccion = self.traducirIdCapa(self.capaEnEdicion)
        self.pintarCapasReferencia(traduccion, self.obtenerBoundingBox().asWkt(), False)
        self.dockwidget.comboCapasEdicion.setEnabled(True)
        self.dockwidget.botonActivarEdicion.setEnabled(True)
        self.dockwidget.botonActualizarRef.setEnabled(False)
        self.dockwidget.botonCancelarReferencia.setEnabled(False)
        self.dockwidget.tablaServiciosCalles.setVisible(False)
        self.dockwidget.botonActualizarServiciosCalles.setVisible(False)
        self.dockwidget.tituloServiciosCalles.setVisible(False)
        self.capaEnEdicion = ''
        QSettings().setValue('capaRefEdicion', self.capaEnEdicion)

##########################################################################################################################

    def ineditarCampos(self, nombreCapa):
        #Predios ineditables

        capa = QgsProject.instance().mapLayer(self.obtenerIdCapa(nombreCapa))
        capa.setReadOnly(False)
        campos = capa.fields()   
        nombres = [field.name() for field in campos]

        for i in range (0, len(nombres)):
            config = capa.editFormConfig()
            config.setReadOnly(i, True)
            capa.setEditFormConfig(config)

##########################################################################################################################

    def obtenerXCapas(self):
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


#####################################################################################################################

    def capasCompletas(self):
        if self.xManzana == None:
            return False
        if self.xPredGeom == None:
            return False
        if self.xPredNum == None:
            return False
        if self.xConst == None:
            return False
        if self.xHoriGeom == None:
            return False
        if self.xHoriNum == None:
            return False
        if self.xVert == None:
            return False
        if self.xCvesVert == None:
            return False
        return True

##########################################################################################################################

    def traducirIdCapa(self, idCapa):

        if QSettings().value('xManzana') == idCapa:
            return 'manzana'
        elif QSettings().value('xPredGeom') == idCapa:
            return 'predios.geom'
        elif QSettings().value('xPredNum') == idCapa:
            return 'predios.num'
        elif QSettings().value('xConst') == idCapa:
            return 'construcciones'
        elif QSettings().value('xHoriGeom') == idCapa:
            return 'horizontales.geom'
        elif QSettings().value('xHoriNum') == idCapa:
            return 'horizontales.num'
        elif QSettings().value('xVert') == idCapa:
            return 'verticales'
        elif QSettings().value('xCvesVert') == idCapa:
            return 'cves_verticales'

        elif QSettings().value('xAreaValor') == idCapa:
            return 'Area de Valor'
        elif QSettings().value('xZonaUno') == idCapa:
            return 'Zona Uno'
        elif QSettings().value('xZonaDos') == idCapa:
            return 'Zona Dos'
        elif QSettings().value('xCP') == idCapa:
            return 'Codigo Postal'
        elif QSettings().value('xColonia') == idCapa:
            return 'Colonias'
        elif QSettings().value('xCalle') == idCapa:
            return 'Calles'
        elif QSettings().value('xSector') == idCapa:
            return 'Sectores'
        elif QSettings().value('xLocal') == idCapa:
            return 'Localidades'
        elif QSettings().value('xSeccion') == idCapa:
            return 'Secciones'
        elif QSettings().value('xMunicipio') == idCapa:
            return 'Municipios'
        elif QSettings().value('xRegion') == idCapa:
            return 'Region Catastral'
        elif QSettings().value('xEstado') == idCapa:
            return 'Estado'

        return None

###########################################################################################################################
            
    def obtenerIdCapa(self, nombreCapa):

        if nombreCapa == "manzana":
            return QSettings().value('xManzana')
        elif nombreCapa == "predios.geom":
            return QSettings().value('xPredGeom')
        elif nombreCapa == "predios.num":
            return QSettings().value('xPredNum')
        elif nombreCapa == "construcciones":
            return QSettings().value('xConst')
        elif nombreCapa == "horizontales.geom":
            return QSettings().value('xHoriGeom')
        elif nombreCapa == "horizontales.num":
            return QSettings().value('xHoriNum')
        elif nombreCapa == "verticales":
            return QSettings().value('xVert')
        elif nombreCapa == "cves_verticales":
            return QSettings().value('xCvesVert')
        elif nombreCapa == "Area de Valor":
            return QSettings().value('xAreaValor')
        elif nombreCapa == "Zona Uno":
            return QSettings().value('xZonaUno')
        elif nombreCapa == "Zona Dos":
            return QSettings().value('xZonaDos')
        elif nombreCapa == "Codigo Postal":
            return QSettings().value('xCP')
        elif nombreCapa == "Colonias":
            return QSettings().value('xColonia')
        elif nombreCapa == "Calles":
            return QSettings().value('xCalle')
        elif nombreCapa == "Sectores":
            return QSettings().value('xSector')
        elif nombreCapa == "Localidades":
            return QSettings().value('xLocal')
        elif nombreCapa == "Secciones":
            return QSettings().value('xSeccion')
        elif nombreCapa == "Municipios":
            return QSettings().value('xMunicipio')
        elif nombreCapa == "Region Catastral":
            return QSettings().value('xRegion')
        elif nombreCapa == "Estado":
            return QSettings().value('xEstado')
        
        return 'None'

################################################################################################

    def setearIdReferencia(self, nombreCapa, idCapa):

        if nombreCapa == "Area de Valor":
            valor = 'xAreaValor'
        elif nombreCapa == "Zona Uno":
            valor = 'xZonaUno'
        elif nombreCapa == "Zona Dos":
            valor = 'xZonaDos'
        elif nombreCapa == "Codigo Postal":
            valor = 'xCP'
        elif nombreCapa == "Colonias":
            valor = 'xColonia'
        elif nombreCapa == "Calles":
            valor = 'xCalle'
        elif nombreCapa == "Sectores":
            valor = 'xSector'
        elif nombreCapa == "Localidades":
            valor = 'xLocal'
        elif nombreCapa == "Secciones":
            valor = 'xSeccion'
        elif nombreCapa == "Municipios":
            valor = 'xMunicipio'
        elif nombreCapa == "Region Catastral":
            valor = 'xRegion'
        elif nombreCapa == "Estado":
            valor = 'xEstado'
        elif nombreCapa == "Manzanas":
            valor = 'xManzanasRef'
        elif nombreCapa == "Predios":
            valor = 'xPredRef'

        QSettings().setValue(valor, idCapa)

###################################################################################################

    def actualizarServiciosCalles(self):

        if self.dockwidget.tablaEdicionRef.rowCount() > 0:       

            calleId = str(self.seleccion[0]['id'])
            tablaServicios = self.dockwidget.tablaServiciosCalles

            listaServicios = []
            for x in range(0, tablaServicios.rowCount()):

                listaServicios.append([str(tablaServicios.item(x,0).checkState()), tablaServicios.item(x,0).text(), tablaServicios.item(x,1).text()])

            
            self.diccServiciosCalle[calleId] = listaServicios


        else:
            self.UTI.mostrarAlerta("Se requiere seleccionar exactamente un elemento a editar", QMessageBox.Warning, 'Edicion de servicios de calles')

####################################################################################################################

    # -- metodo boton de abrir cedula --
    def abrirCedula(self):
        self.cambiarStatusCedula("Seleccione un predio...", "ok")
        self.iface.actionSelect().trigger()
        self.canvas.setCursor(self.cursorRedondo)
        self.dockwidget.btnAbrirCedula.setEnabled(False)
        self.abrePredio = True

###########################################################################################################

    # -- metodo boton de cancelar apertura de cedula --
    def cancelarCedula(self):
        self.iface.actionSelect().trigger()
        self.dockwidget.btnAbrirCedula.setEnabled(True)
        self.abrePredio = False
        self.cambiarStatusCedula("Cancelado...", "")

###########################################################################################################

        # -- funcion para cancelar la apertura de la cedula --
    def cancelaAperturaCedula(self):
        self.abrePredio = False
        self.dockwidget.btnAbrirCedula.setEnabled(True)

        self.xPredGeom.removeSelection()
        self.xHoriGeom.removeSelection()
        self.xCvesVert.removeSelection()
        self.canvas.refresh()
        # regresa herramienta de seleccion normal
        self.iface.actionSelect().trigger()
        self.cambiarStatusCedula("Listo...", "ok")

#################################################################


    def segmentar(self):
        #-Irrelevante-#
        capaManzana = QgsProject.instance().mapLayersByName('manzana')[0]
        capaAux = QgsProject.instance().mapLayersByName('cves_verticales')[0]
        #capaCalles = QgsProject.instance().mapLayersByName('Calles')[0]
        
        listaM = self.pruebaObtenerManzana('manzana')
        #print(listaM)
        
        self.manzanaChidotota = listaM[0]
        geomManzana = self.manzanaChidotota.geometry()


        simple = geomManzana.simplify(1)

        n   = 0
        ver = simple.vertexAt(1)
        points=[]

        while(ver != QgsPoint(0,0)):
            n +=1
            points.append(ver)
            ver=simple.vertexAt(n)

        #points.append(points[0])
        segmentos = []
        rango = len(points)
        centroides = []



        for x in range(0, rango-1):
            line_start = points[x]
            line_end = points[x+1]
            line = QgsGeometry.fromPolyline([line_start,line_end])
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry(line.centroid()))
            centroides.append(feat)
            #capaAux.dataProvider().addFeatures([feat])
            #capaAux.triggerRepaint()
            #capaAux.commitChanges()

        callesColindantes = []
        listaToques = []

        listaCalles = self.pruebaObtenerCalles(geomManzana)
        #Ya con centroides

        for punto in centroides:
            
            geomPunto = punto.geometry()
            tamanoBuff = 3
            bandera = False

            while tamanoBuff <= 30:

                bufferPredio = geomPunto.buffer(tamanoBuff,16)
            
                for calle in listaCalles:
                    
                    geomCalle = calle.geometry()
                    bufferCalle = geomCalle.buffer(0.1,1)

                    if bufferCalle.intersects(bufferPredio):
                        bandera = True

                        listaToques.append(calle)

                if not bandera:
                    tamanoBuff += 1
                else:
                    distancia = 999999
                    calleElegida = QgsGeometry()
                    for calleC in listaToques:
                        #print(type(calleC))
                        geomC = calleC.geometry()
                        if geomPunto.distance(geomC) < distancia:
                            distancia = geomPunto.distance(geomC)
                            calleElegida = calleC
                    
                    #st = str(calleElegida['id']) + ' - ' +  str(calleElegida['calle'])
                        
                    if not calleElegida in callesColindantes:
                        callesColindantes.append(calleElegida)

                    tamanoBuff = 99

        return callesColindantes
        
#####################################

    def checarPrincipal(self):

        capaManzana = QgsProject.instance().mapLayersByName('manzana')[0]
        capaPuntos = QgsProject.instance().mapLayersByName('predios.num')[0]
        capaPredios = QgsProject.instance().mapLayersByName('predios.geom')[0]
        capaConstru = QgsProject.instance().mapLayersByName('construcciones')[0]
        listaCalles = self.segmentar()
        
        manzana = self.manzanaChidotota
        geomManzana = manzana.geometry()

        listaPuntosP = self.pruebaObtenerManzana('predios.num')
        listaPredios = self.pruebaObtenerManzana('predios.geom')

        relacionPredios = {}
        for puntito in listaPuntosP:
            geomPuntito = puntito.geometry()
            for predito in listaPredios:
                geomPredito = predito.geometry()
                if geomPuntito.intersects(geomPredito):
                    relacionPredios[puntito.attributes()[0]] = predito.attributes()[1]
                    break

        #print(relacionPredios)



         
        for punto in listaPuntosP:
            
            geomPredio = punto.geometry()

            if not geomPredio.intersects(geomManzana):
                continue

            tamanoBuff = 3
            bandera = False
            listaToques = []
            salidaCalles = []

            while tamanoBuff <= 30:

                bufferPredio = geomPredio.buffer(tamanoBuff,16)
            
                for calle in listaCalles:
                    
                    geomCalle = calle.geometry()
                    bufferCalle = geomCalle.buffer(0.1,1)

                    if bufferCalle.intersects(bufferPredio):
                        bandera = True
                        listaToques.append(calle)

                if not bandera:
                    tamanoBuff += 1
                else:
                    #print('tenemos un else con ' + str(punto.id()))
                    distancia = 999999
                    calleElegida = QgsGeometry()
                    for calleC in listaToques:
                        geomC = calleC.geometry()
                        if geomPredio.distance(geomC) < distancia:
                            distancia = geomPredio.distance(geomC)
                            calleElegida = calleC
                   
                    #if not st in callesColindantes:
                    #salidaCalles.append(st)

                    tamanoBuff = 99
        
###############################################################################################

    def pruebaObtenerManzana(self, nombreCapa):
        #Nombre de la capa de acuerdo al valor del ComboBox de capas a cargar
        
        data = self.obtenerAPintar(self.obtenerIdCapa(nombreCapa))
        
        type(data)
        srid = 32614
        inSpatialRef = osr.SpatialReference()
        inSpatialRef.ImportFromEPSG(int(srid))
        outSpatialRef = osr.SpatialReference()
        outSpatialRef.ImportFromEPSG(int(srid))
        coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
        
        if nombreCapa != 'predios.num':
            if not bool(data):
                raise Exception('Error')

            if data['features'] == []:
                return

            varKeys = data['features'][0]['properties']

            keys = list(varKeys.keys())
            #print(keys)

            
            properties = []
            geoms = []
            for feature in data['features']:
                geom = feature['geometry']
                
                property = feature['properties']
                geom = json.dumps(geom)
                geometry = ogr.CreateGeometryFromJson(geom)
                geometry.Transform(coordTrans)
                geoms.append(geometry.ExportToWkt())

                l = []
                for i in range(0, len(keys)):
                    
                    l.append(property[keys[i]])
                    
                properties.append(l)

            feats = [ QgsFeature() for i in range(len(geoms)) ]
            for i, feat in enumerate(feats):
                feat.setGeometry(QgsGeometry.fromWkt(geoms[i]))
                feat.setAttributes(properties[i])
                #print(properties[i])

            return feats

        else:
            polys = []
            for feature in data:
                wkt = feature['geomNum']
                gem = QgsGeometry.fromWkt(wkt)
                polys.append(gem)

            feats = [ QgsFeature() for i in range(len(polys)) ]

            for i, feat in enumerate(feats):  
                feat.setGeometry(polys[i])
                feat.setAttributes([i])
                #print(feat.attributes())
                #prov.addFeature(feat)
                #feat[etiquetaField] = listNum[i]
                #mem_layer.updateFeature(feat)
                #mem_layer.changeAttributeValue(feat.id(), 0, listNum[i])

            return feats





###

    def pruebaObtenerCalles(self, param):
        #Nombre de la capa de acuerdo al valor del ComboBox de capas a cargar
        
        geoTemp = (QgsGeometry.fromWkt(param.boundingBox().asWktPolygon())).buffer(60, 0)
        #print('la copia')
        #print(type(geoTemp))
        data = self.obtenerCapasDeReferencia(self.tablasReferencias['Calles'], geoTemp.asWkt())
        
        type(data)
        srid = 32614
        inSpatialRef = osr.SpatialReference()
        inSpatialRef.ImportFromEPSG(int(srid))
        outSpatialRef = osr.SpatialReference()
        outSpatialRef.ImportFromEPSG(int(srid))
        coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
        if not bool(data):
            raise Exception('Error')

        if data['features'] == []:
            return

        varKeys = data['features'][0]['properties']

        keys = list(varKeys.keys())
        

        properties = []
        geoms = []
        for feature in data['features']:
            geom = feature['geometry']
            
            property = feature['properties']
            geom = json.dumps(geom)
            geometry = ogr.CreateGeometryFromJson(geom)
            geometry.Transform(coordTrans)
            geoms.append(geometry.ExportToWkt())

            l = []
            for i in range(0, len(keys)):
                
                l.append(property[keys[i]])
            properties.append(l)

        feats = [ QgsFeature() for i in range(len(geoms)) ]
        for i, feat in enumerate(feats):
            feat.setGeometry(QgsGeometry.fromWkt(geoms[i]))
            feat.setAttributes(properties[i])
            #print(properties[i])
        return feats

#---------------------------------------------------------------------------

    def cargarPrediosEnComboDividir(self, listaPredios):
        
        self.DFS.dlg.comboPredios.clear()
        lista = []
        for predio in listaPredios:
            lista.append(str(predio.attributes()[1]))

        lista.sort()
        for elemento in lista:
            self.DFS.dlg.comboPredios.addItem(elemento)

