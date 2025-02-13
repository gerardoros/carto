
import os, json, requests

from PyQt5 import uic
from PyQt5 import QtWidgets

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QMessageBox

from .agregarRoles_usuario import agregarRoles_usuario

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'verEditarUsuarios.ui'))

class usuariosEdicionVer(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, usuario = None, nuevo = False, edicion = False, CFG = None, UTI = None, parent=None):
        """Constructor."""
        super(usuariosEdicionVer, self).__init__(parent, \
            flags=Qt.WindowCloseButtonHint)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect

        # usuario a mostrar
        self.usuario = usuario
        self.nuevo = nuevo
        self.edicion = edicion
        self.listaServicios = []
        self.CFG = CFG
        self.UTI = UTI
        #self.nuevalista = []l

        # -- informacion cargada
        self.cargada = False

        self.headers = {'Content-Type': 'application/json'}
        self.setupUi(self)

    def showEvent(self, event):

        if self.cargada:
            return

        # -- Eventos
        self.btnOk.clicked.connect(self.event_aceptar)
        self.btnCancelar.clicked.connect(self.event_cancelar)
        self.btnAgregaRoles.clicked.connect(self.event_agregaRoles)

        # -- Iniciarlizaciones
        # ver y editar
        if not self.nuevo:
            self.lbContrUno.hide()
            self.mleContrUno.hide()
            self.lbContrDos.hide()
            self.mleContrDos.hide()
        else:
            self.cbActivado.hide()

        # editar y nuevo
        self.habilitaControles(self.edicion)

        # llenar los campos
        if self.usuario:
            self.llenaUsuario(self.usuario)

        self.dlg.twRoles.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.dlg.twRoles.setSortingEnabled(True)
        self.dlg.twRoles.setColumnWidth(1,349)
        
        self.cargada = True

    # --- E V E N T O S   Dialog ---

    # - boton presionado dentro de la lista
    def event_currentPositionButtonPressed(self):

        clickme = QtWidgets.qApp.focusWidget()
        # or button = self.sender()
        index = self.dlg.twRoles.indexAt(clickme.pos())

        if index.isValid():
            self.dlg.twRoles.removeRow(index.row())

    def event_agregaRoles(self):

        # consultar los roles
        self.roles = self.consumeWSGeneral(url_cons = self.CFG.url_AU_getAllAuthorities)

        if not self.roles:
            return
        # tenemos la lista asi ['ROLE_ADMIN', 'ROLE_USER', 'ROLE_GENERAL', 'LINDEROS']

        # con un for recorrer la lista de roles

        # con cada iteracion consumir el servicio web con el rol
        #http://201.165.150.64:8080/autentificacion/api/account/permisos-carto-user-distinct/<ROL>
        self.nuevalista = []
        # de la listaque regrese el servicio filtrar las operaciones para al final tener una lista con roles y operaciones
        for x in range(0,len(self.roles)):
            n={}
            self.listaServicios = self.consumeWSGeneral(url_cons = self.CFG.url_AU_getAllRole + self.roles[x])
            n['rol'] = self.roles[x]
            comas = ''
            for i in range(0,len(self.listaServicios)):
                if self.listaServicios[i]['asignado'] == True:
                    comas = comas + self.listaServicios[i]['nombre'] + ','

            n['operaciones'] = comas[:-1]

            self.nuevalista.append(n)

        
        '''nuevalista = []

        for recorrer lista de roles:
            listaServicios = self.consumeWSGeneral(url_cons = self.CFG.url_AU_getAllAuthorities + el rol de la iteracion)

            n['rol'] = rol de iteracion
            comas = ''
            for recorrer la listaServicios

                comas = la concatenacion de las operaciones que tengan True

            n['operaciones'] = comas

        nuevalista.append(n)'''

        # al final tendras la lista de roles con operaciones
        # y esa lista la utilizaras para llenar la tabla del otro formario pasandola por parametros
        # obj = agregarRoles_usuario(nuevalista, CFG = self.CFG, UTI = self.UTI)
        # despues se tendran que hacer los debidos cambios en el formulario de agregarRoles para que se vean los roles con 
            # sus operaciones






        if not self.roles:
            return

        # manda a abrir el formulario (parametros: self.roles, self.CFG, self.UTI)
        obj = agregarRoles_usuario(self.nuevalista, CFG = self.CFG, UTI = self.UTI)
        respuesta = obj.exec()

        # regresa un 0 o un 1
        # 0 = RECHAZADO = CANCELAR
        # 1 = ACEPTADO  = ACEPTAR
        if respuesta == 0:
            return

        # agregar los roles seleccionados 
        # validar si se repiten
        rolesNuevos = obj._seleccionados

        # lista de los roles actuales
        rolesAct = []

        if self.dlg.twRoles.rowCount() > 0:
            allRows = self.dlg.twRoles.rowCount()
            for row in range(0, allRows):
                item = self.dlg.twRoles.item(row, 0)
                item2 = self.dlg.twRoles.item(row, 1)

                m = {}
                m['rol'] = item.text()
                m['opreaciones'] = item2.text()

                rolesAct.append(m)

        # se combinan quitando duplicados
        # lista = list(set(rolesNuevos + rolesAct))

        print(rolesAct)
        print(rolesNuevos)

        for l in rolesAct:
            rolesNuevos.append(l)

        #lista = rolesAct.extend(rolesNuevos)
        print(rolesNuevos)

        # limpiar qTableWidget
        self.dlg.twRoles.clearContents()
        self.dlg.twRoles.setRowCount(0)
            
        for row in range(0, self.dlg.twRoles.rowCount()):        
            self.dlg.twRoles.removeRow(row) 

        # se agrega a la lista
        self.llenaRoles(rolesNuevos)


    def event_aceptar(self, nuevo):

        #if self.nuevo:
        if nuevo:
            # valida constraseña
            # valida campos llenos
            cont1 = self.dlg.mleContrUno.text()
            cont2 = self.dlg.mleContrDos.text()

            if len(cont1) < 5:
                self.createAlert('La constraseña debe de tener al menos 5 caracteres', QMessageBox().Warning)
                return
            
            if cont1 != cont2:
                self.createAlert('Vuelva a escribir la constraseña', QMessageBox().Warning)
                return

        nombre = self.dlg.leNombres.text()
        apellido = self.dlg.leApellidos.text()
        usuario = self.dlg.leUsuario.text()
        correo = self.dlg.leCorreo.text()

        activado = self.dlg.cbActivado.isChecked()

        if len(nombre) == 0:
            self.createAlert('Defina el (los) nombre (s)', QMessageBox().Warning)
            return

        if len(apellido) == 0:
            self.createAlert('Defina el (los) apellido (s)', QMessageBox().Warning)
            return

        if len(usuario) == 0:
            self.createAlert('Defina el usuario', QMessageBox().Warning)
            return

        if len(correo) == 0:
            self.createAlert('Defina el correo', QMessageBox().Warning)
            return

        if ' ' in usuario:
            self.createAlert('Usuario con espacios en blanco', QMessageBox().Warning)
            return

        roles = []

        allRows = self.dlg.twRoles.rowCount()
        for row in range(0, allRows):
            item = self.dlg.twRoles.item(row, 0)
            roles.append(item.text())

        envio = {}
        envio['authorities'] = roles
        envio['email'] = correo
        envio['firstName'] = nombre
        envio['lastName'] = apellido
        envio['login'] = usuario
        envio['password'] = None if not self.nuevo else cont1
        envio['id'] = None if not self.usuario else self.usuario['id']
        envio['activated'] = activado

        # enviar al ws
        resp = self.guardaUsuario(nuevo = self.nuevo, url = (self.CFG.url_AU_creaUsuario if self.nuevo else self.CFG.url_AU_actualizaUsuario), envio = envio)

        if resp == 'OK':
            self.createAlert('Usuario ' + ('Creado' if self.nuevo else 'Actualizado') + ' Correctamente', QMessageBox().Information)
        else:
            return

        #self.accept()

    # -- cancelar la fusion de fracciones
    def event_cancelar(self):
        self.reject()

    # --- E V E N T O S   Dialog ---

    # --- M E T O D O S   Dialog ---

    def habilitaControles(self, booleano = False):
        self.leNombres.setReadOnly(not booleano)
        self.leApellidos.setReadOnly(not booleano)
        self.cbActivado.setEnabled(booleano)
        self.leUsuario.setReadOnly(not booleano)
        self.leCorreo.setReadOnly(not booleano)

        self.btnAgregaRoles.setEnabled(booleano)
        #self.btnCancelar.setEnabled(booleano)
        self.btnOk.setEnabled(booleano)

        if not booleano:
            self.btnCancelar.setText('Cerrar')
            self.btnOk.hide()
        else:
            self.btnCancelar.setText('Cancelar')

    # - Crea una alerta para ser mostrada como ventana de advertencia
    def createAlert(self, mensaje, icono = QMessageBox().Critical, titulo = 'Usuarios'):
        #Create QMessageBox
        self.msg = QMessageBox()
        #Add message
        self.msg.setText(mensaje)
        #Add icon of critical error
        self.msg.setIcon(icono)
        #Add tittle
        self.msg.setWindowTitle(titulo)
        #Show of message dialog
        self.msg.show()
         # Run the dialog event loop
        result = self.msg.exec_()

    def llenaUsuario(self, usuario):

        self.leNombres.setText(usuario['firstName'])
        self.leApellidos.setText(usuario['lastName'])
        self.leUsuario.setText(usuario['login'])
        self.leCorreo.setText(usuario['email'])

        self.cbActivado.setChecked(usuario['activated'])

        # llena roles
        self.llenaRoles(self.usuario['authorities'])
        
    def llenaRoles(self, roles = []):
        # llena roles
        self.dlg.twRoles.setRowCount(len(roles))

        for i in range(0, len(roles)):
            
            btnRol = QtWidgets.QPushButton('Quitar')
            btnRol.setEnabled(self.edicion)
            btnRol.setStyleSheet('''QPushButton{
                                background : rgb(174, 116, 0);
                                color : rgb(255, 255, 255);
                                font-weight: bold;
                                }
                                QPushButton::disabled {
                                background : rgb(187, 129, 13);
                                color : rgb(245,245,245);
                                border: 1px solid #adb2b5;
                                }''')

            self.dlg.twRoles.setItem(i, 0, QtWidgets.QTableWidgetItem(roles[i]['rol']))
            self.dlg.twRoles.setItem(i, 1, QtWidgets.QTableWidgetItem(roles[i]['opreaciones']))
            self.dlg.twRoles.setCellWidget(i, 2, btnRol)

            btnRol.clicked.connect(self.event_currentPositionButtonPressed)
    # --- M E T O D O S   Dialog ---

    # --- S E R V I C I O S   W E B  ---

    # - manda al wsroles un predio a guardar
    def guardaUsuario(self, nuevo = False, url = '', envio = {}):
        data = ""
        
        # envio - el objeto de tipo dict, es el json que se va a guardar
        # se debe hacer la conversion para que sea aceptado por el servicio web
        jsonEnv = json.dumps(envio)
        
        try:
            # header para obtener el token
            self.headers['Authorization'] = self.UTI.obtenerToken()

            if nuevo:
                response = requests.post(url, headers = self.headers, data = jsonEnv)
                print(response)
            else:

                # ejemplo con put, url, header y body o datos a enviar
                response = requests.put(url, headers = self.headers, data = jsonEnv)

        except requests.exceptions.RequestException as e:
            self.createAlert("Error de servidor, 'guardaUsuario()' '" + str(e) + "'", QMessageBox().Critical, "Error de servidor")
            return str(e)

        if response.status_code == 403:
            self.createAlert('Sin Permisos para ejecutar la accion', QMessageBox().Critical, "Usuarios")
            return None
 
           
        elif response.status_code >= 300:
            #self.createAlert('Error en peticion "guardaUsuario()":\n' + response.text, QMessageBox().Critical, "Error de servidor")
            if response.text[170:188] == '"error.userexists"':
                self.createAlert('El usuario ya existe', QMessageBox().Critical, "Usuarios")
            if response.text[179:198] == '"error.emailexists"':
                self.createAlert('El correo electrónico ya existe', QMessageBox().Critical, "Usuarios")
            return response.text

        return 'OK'

    # - consume ws para informacion de catalogos
    def consumeWSGeneral(self, url_cons = ""):

        url = url_cons
        data = ""

        try:
            self.headers['Authorization'] = self.UTI.obtenerToken()
            response = requests.get(url, headers = self.headers)
        except requests.exceptions.RequestException as e:
            self.createAlert("Error de servidor--, 'consumeWSGeneral()' '" + str(e) + "'", QMessageBox().Critical, "Error de servidor")
            return

        if response.status_code == 200:
            data = response.content
           
        elif response.status_code == 403:
            self.createAlert('Sin Permisos para ejecutar la acción', QMessageBox().Critical, "Usuarios")
            return None
           
        else:
            self.createAlert('Error en peticion "consumeWSGeneral()":\n' + response.text, QMessageBox().Critical, "Error de servidor")
            return

        return json.loads(data)

    # --- S E R V I C I O S   W E B   CIERRA ---