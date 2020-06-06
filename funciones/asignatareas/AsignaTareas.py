# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AsignaTareas
                                 A QGIS plugin
 Asignación de tareas
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-04-01
        git sha              : $Format:%H$
        copyright            : (C) 2020 by worknest
        email                : worknest@gmail.com
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
from PyQt5.QtWidgets import QAction
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from qgis.core import *

# Initialize Qt resources from file resources.py
from .resources import *
import os, json, requests
# Import the code for the dialog
from .AsignaTareas_dialog import AsignaTareasDialog
import os.path


class AsignaTareas:
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
        
        # Create the dialog (after translation) and keep reference
        # Intancias de variables        
        self.dlg = AsignaTareasDialog()
        self.UTI = None
        self.CFG = None
        self.currentPredios = None

        # ------- inicializacion de comportamientos
        self.dlg.cmbCvesSector.clear()
        self.dlg.cmbCvesManzana.clear()
        self.vaciarTabla(self.dlg.twPredios)
        self.vaciarTabla(self.dlg.twMazPred)

        self.dlg.gbClaves.hide()
        self.dlg.lComentarios.setGeometry(10, 110, 111, 16)
        self.dlg.pteComentarios.setGeometry(10, 133, 586, 151)
        self.dlg.pbAsignar.setGeometry(453, 302, 142, 41)

        self.dlg.setMinimumSize(624, 370)
        self.dlg.setMaximumSize(625, 371)
        self.dlg.resize(625, 371)
        
        # ocultar 
        self.dlg.twPredios.hideColumn(1)
        self.dlg.twMazPred.hideColumn(0)

        # ------- Conexion de EVENTOS
        self.dlg.cmbProcesos.currentIndexChanged.connect(self.event_cambioProceso)
        self.dlg.cmbActividades.currentIndexChanged.connect(self.event_cambioActividades)
        self.dlg.cmbTareas.currentIndexChanged.connect(self.event_cambioTareas)
        self.dlg.cmbUsuarios.currentIndexChanged.connect(self.event_cambioUsuarios)
        self.dlg.cmbCvesLocalidad.currentIndexChanged.connect(self.event_cambioLocalidades)
        self.dlg.cmbCvesSector.currentIndexChanged.connect(self.event_cambioSector)
        self.dlg.cmbCvesManzana.currentIndexChanged.connect(self.event_cambioManzana)
        self.dlg.pbAsignar.clicked.connect(self.evet_asignarTarea)
        self.dlg.btnMas.clicked.connect(self.event_btnMas)
        self.dlg.btnMenos.clicked.connect(self.event_btnMenos)
        self.dlg.chkTodoClaves.stateChanged.connect(self.marcarTodoClaves)
        self.dlg.chkTodoMazPred.stateChanged.connect(self.marcarTodoMazPred)

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()

        # carga Procesos
        self.obtenerProcesos()

        # obtener las localidades
        self.obtenerLocalidades()

        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    # -------- C O N S U L T A   W E B   S E R V I C E S --------

    def consultaWS(self, url = ''):

        # consulta de informacion procesos WS
        try:
            headers = { 'Content-Type': 'application/json', 'Authorization' : self.UTI.obtenerToken() }
            respuesta = requests.get(url, headers = headers)
        except requests.exceptions.RequestException:
            self.UTI.mostrarAlerta("Problemas al cargar la información de los procesos", QMessageBox().Critical, "Asignar tareas")

        return respuesta.json()

    # - asigna tarea
    def asignaTareaWS(self, asig, url):
        data = ""
        
        jsonGuarda = json.dumps(asig)
        
        try:
            self.headers['Authorization'] = self.UTI.obtenerToken()
            response = requests.post(url, headers = self.headers, data = jsonGuarda)
        except requests.exceptions.RequestException as e:
            self.createAlert("Error de servidor" + str(e) + "'", QMessageBox().Critical, "Error de servidor")
            return str(e)

        if response.status_code == 200:
            data = response.content
        else:
            self.createAlert('Error en peticion "asignaTareaWS()":\n' + response.text, QMessageBox().Critical, "Error de servidor")
            return response.text

        return 'OK'

    # -------- C O N S U L T A   W E B   S E R V I C E S   F I N A L --------

    # -------- M E T O D O S --------

    def obtenerProcesos(self):

        self.dlg.cmbProcesos.clear()
        self.dlg.cmbActividades.clear()
        self.dlg.cmbTareas.clear()
        self.dlg.cmbUsuarios.clear()

        # confimar la limpieza del combo
        self.dlg.cmbProcesos.clear()

        # obtiene en forma de lista la respuesta del servicio web
        data = self.consultaWS(self.CFG.url_procesos)
        lenJson = len(list(data))

        # si es que hay mas de un elemento en la lista
        if lenJson > 0:
            self.llenaCombos(data, self.dlg.cmbProcesos)
        else:
            # vacia todos los combos
            self.dlg.cmbProcesos.setEnabled(False)
            self.dlg.cmbActividades.setEnabled(False)
            self.dlg.cmbTareas.setEnabled(False)
            self.dlg.cmbUsuarios.setEnabled(False)

            self.UTI.mostrarAlerta("No existen procesos", QMessageBox().Information, "Asignación de tareas")

    def obtenerActividades(self, idProceso):

        if idProceso:
            # vacia todos los combos
            self.dlg.cmbTareas.setEnabled(False)
            self.dlg.cmbTareas.clear()
            self.dlg.cmbUsuarios.setEnabled(False)
            self.dlg.cmbUsuarios.clear()
            self.dlg.cmbActividades.clear()

            # obtiene en forma de lista la respuesta del servicio web
            data = self.consultaWS(self.CFG.url_actByProceso + str(idProceso))
            lenJson = len(list(data))

            # si es que hay mas de un elemento en la lista
            if lenJson > 0:
                self.llenaCombos(data, self.dlg.cmbActividades)
                self.dlg.cmbActividades.setEnabled(True)
            else:
                self.dlg.cmbActividades.setEnabled(False)
                self.UTI.mostrarAlerta("No existen actividades", QMessageBox().Information, "Asignación de tareas")

    def obtenerTareas(self, idActividad):

        if idActividad:
            # vacia todos los combos
            self.dlg.cmbUsuarios.setEnabled(False)
            self.dlg.cmbUsuarios.clear()
            self.dlg.cmbTareas.clear()

            # obtiene en forma de lista la respuesta del servicio web
            data = self.consultaWS(self.CFG.url_tareasByActividad + str(idActividad))
            lenJson = len(list(data))

            # si es que hay mas de un elemento en la lista
            if lenJson > 0:
                
                listaTemp = ['--Selecciona--']
                listaTempItems = [-1]
                
                for tarea in data:
                    listaTemp.append(str(tarea['descripcion']))
                    listaTempItems.append(tarea)

                modeloTemp = QStandardItemModel()
                for i,word in enumerate( listaTemp ):   
                    
                    item = QStandardItem(word)
                    modeloTemp.setItem(i, 0, item)

                self.UTI.extenderCombo_actualizado(self.dlg.cmbTareas, modeloTemp, listaTempItems)
                self.dlg.cmbTareas.model().item(0).setEnabled(False)
                self.dlg.cmbTareas.setEnabled(True)

            else:
                self.dlg.cmbTareas.setEnabled(False)
                self.UTI.mostrarAlerta("No existen tareas", QMessageBox().Information, "Asignación de tareas")

    def obtenerUsuarios(self, idTarea):

        if idTarea:
            self.dlg.cmbUsuarios.clear()
            self.dlg.cmbUsuarios.setEnabled(True)

            # obtiene en forma de lista la respuesta del servicio web
            data = self.consultaWS(self.CFG.url_usuarioByTarea + str(idTarea))
            lenJson = len(list(data))

            # si es que hay mas de un elemento en la lista
            if lenJson > 0:
                
                listaTemp = ['--Selecciona--']
                listaTempItems = [-1]
                
                for usuario in data:
                    listaTemp.append(str(usuario['nombre']) + ' ' + str(usuario['apellido']))
                    listaTempItems.append(usuario)

                modeloTemp = QStandardItemModel()
                for i,word in enumerate( listaTemp ):   
                    
                    item = QStandardItem(word)
                    modeloTemp.setItem(i, 0, item)

                self.UTI.extenderCombo_actualizado(self.dlg.cmbUsuarios, modeloTemp, listaTempItems)
                self.dlg.cmbUsuarios.model().item(0).setEnabled(False)
        else:
            # vacia todos los combos
            self.dlg.cmbUsuarios.setEnabled(False)
            self.dlg.cmbUsuarios.clear()

            self.UTI.mostrarAlerta("No existen usuarios", QMessageBox().Information, "Asignación de tareas")

    def obtenerLocalidades(self):

        # obtiene en forma de lista la respuesta del servicio web
        data = self.consultaWS(self.CFG.urlLocalidades)

        # llenar combos
        self.llenaCombosClaves(data, self.dlg.cmbCvesLocalidad)

    def obtenerSectores(self, idLocalidad):

        # consulta WS
        data = self.consultaWS(self.CFG.urlSectores + str(idLocalidad) + '/sector/')

        # llenar combos
        self.llenaCombosClaves(data, self.dlg.cmbCvesSector)

    def obtenerManzana(self, idSector):

        # consulta WS
        data = self.consultaWS(self.CFG.urlManzanas + str(idSector) + '/manzana/')

        # llenar combos
        self.llenaCombosClaves(data, self.dlg.cmbCvesManzana)

    def obtenerPredios(self, idManzana):

        # consulta WS
        data = self.consultaWS(self.CFG.urlPredios + str(idManzana) + '/predios/')
        self.currentPredios = data

        self.vaciarTabla(self.dlg.twPredios)

        # llenar tabla
        for x in range(0, len(data)):
            self.dlg.twPredios.insertRow(x)

            item = QtWidgets.QTableWidgetItem(str(data[x]['label']))
            item.setFlags( QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.dlg.twPredios.setItem(x, 0 , item)

            item = QtWidgets.QTableWidgetItem(str(data[x]['other']))
            item.setFlags( QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.dlg.twPredios.setItem(x, 1 , item)

    # llena con informacion consultada de los WS los combos utilizados y tambien define comportamientos del mismo
    def llenaCombos(self, data, combo):

        listaTemp = ['--Selecciona--']
        listaTempIds = [-1]
        
        for d in data:
            listaTemp.append(str(d['descripcion']))
            listaTempIds.append(d['id'])

        modeloTemp = QStandardItemModel()
        for i,word in enumerate( listaTemp ):   
            
            item = QStandardItem(word)
            modeloTemp.setItem(i, 0, item)

        self.UTI.extenderCombo_actualizado(combo, modeloTemp, listaTempIds)
        combo.model().item(0).setEnabled(False)

    # llena con informacion consultada de los WS los combos utilizados
    def llenaCombosClaves(self, data, combo):

        combo.clear()
        lenJson = len(list(data))

        combo.addItem('--Selecciona--', -1)

        # si es que hay mas de un elemento en la lista
        if lenJson > 0:
            for x in range(0, len(data)):
                combo.addItem(data[x]['label'])
                combo.setItemData(x + 1, data[x])

        #combo.setCurrentIndex(-1)
        combo.model().item(0).setEnabled(False)

    def vaciarTabla(self, tabla):
        tabla.clearContents()
        tabla.setRowCount(0)

    def marcarTodoClaves(self):
        if self.dlg.chkTodoClaves.checkState() == QtCore.Qt.Checked:
            if self.dlg.twPredios.rowCount() > 0:
                for c in range(0, self.dlg.twPredios.rowCount()):
                    self.dlg.twPredios.item(c, 0 ).setCheckState(QtCore.Qt.Checked)
            else:
                self.dlg.chkTodoClaves.setCheckState(QtCore.Qt.Unchecked)
        else:
            for c in range(0, self.dlg.twPredios.rowCount()):
                self.dlg.twPredios.item(c, 0 ).setCheckState(QtCore.Qt.Unchecked)

    def marcarTodoMazPred(self):
        if self.dlg.chkTodoMazPred.checkState() == QtCore.Qt.Checked:
            if self.dlg.twMazPred.rowCount() > 0:
                for c in range(0, self.dlg.twMazPred.rowCount()):
                    self.dlg.twMazPred.item(c, 1 ).setCheckState(QtCore.Qt.Checked)
            else:
                self.dlg.chkTodoMazPred.setCheckState(QtCore.Qt.Unchecked)
        else:
            for c in range(0, self.dlg.twMazPred.rowCount()):
                self.dlg.twMazPred.item(c, 1 ).setCheckState(QtCore.Qt.Unchecked)                

    # -------- M E T O D O S   F I N A L --------


    # -------- E V E N T O S --------

    def event_cambioProceso(self):
        # se obtiene el identificador del proceso
        idProceso = self.dlg.cmbProcesos.itemData(self.dlg.cmbProcesos.currentIndex())

        # cargar informacion de las ACTIVIDADES
        self.obtenerActividades(idProceso)

    def event_cambioActividades(self):
        # se obtiene el identificador del actividades
        idActividad = self.dlg.cmbActividades.itemData(self.dlg.cmbActividades.currentIndex())
        print('actividad', idActividad)

        # cargar informacion de las TAREAS
        self.obtenerTareas(idActividad)

    def event_cambioTareas(self):
        # se obtiene la tarea
        tarea = self.dlg.cmbTareas.itemData(self.dlg.cmbTareas.currentIndex())

        if tarea:

            # mostrar las claves
            if tarea['datosCartograficos']:               

                self.dlg.gbClaves.show()
                self.dlg.lComentarios.setGeometry(10, 402, 111, 16)
                self.dlg.pteComentarios.setGeometry(10, 422, 586, 71)
                self.dlg.pbAsignar.setGeometry(453, 502, 142, 41)

                self.dlg.setMinimumSize(624, 570)
                self.dlg.setMaximumSize(625, 571)
                self.dlg.resize(625, 571)

            else:
                # limpiar claves
                self.dlg.cmbCvesSector.clear()
                self.dlg.cmbCvesManzana.clear()
                self.vaciarTabla(self.dlg.twPredios)
                self.vaciarTabla(self.dlg.twMazPred)

                self.dlg.gbClaves.hide()
                self.dlg.lComentarios.setGeometry(10, 110, 111, 16)
                self.dlg.pteComentarios.setGeometry(10, 133, 586, 151)
                self.dlg.pbAsignar.setGeometry(453, 302, 142, 41)

                self.dlg.setMinimumSize(624, 370)
                self.dlg.setMaximumSize(625, 371)
                self.dlg.resize(625, 371)

            # carga informacion de los USUARIOS
            self.obtenerUsuarios(tarea['id'])

    def event_cambioUsuarios(self):
        # se obtiene el usuario
        usuario = self.dlg.cmbUsuarios.itemData(self.dlg.cmbUsuarios.currentIndex())

    def event_cambioLocalidades(self):
        # se obtiene la localidad seleccionada
        localidad = self.dlg.cmbCvesLocalidad.itemData(self.dlg.cmbCvesLocalidad.currentIndex())

        if(localidad):

            # limpiar campos
            self.dlg.cmbCvesSector.clear()
            self.dlg.cmbCvesManzana.clear()
            self.vaciarTabla(self.dlg.twPredios)

            if localidad == -1:
                return

            idLocalidad = localidad['value']

            # cargar sectores
            self.obtenerSectores(idLocalidad)

    def event_cambioSector(self):
        # se obtiene el sector seleccionado
        sector = self.dlg.cmbCvesSector.itemData(self.dlg.cmbCvesSector.currentIndex())

        if(sector):

            # limpiar campos
            self.dlg.cmbCvesManzana.clear()
            self.vaciarTabla(self.dlg.twPredios)

            if sector == -1:
                return

            idSector = sector['value']

            # cargar sectores
            self.obtenerManzana(idSector)

    def event_cambioManzana(self):
        # se obtiene la localidad seleccionada
        manzana = self.dlg.cmbCvesManzana.itemData(self.dlg.cmbCvesManzana.currentIndex())
        print('manzana', manzana)

        if(manzana):

            if manzana == -1:
                return

            idManzana = manzana['value']

            # cargar sectores
            self.obtenerPredios(idManzana)

    def evet_asignarTarea(self):

        # validaciones
        tarea = self.dlg.cmbTareas.itemData(self.dlg.cmbTareas.currentIndex())
        print('tareaaaaaaaaaaaa', tarea)
        if not tarea:
            self.UTI.mostrarAlerta("Selecciona una tarea", QMessageBox().Information, "Asignación de tareas")
            return

        if tarea == -1:
            self.UTI.mostrarAlerta("Selecciona una tarea", QMessageBox().Information, "Asignación de tareas")
            return

        usuario = self.dlg.cmbUsuarios.itemData(self.dlg.cmbUsuarios.currentIndex())
        print('usuarioooo', usuario)
        if not usuario:
            self.UTI.mostrarAlerta("Selecciona un usuario", QMessageBox().Information, "Asignación de tareas")
            return

        if usuario == -1:
            self.UTI.mostrarAlerta("Selecciona un usuario", QMessageBox().Information, "Asignación de tareas")
            return

        manzana = ""
        predio = ""
        if tarea['datosCartograficos']:
            # comienza validacion de claves - se deben de seleccionar hasta la manzana
            mza = self.dlg.cmbCvesManzana.itemData(self.dlg.cmbCvesManzana.currentIndex())
            if not mza:
                self.UTI.mostrarAlerta("Selecciona una manzana", QMessageBox().Information, "Asignación de tareas")
                return
            if mza  == -1:
                self.UTI.mostrarAlerta("Selecciona una manzana", QMessageBox().Information, "Asignación de tareas")
                return

            print('manzanaaaaaa' ,mza)
            manzana = mza['other']


        # prepara peticion
        data = {}
        data['comentario'] = self.dlg.pteComentarios.toPlainText()
        data['idTareaProcAct'] = tarea['id']
        data['idUsuarioAsignado'] = usuario['id']

        print(data, '++++++++++++++++++++++++++++++++++++++++++++++++++++')
        if tarea['datosCartograficos']:
            pass
            

        # self.asignaTareaWS(data, url)

    def event_btnMas(self):

        # validaciones
        if self.dlg.twPredios.rowCount() == 0:
            self.UTI.mostrarAlerta("Selecciona una manzana", QMessageBox().Information, "Asignación de tareas")
            return

        items = []
        itemsT = []
        indexs = []

        # obtiene los items seleccionados por los checks
        for c in range(0, self.dlg.twPredios.rowCount()):
            if self.dlg.twPredios.item(c, 0 ).checkState() == QtCore.Qt.Checked:
                iT = {}
                iT['clave'] = self.dlg.twPredios.model().index(c, 1).data()
                iT['predio'] = self.dlg.twPredios.model().index(c, 0).data()

                # items.append(self.dlg.twPredios.model().index(c).data())
                itemsT.append(iT)
                indexs.append(c)

        '''
        if len(indexs) == 0:
            self.UTI.mostrarAlerta("Selecciona al menos un predio", QMessageBox().Information, "Asignación de tareas")
            return
        '''

        # llenar el otro table widget
        mza = self.dlg.cmbCvesManzana.itemData(self.dlg.cmbCvesManzana.currentIndex())
        
        manzana = mza['label']
        cveMza = mza['other']

        # leer los items dentro de twMazPred para obtener los predios
        lt = []
        for c in range(0, self.dlg.twMazPred.rowCount()):
            lt.append(self.dlg.twMazPred.model().index(c, 0).data() + self.dlg.twMazPred.model().index(c, 2).data())

        print(lt)

        for it in itemsT:
            if it['clave'] not in lt:
                items.append(it)

        indexs.sort(reverse = True)
        # eliminar los items del tableWidget
        for i in indexs:
            self.dlg.twPredios.removeRow(i)

        for x in range(0, len(items)):

            # se agrega la fila completa
            rowCount = self.dlg.twMazPred.rowCount()
            self.dlg.twMazPred.insertRow(rowCount)
            rowCount = self.dlg.twMazPred.rowCount()

            # se define cada item de la fila con su propio contenido y comportamiento
            item = QtWidgets.QTableWidgetItem(str(cveMza))
            item.setFlags( QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.dlg.twMazPred.setItem(rowCount - 1, 0 , item)

            item = QtWidgets.QTableWidgetItem(str(manzana))
            item.setFlags( QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.dlg.twMazPred.setItem(rowCount - 1, 1 , item)

            item = QtWidgets.QTableWidgetItem(str(items[x]['predio']))
            item.setFlags( QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.dlg.twMazPred.setItem(rowCount - 1, 2 , item)

        # cuando se selecciona unicament la manzana
        if len(items) == 0:
            print(cveMza, manzana)
            
            rowCount = self.dlg.twMazPred.rowCount()

            self.dlg.twMazPred.insertRow(rowCount)
            rowCount = self.dlg.twMazPred.rowCount()
            # se define cada item de la fila con su propio contenido y comportamiento
            item = QtWidgets.QTableWidgetItem(str(cveMza))
            item.setFlags( QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.dlg.twMazPred.setItem(rowCount - 1, 0 , item)

            item = QtWidgets.QTableWidgetItem(str(manzana))
            item.setFlags( QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.dlg.twMazPred.setItem(rowCount - 1, 1 , item)

            item = QtWidgets.QTableWidgetItem('')
            item.setFlags( QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.dlg.twMazPred.setItem(rowCount - 1, 2 , item)
            
            
    def event_btnMenos(self):
        
        if not self.currentPredios:
            return

        print('predios------', self.currentPredios)
        mza = self.dlg.cmbCvesManzana.itemData(self.dlg.cmbCvesManzana.currentIndex())
        print(mza)


        indexs = []
        lt = []
        # obtiene los items seleccionados por los checks
        for c in range(0, self.dlg.twMazPred.rowCount()):
            # False
            if self.dlg.twMazPred.item(c, 1 ).checkState() != QtCore.Qt.Checked:
                lt.append(self.dlg.twMazPred.model().index(c, 0).data() + self.dlg.twMazPred.model().index(c, 2).data())
            else:
                # True
                indexs.append(c)

        if len(indexs) == 0:
            self.UTI.mostrarAlerta("Selecciona al menos una clave", QMessageBox().Information, "Asignación de tareas")
            return

        data = []
        for x in range(0, len(self.currentPredios)):
            if self.currentPredios[x]['other'] not in lt:
                data.append(self.currentPredios[x])

        self.vaciarTabla(self.dlg.twPredios)

        # llenar tabla
        for x in range(0, len(data)):
            self.dlg.twPredios.insertRow(x)

            item = QtWidgets.QTableWidgetItem(str(data[x]['label']))
            item.setFlags( QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.dlg.twPredios.setItem(x, 0 , item)

            item = QtWidgets.QTableWidgetItem(str(data[x]['other']))
            item.setFlags( QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.dlg.twPredios.setItem(x, 1 , item)


        # eliminar los registros activos en twMazPred
        indexs.sort(reverse = True)
        # eliminar los items del tableWidget
        for i in indexs:
            self.dlg.twMazPred.removeRow(i)

    # -------- E V E N T O S   f I N A L--------