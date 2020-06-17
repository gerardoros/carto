# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VentanaClavesV3
                                 A QGIS plugin
 VentanaClavesV3
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2018-07-03
        git sha              : $Format:%H$
        copyright            : (C) 2018 by VentanaClavesV3
        email                : VentanaClavesV3
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
from PyQt5.QtWidgets import QAction

from .resources import *
from .VentanaClavesV3_dialog import VentanaClavesV3Dialog
import os.path

from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt, QSize
from PyQt5.QtGui import QIcon, QColor, QCursor, QPixmap
from PyQt5.QtWidgets import QAction, QWidget,QVBoxLayout, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QTextEdit, QLineEdit
from PyQt5 import QtWidgets
from PyQt5 import QtCore

from qgis.core import *
from qgis.utils import iface, loadPlugin, startPlugin, reloadPlugin
from qgis.gui import QgsLayerTreeView, QgsMapToolEmitPoint, QgsMapTool, QgsRubberBand, QgsVertexMarker

import os.path
import os, json, requests, sys
from osgeo import ogr, osr


class VentanaClavesV3:
    """QGIS Plugin Implementation."""

    def __init__(self, iface, pluginDFS):
        
        self.dlg = VentanaClavesV3Dialog(pluginV=self, parent = iface.mainWindow())
        self.DFS = pluginDFS
        self.capaPredio = None

        self.predioOriginal = None

        self.seleccion = None

        self.primeraVez = True
        self.dlg.btnAutomatico.clicked.connect(self.asignacionAutomatica)

        self.dlg.btnClave.clicked.connect(self.asignacionDesManual)
        self.dlg.btnCompletar.clicked.connect(self.completarSubdivision)
        self.dlg.btnDesasignarTodo.clicked.connect(self.desasignarTodasClaves)
        self.subCompleta = False

#------------------------------------------------------------------
    
    def asignacionAutomatica(self):
        
        # inicializa la capa de predios
        self.obtieneCapaPredios()

        self.capaPredio.startEditing()
        
        # predios a asignar clave
        totalPredios = []
        cvesPredios = []
        for predio in self.capaPredio.getFeatures():
            if predio['clave'] == '':
                totalPredios.append(predio)
            else:
                cvesPredios.append(int(predio['clave']))

        cvesPredios.sort(reverse=True)
        nCve = cvesPredios[0] + 1
        primera = True

        for i in range(0, len(totalPredios)):
            feat = totalPredios[i]

            if primera:
                clave = self.predioOriginal['clave']
                feat['clave'] = f'{int(clave):05}'

                if int(clave) == nCve:
                    nCve = nCve + 1

                primera = False
            else:
                feat['clave'] = f'{nCve:05}'

                # clave anterior
                feat['cve_cat_ant'] = self.predioOriginal['cve_cat']
                nCve = nCve + 1

            feat['cve_cat'] = self.predioOriginal['cve_cat'][0:20] + feat['clave']

            self.capaPredio.updateFeature(feat)

        
        self.capaPredio.removeSelection()
        self.DFS.UTI.mostrarAlerta('Claves asignadas', QMessageBox().Information, 'Claves asignadas')

        self.capaPredio.triggerRepaint()
        self.capaPredio.commitChanges()

#------------------------------------------------------------------

    def cargarAsignacionManual(self):

        # inicializa la capa de predios
        self.obtieneCapaPredios()

        self.seleccion = self.capaPredio.selectedFeatures()
        self.dlg.txtClave.setText('')

        if len(self.seleccion) == 1:

            seleccion = self.seleccion[0]
            claveAsignada = seleccion['clave']
            
            
            if seleccion.geometry().asWkt() in self.DFS.listaNuevosPredios: #Cuando es predio nuevo

                #self.dlg.btnClave.setEnabled(True)
                if claveAsignada == '':
                    self.dlg.txtClave.setEnabled(True)
                    self.dlg.btnClave.setEnabled(True)
                else:
                    self.dlg.txtClave.setEnabled(True)
                    self.dlg.btnClave.setEnabled(True)
                    self.dlg.txtClave.setText(claveAsignada)
            else: #Cuando NO es predio nuevo

                self.dlg.txtClave.setEnabled(False)
                self.dlg.btnClave.setEnabled(False)
                
        else: #Cuando la seleccion esta vacia

            self.dlg.txtClave.setEnabled(False)
            self.dlg.btnClave.setEnabled(False)

#--------------------------------------------------------------

    def asignacionDesManual(self):
        
        # inicializa la capa de predios
        self.obtieneCapaPredios()

        # valida la seleccion de un predio
        if self.seleccion is None:
            self.DFS.UTI.mostrarAlerta('Seleccione un predio', QMessageBox().Information, 'Aviso')
            return

        clave = self.seleccion[0]['clave']

        # valida clave a asignar
        if self.dlg.txtClave.text() == '':
            self.DFS.UTI.mostrarAlerta('Defina la clave a asignar', QMessageBox().Information, 'Clave asignada')
            return

        texto = self.dlg.txtClave.text()

        # valida que sean solo numeros
        if not self.DFS.UTI.esEntero(texto):
            self.DFS.UTI.mostrarAlerta('La clave a asignar debe contener solo números', QMessageBox().Information, 'Clave asignada')
            return

        # prepara la clave
        clave = f'{int(texto):05}'

        # validar claves repetidas
        for feat in self.capaPredio.getFeatures():
            if feat['clave'] == clave:
                self.DFS.UTI.mostrarAlerta('La clave se encuentra repetida', QMessageBox().Information, 'Clave asignada')
                return

        # asigna la clave al predio 
        self.capaPredio.startEditing()
        self.seleccion[0]['clave'] = clave
        self.seleccion[0]['cve_cat'] = self.predioOriginal['cve_cat'][0:20] + clave
        self.seleccion[0]['cve_cat_ant'] = self.predioOriginal['cve_cat']

        self.capaPredio.updateFeature(self.seleccion[0])
        self.capaPredio.triggerRepaint()
        self.capaPredio.commitChanges()

        self.dlg.txtClave.setText(clave)

        self.DFS.UTI.mostrarAlerta("Proceso correcto", QMessageBox().Information, 'Clave asignada')


#---------------------------------------------------------------------------------

    def completarSubdivision(self):

        # inicializa la capa de predios
        self.obtieneCapaPredios()
        bandera = True

        for feat in self.capaPredio.getFeatures():
            if feat.geometry().asWkt() in self.DFS.listaNuevosPredios:
                if feat['clave'] == '':
                    bandera = False
                    break
        
        if bandera:

            bandera = False
            for feat in self.capaPredio.getFeatures():
                
                if feat['clave'] == self.DFS.predioEnDivision['clave']:
                    bandera = True
                    break

            if bandera:
                self.DFS.UTI.mostrarAlerta('Subdivision completa', QMessageBox().Information, 'Subdivision completa, Parte 2 de 2')
                self.dlg.close()

                self.DFS.enClaves = False
                self.DFS.enSubdivision = False

                self.DFS.dlg.close()
                self.primeraVez = True
                self.DFS.enClaves = False
                self.subCompleta = True
                self.dlg.close()
                self.subCompleta = False
                self.DFS.VentanaAreas.close()
                self.DFS.vaciarRubbers()
            else:
                self.DFS.UTI.mostrarAlerta('No puedes continuar hasta que un predio contenga la clave: ' + str(self.DFS.predioEnDivision['clave']), QMessageBox().Critical, 'Error al completar subdivision')
        else:
            self.DFS.UTI.mostrarAlerta('No puedes continuar hasta que todos los predios resultados de la subdivision\ntengan clave asignada', QMessageBox().Critical, 'Error al completar subdivision')

#--------------------------------------------------------------------------------------

    def desasignarTodasClaves(self):

        # inicializa la capa de predios
        self.obtieneCapaPredios()

        for feat in self.capaPredio.getFeatures():
            if feat.geometry().asWkt() in self.DFS.listaNuevosPredios:
                self.capaPredio.startEditing()
                feat['clave'] = ''
                feat['id'] = None
                feat['cve_cat'] = ''
                self.capaPredio.updateFeature(feat)
                self.capaPredio.triggerRepaint()
                self.capaPredio.commitChanges()
                self.dlg.txtClave.setText('')

#----------------------------------------------------------------------------------------------

    '''
    def cargarDelCombo(self):

        #if len(self.seleccion) == 1:
        self.entradaLibre = self.dlg.cmbClaves.currentIndex() == 0
        
        self.dlg.txtClave.setEnabled(self.entradaLibre)
        
        if self.primeraVez:
            self.dlg.txtClave.setEnabled(False)
            self.primeraVez = False
    '''
    
#----------------------------------------------------------
    '''
    def rellenarClaves(self):

        try:
            idp = self.DFS.predioEnDivision['clave']
            self.listaClaves = [ 'ENTRADA MANUAL', str(idp), '10101', '20202', '30303']
        except:
            return
    '''

    def obtieneCapaPredios(self):

        '''
        if self.capaPredio is not None:
            return
        '''

        self.capaPredio = QgsProject.instance().mapLayer(self.DFS.ACA.obtenerIdCapa('predios.geom'))

        if self.capaPredio:
            self.capaPredio.selectionChanged.connect(self.cargarAsignacionManual)