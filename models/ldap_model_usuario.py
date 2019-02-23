# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from distutils.command.config import config
import re
from odoo import api, fields, models, registry, SUPERUSER_ID
import ldap
import ldap.modlist as modlist
import hashlib
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


# modelo para manejar los usaurios
class LdapUsuario(models.Model):
    _inherit = 'usermanagement.usuario'
    nombre = fields.Char('Nombre', required=True,compute = "_calcular_ldap", store = False)
    apellidos = fields.Char('Apellidos', required=True,compute = "_calcular_ldap", store = False)
    correo = fields.Char('Correo', required=True, compute = "_calcular_ldap", store = False)
    cuota = fields.Integer('Cuota', compute = "_calcular_ldap", store = False)
    carnet_identidad = fields.Char('Carnet de Identidad', size=11)
    @api.multi
    def _calcular_ldap(self):
        Ldap = self.env['res.company.ldap']
        for conf in Ldap.get_ldap_dicts():
            l = Ldap.connect(conf)
            l.protocol_version = ldap.VERSION3
            # l.set_option(ldap.OPT_REFERRALS, 0)vc
            ldap_password = conf['ldap_password'] or ''
            ldap_binddn = conf['ldap_binddn'] or ''
            try:
                l.simple_bind_s(ldap_binddn.encode('utf-8'),
                                ldap_password.encode('utf-8'))
            except ldap.LDAPError, e:
                    raise ValidationError("Error con el LDAP")
                    _logger.error("Error cargando los datos \"%s\" " % e)
            base = "OU=Usuarios,dc=uo,dc=edu,dc=cu"

            attributes = ['mail','givenName','sn','departmentNumber','title']
            for record in self:
                criteria = "(sAMAccountName=" + record.nombre_usuario + ")"
                result = l.search_st(base, ldap.SCOPE_SUBTREE, criteria, attributes)
                if result:
                    if result[0][1]:
                        if 'mail' in result[0][1]:
                            record.correo= result[0][1]['mail'][0].decode('utf-8').encode('utf-8')
                        record.nombre = result[0][1]['givenName'][0].decode('utf-8').encode('utf-8')
                        record.apellidos = result[0][1]['sn'][0].decode('utf-8').encode('utf-8')

                        if 'departmentNumber' in result[0][1]:
                            try:
                                if result[0][1]['departmentNumber'][0][:-4].strip() != '':
                                    record.cuota = int(result[0][1]['departmentNumber'][0][:-4].strip())
                                    if result[0][1]['departmentNumber'][0].find('g') > 0:
                                        cuota = int(result[0][1]['departmentNumber'][0][:-4].strip())
                                        record.cuota = cuota * 1024
                                else:
                                    record.cuota = 0
                            except ValueError:
                                _logger.error(
                                    "Cuota invalida!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\"%s\" " % result[0][1]['departmentNumber'][0][:-4].strip())
                                _logger.error(
                                    "Usuario!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\"%s\" " %
                                    self.nombre_usuario)

                        else:
                            record.cuota = 0
                        if 'title' in result[0][1]:
                            record.carnet_identidad = result[0][1]['title'][0]

    @api.model
    @api.returns('self', lambda rec: rec.id)
    def create(self, values):
        rec = False
        Ldap = self.env['res.company.ldap']
        for conf in Ldap.get_ldap_dicts():
            l = Ldap.connect(conf)
            l.protocol_version = ldap.VERSION3
            # l.set_option(ldap.OPT_REFERRALS, 0)vc
            ldap_password = conf['ldap_password'] or ''
            ldap_binddn = conf['ldap_binddn'] or ''
            try:
                l.simple_bind_s(ldap_binddn.encode('utf-8'),
                                ldap_password.encode('utf-8'))
            except ldap.LDAPError, e:
                raise ValidationError(
                    'No se puede conectar con el Servidor LDAP,pruebe mas tarde.')
            base = "OU=Usuarios,dc=uo,dc=edu,dc=cu"
            # criteria = "(sAMAccountName=david.montero)"
            attributes = ['cn']
            criteria = "objectClass=person"
            attrs = {}

            attrs['objectclass'] = ['top', 'person',
                'organizationalPerson', 'user']
            attrs['instanceType'] = "4"

            # if "area_id" in values:
            # attrs['department'] = self.env['usermanagement.area'].browse(values["area_id"]).nombre.encode('utf-8')
            # _logger.error("nuevos \"%s\" " % self.env['usermanagement.area'].browse(values["area_id"]).nombre)
            importar = False
            Ldap = self.env['res.company.ldap'].search([])
            for conf in Ldap:
                if conf.inportar == True:
                    importar = True

            if importar == True:
                correo = values["correo"]
                nombre = values["nombre"]
                apellidos = values["apellidos"]
                direccion = values["direccion"]
                carnet = values["carnet_identidad"]
                nombre_usuario = values["nombre_usuario"]
                if "cuota" in values.keys():
                    cuota = values["cuota"]
                    attrs['departmentNumber'] = str(cuota)
                contrasena = values["contrasena"]
                values["contrasena"] = "Contrasena02++".encode('utf-8')
                values["confirmar_contrasena"] = "Contrasena02++".encode(
                    'utf-8')

            else:
                correo = values["correo"].encode('utf-8')
                nombre = values["nombre"].encode('utf-8')
                apellidos = values["apellidos"].encode('utf-8')
                direccion = ""
                if values["carnet_identidad"]:
                    carnet = values["carnet_identidad"].encode('utf-8')
                if values["pasaporte"]:
                    carnet = values["pasaporte"].encode('utf-8')
                nombre_usuario = values["nombre_usuario"].encode('utf-8')
                if "cuota" in values.keys():
                    cuota = values["cuota"]
                    attrs['departmentNumber'] = str(cuota) + "mb/w"
                if values["direccion"]:
                    direccion = values["direccion"].encode('utf-8')
                contrasena = values["contrasena"].encode('utf-8')
                values["contrasena"] = "Contrasena02++".encode('utf-8')
                values["confirmar_contrasena"] = "Contrasena02++".encode(
                    'utf-8')

            attrs['mail'] = correo
            attrs['name'] = nombre + " " + apellidos
            attrs['physicalDeliveryOfficeName'] = direccion
            attrs['title'] = carnet
            attrs['userPrincipalName'] = correo
            contrasena = "\"" + contrasena + "\""
            attrs['unicodePwd'] = contrasena.encode("UTF-16LE")

            login = nombre_usuario + ":Proxy UOnet:" + contrasena
            login = hashlib.md5(login).hexdigest()
            attrs['description'] = "Proxy UOnet:" + login
            attrs['cn'] = nombre + " " + apellidos
            attrs['sAMAccountname'] = nombre_usuario
            attrs['givenName'] = nombre
            attrs['sn'] = apellidos
            attrs['displayName'] = nombre + " " + apellidos
            attrs['userPrincipalName'] = correo
            #        attrs['jpegPhoto'] = values['foto'].decode('base64')

            # Some flags for userAccountControl property
            SCRIPT = 1
            ACCOUNTDISABLE = 2
            HOMEDIR_REQUIRED = 8
            PASSWD_NOTREQD = 32
            NORMAL_ACCOUNT = 512
            DONT_EXPIRE_PASSWORD = 65536
            TRUSTED_FOR_DELEGATION = 524288
            PASSWORD_EXPIRED = 8388608
            attrs['userAccountControl'] = str(NORMAL_ACCOUNT)
            importar = False
            Ldap = self.env['res.company.ldap'].search([])
            for conf in Ldap:
                if conf.inportar == True:
                    importar = True
            try:
                obj = self.search([('nombre_usuario', '=', nombre_usuario)])
                if obj:
                    raise ValidationError("El nombre de usuario ya existe.")
                rec = super(LdapUsuario, self).create(values)
                ldif = modlist.addModlist(attrs)
                dn = "CN=" + nombre + " " + apellidos + ",OU=Usuarios,dc=uo,dc=edu,dc=cu"
                _logger.error(
                    "Preparando para crear Usuario En el LDAP++++++++++++++++++++++++++++++++++++++++++\"%s\" " % nombre + " " + apellidos)
                _logger.error("Importar\"%s\" " % importar)
                if importar == False:
                    _logger.error(
                        "Creando Usuario En el LDAP!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\"%s\" " % nombre + " " + apellidos)
                    l.add_s(dn, ldif)
                # Agregarlo en los grupos

                if importar == False:
                    _logger.error("Valores\"%s\" " % values)
                    if values['grupo_ids']:
                        for g in values['grupo_ids'][0][2]:
                            grupo=self.env['usermanagement.grupo'].browse(g)
                            l.modify_s("CN=" + grupo.nombre.encode('utf-8') + ",OU=GRUPOS,dc=uo,dc=edu,dc=cu",
                                       [(ldap.MOD_ADD, 'member',
                                         'CN=' + values["nombre"].encode('utf-8') + " " + values["apellidos"].encode(
                                             'utf-8') + ',OU=Usuarios,dc=uo,dc=edu,dc=cu')])
                    if values['servicio_ids']:
                        for s in values['servicio_ids'][0][2]:
                            servicio=self.env['usermanagement.servicio'].browse(
                                s)
                            _logger.error("new_rec Valor \"%s\" " % rec)
                            l.modify_s("CN=" + servicio.nombre.encode('utf-8') + ",OU=Servicios,dc=uo,dc=edu,dc=cu",
                                       [(ldap.MOD_ADD, 'member',
                                         'CN=' + values["nombre"].encode('utf-8') + " " + values[
                                             "apellidos"].encode(
                                             'utf-8') + ',OU=Usuarios,dc=uo,dc=edu,dc=cu')])

            except ldap.LDAPError, e:
                _logger.error("Error a Creando el usuario \"%s\" " % e)
                raise ValidationError("No se pudo crear el usuario")
            _logger.error("Creando Usuario \"%s\" " % nombre + " " + apellidos)
            l.unbind()
        return rec

    # Metodo que interviene al modificar un usuario y registra datos en la clase RegistroActividades al modificar un usuario
    @api.multi
    @api.model
    def write(self, values, context=None):
        if "nombre_usuario" in values:
            nombre_usuario=values["nombre_usuario"]
            obj=self.search([('nombre_usuario', '=', nombre_usuario)])
            if obj:
                raise ValidationError("El nombre de usuario ya existe.")
        importar=False
        Ldap=self.env['res.company.ldap'].search([])
        for conf in Ldap:
            if conf.inportar == True:
                importar=True
        if importar == False:
            Ldap=self.env['res.company.ldap']
            for conf in Ldap.get_ldap_dicts():
                l=Ldap.connect(conf)
                l.protocol_version=ldap.VERSION3
                # l.set_option(ldap.OPT_REFERRALS, 0)vc
                ldap_password=conf['ldap_password'] or ''
                ldap_binddn=conf['ldap_binddn'] or ''
                _logger.error("Contrsena \"%s\" " % ldap_binddn)
                _logger.error("user \"%s\" " % ldap_password)
                l.simple_bind_s(ldap_binddn.encode('utf-8'),
                                ldap_password.encode('utf-8'))
                Ldap=self.env['res.company.ldap'].search([])


                if importar == False:
                    if 'grupo_ids' in values.keys():
                        # Analizo los grupos borrados o adicionados
                        delete_grupos, new_grupos=self.del_new(
                            values, 'grupo_ids', False)
                        if delete_grupos:
                            for group in delete_grupos:
                                grupo=self.env['usermanagement.grupo'].browse(
                                    group)
                                try:
                                    l.modify_s("CN=" + grupo.nombre.encode('utf-8') + ",OU=GRUPOS,dc=uo,dc=edu,dc=cu",
                                            [(ldap.MOD_DELETE, 'member',
                                                'CN=' + self.nombre.encode('utf-8') + " " + self.apellidos.encode(
                                                    'utf-8') + ',OU=Usuarios,dc=uo,dc=edu,dc=cu')])
                                except ldap.LDAPError, e:
                                    raise ValidationError(
                                        "No se pudo borrar el grupo  del usuario")
                                    _logger.error("Error Editando \"%s\" " % e)
                                    _logger.error(
                                        "Error Editando \"%s\" " % + nombre + " " + apellidos)
                                    activides_values={'name': "Importando Usuarios ",
                                                        'notas': 'Error a importar el usuario :' + nombre + " " + apellidos + " Mensage: " + str(
                                                            e)}

                        if new_grupos:
                            for group in new_grupos:
                                grupo=self.env['usermanagement.grupo'].browse(
                                    group)
                                try:
                                    l.modify_s("CN=" + grupo.nombre.encode('utf-8') + ",OU=GRUPOS,dc=uo,dc=edu,dc=cu",
                                            [(ldap.MOD_ADD, 'member',
                                                'CN=' + self.nombre.encode('utf-8') + " " + self.apellidos.encode(
                                                    'utf-8') + ',OU=Usuarios,dc=uo,dc=edu,dc=cu')])
                                except ldap.LDAPError, e:
                                    raise ValidationError(
                                        "No se pudo agregar el grupo  al usuario")
                                    _logger.error("Error Editando \"%s\" " % e)
                                    _logger.error(
                                        "Error Editando \"%s\" " % + nombre + " " + apellidos)
                    if 'servicio_ids' in values.keys():
                        # Analizo los grupos borrados o adicionados
                        delete_servicios, new_servicios=self.del_new(
                            values, 'servicio_ids', False)
                        if delete_servicios:
                            for servicio in delete_servicios:
                                s=self.env['usermanagement.servicio'].browse(
                                    servicio)
                                if s.nombre == "Internet":
                                    mod_attrs=[
                                        (ldap.MOD_REPLACE, "description", "Proxy UOnet:")]
                                    try:
                                        l.modify_s("CN=" + self.nombre.encode('utf-8') + " " + self.apellidos.encode(
                                            'utf-8') + ",OU=Usuarios,dc=uo,dc=edu,dc=cu", mod_attrs)
                                    except ldap.LDAPError, e:
                                            _logger.error(
                                                "Error Editando El description\"%s\" " % e)
                                try:
                                    l.modify_s("CN=" + s.nombre.encode('utf-8') + ",OU=Servicios,dc=uo,dc=edu,dc=cu",
                                            [(ldap.MOD_DELETE, 'member',
                                                'CN=' + self.nombre.encode('utf-8') + " " + self.apellidos.encode(
                                                    'utf-8') + ',OU=Usuarios,dc=uo,dc=edu,dc=cu')])
                                except ldap.LDAPError, e:
                                    # raise ValidationError("No se pudo borrar el Servico  del usuario")
                                    _logger.error("Error Editando \"%s\" " % e)

                        if new_servicios:
                            for servicio in new_servicios:
                                s=self.env['usermanagement.servicio'].browse(
                                    servicio)
                                try:
                                    l.modify_s("CN=" + s.nombre.encode('utf-8') + ",OU=Servicios,dc=uo,dc=edu,dc=cu",
                                            [(ldap.MOD_ADD, 'member',
                                                'CN=' + self.nombre.encode('utf-8') + " " + self.apellidos.encode(
                                                    'utf-8') + ',OU=Usuarios,dc=uo,dc=edu,dc=cu')])
                                except ldap.LDAPError, e:
                                    # raise ValidationError("No se pudo agregar el Servico  al usuario")
                                    _logger.error("Error Editando \"%s\" " % e)

                old_value={}
                new_value={}

                # if "area_id" in values:
                # new_value['department'] = self.env['usermanagement.area'].browse(values["area_id"]).nombre.encode('utf-8')
                # _logger.error("nuevos \"%s\" " % self.env['usermanagement.area'].browse(values["area_id"]).nombre)
                importar=False
                dn="CN=" + self.nombre.encode('utf-8') + " " + self.apellidos.encode(
                    'utf-8') + ",OU=Usuarios,dc=uo,dc=edu,dc=cu"
                Ldap=self.env['res.company.ldap'].search([])


                if importar == True:
                    if "correo" in values:
                        correo=values["correo"]
                    if "nombre" in values:
                        nombre=values["nombre"]
                    if "apellidos" in values:
                        apellidos=values["apellidos"]
                    if "direccion" in values:
                        direccion=values["direccion"]
                    if "carnet_identidad" in values:
                        carnet=values["carnet_identidad"]
                    if "nombre_usuario" in values:
                        nombre_usuario=values["nombre_usuario"]
                    if "contrasena" in values:
                        contrasena=values["contrasena"]
                        values["contrasena"]="Contrasena02++"
                    if "cuota" in values:
                        cuota=values["cuota"]
                    if "estado" in values:
                        estado=values["estado"]
                else:
                    if "correo" in values:
                        correo=values["correo"].encode('utf-8')
                    if "nombre" in values:
                        nombre=values["nombre"].encode('utf-8')
                    if "apellidos" in values:
                        apellidos=values["apellidos"].encode('utf-8')
                    if "direccion" in values:
                        direccion=values["direccion"].encode('utf-8')
                    if "carnet_identidad" in values:
                        carnet=values["carnet_identidad"].encode('utf-8')
                    if "nombre_usuario" in values:
                        nombre_usuario=values["nombre_usuario"].encode('utf-8')
                    if "contrasena" in values:
                        contrasena=values["contrasena"]
                        contrasena=contrasena.encode('utf-8')
                        values["contrasena"]="Contrasena02++"
                    if "cuota" in values:
                        cuota=values["cuota"]
                    if "estado" in values:
                        estado=values["estado"]

                if "correo" in values:
                    new_value['mail']=correo
                    new_value['userPrincipalName']=correo
                    old_value['mail']=self.correo.encode('utf-8')
                    old_value['userPrincipalName']=correo

                # if "foto" in values:
                #               cuota_new = {}
                #               cuota_old = {}
                #               cuota_new['jpegPhoto'] = values["foto"].decode('base64')
                #               cuota_old['jpegPhoto'] = self.foto
                #              modlist = ldap.modlist.modifyModlist(cuota_old, cuota_new)
                #              try:
                #                  l.modify_s(dn, modlist)
                #              except ldap.LDAPError, e:
                #                  try:
                #                      l.modify_s(dn,[(ldap.MOD_ADD, 'jpegPhoto',values["foto"].decode('base64'))])
                #                 except ldap.LDAPError, e:
                #                    _logger.error("Error Editando Foto\"%s\" " % e)
                if "estado" in values:
                    if estado == "desactivado":
                        new_value['userAccountControl']="514"
                        old_value['userAccountControl']="512"
                        # new_value['description']=" ".encode('utf-8')

                    if estado == "activado":
                        new_value['userAccountControl']="512"
                        old_value['userAccountControl']="514"
                        # new_value['description'] = " ".encode('utf-8')

                if "cuota" in values:
                    cuota_new={}
                    cuota_old={}
                    cuota_new['departmentNumber']=str(
                        cuota).encode('utf-8') + "mb/w"
                    cuota_old['departmentNumber']=str(
                        self.cuota).encode('utf-8') + "mb/w"
                    modlist=ldap.modlist.modifyModlist(cuota_old, cuota_new)
                    try:
                        if importar == False:
                            l.modify_s(dn, modlist)
                    except ldap.LDAPError, e:
                        try:
                            if importar == False:
                                l.modify_s(
                                    dn, [(ldap.MOD_ADD, 'departmentNumber', str(cuota).encode('utf-8') + "mb/w")])
                        except ldap.LDAPError, e:
                            _logger.error("Error Editando \"%s\" " % e)

                if "contrasena" in values:
                    # unicode_pass = unicode('\"' + contrasena + '\"', 'iso-8859-1')
                    Ldap = self.env['res.company.ldap'].search([])
                    for conf in Ldap:
                        conf.write({'inportar': False})
                    _logger.error("Cambiando contrasena-----------------------------------------------------------------------------")
                    _logger.error("Cambiando al usuario\"%s\" " % self.nombre_usuario)
                    unicode_pass='\"' + contrasena + '\"'.encode('utf-8')
                    password_value=unicode_pass.encode('utf-16-le')
                    add_pass=[(ldap.MOD_REPLACE, 'unicodePwd', [password_value])]
                    login=self.nombre_usuario + ":Proxy UOnet:" + contrasena
                    login=hashlib.md5(login).hexdigest()
                    add_des=[(ldap.MOD_REPLACE, 'description',["Proxy UOnet:" + login])]
                    response=[]
                    try:
                            response=l.modify_s('CN=' + self.nombre.encode('utf-8') + " " + self.apellidos.encode(
                            'utf-8') + ',OU=Usuarios,DC=uo,DC=edu,DC=cu', add_pass)
                            _logger.error("Respuesta->>>>>>>>>>>>>>>>>>>>>>>>>> \"%s\" " % response[0])
                            l.modify_s('CN=' + self.nombre.encode('utf-8') + " " + self.apellidos.encode(
                            'utf-8') + ',OU=Usuarios,DC=uo,DC=edu,DC=cu', add_des)
                            
                    except ldap.LDAPError, e:
                        _logger.error("Error cambiando contrasena--------------------->>>>>>>>>>>>>>>>>>>>>>>>>> \"%s\" " % e)
                        raise ValidationError(
                        'Error cambiando contraseña.La contraseña debe tener entre 8 y 25 caracteres, una letra mayúscula, al menos una letra minúscula y un caracter numérico ')

                if "nombre" in values and "apellidos" in values:
                    # new_value['name'] = nombre + " " + apellidos
                    # new_value['cn'] = nombre + " " + apellidos
                    if importar == False:
                    # old_value['name'] = self.nombre.encode('utf-8') + " " + self.apellidos.encode('utf-8')
                    # old_value['cn'] = self.nombre.encode('utf-8') + " " + self.apellidos.encode('utf-8')
                        old_value['displayName']=self.nombre.encode(
                            'utf-8') + " " + self.apellidos.encode('utf-8')
                        new_value['displayName']=nombre + " " + apellidos

                        l.rename_s(dn, 'CN=' + nombre + " " + apellidos,
                                'OU=Usuarios,DC=uo,DC=edu,DC=cu')
                        dn='CN=' + nombre + " " + apellidos + ",OU=Usuarios,dc=uo,dc=edu,dc=cu"
                if "direccion" in values:
                    if importar == False:
                        new_value['physicalDeliveryOfficeName']=direccion
                        old_value['physicalDeliveryOfficeName']=self.direccion.encode(
                            'utf-8')
                if "carnet_identidad" in values:
                    if importar == False:
                        new_value['title']=carnet
                        old_value['title']=self.carnet_identidad.encode(
                            'utf-8')
                if "nombre_usuario" in values:
                    if importar == False:
                        old_value['sAMAccountname']=self.nombre_usuario.encode(
                            'utf-8')
                        new_value['sAMAccountname']=nombre_usuario
                    # new_value['userPassword'] = "test123*"
                if "nombre" in values and not "apellidos" in values:
                    if importar == False:
                        new_value['givenName']=nombre
                        new_value['displayName']=nombre + \
                            " " + self.apellidos.encode('utf-8')
                        old_value['givenName']=self.nombre.encode('utf-8')
                        old_value['displayName']=self.nombre.encode(
                            'utf-8') + " " + self.apellidos.encode('utf-8')
                        l.rename_s(dn, 'CN=' + nombre + " " + self.apellidos.encode('utf-8'),
                            'OU=Usuarios,DC=uo,DC=edu,DC=cu')
                        dn='CN=' + nombre + " " + \
                            self.apellidos.encode(
                                'utf-8') + ",OU=Usuarios,dc=uo,dc=edu,dc=cu"
                if "apellidos" in values and not "nombre" in values:
                    if importar == False:
                        new_value['sn']=apellidos
                        # new_value['name'] = self.nombre.encode('utf-8') + " " + apellidos
                        # new_value['cn'] = self.nombre.encode('utf-8') + " " + apellidos
                        new_value['displayName']=self.nombre.encode(
                            'utf-8') + " " + apellidos
                        old_value['sn']=self.apellidos.encode('utf-8')
                        l.rename_s(dn, 'CN=' + self.nombre.encode('utf-8') + " " + apellidos,
                            'OU=Usuarios,DC=uo,DC=edu,DC=cu')
                        dn='CN=' + \
                            self.nombre.encode(
                                'utf-8') + " " + apellidos + ",OU=Usuarios,dc=uo,dc=edu,dc=cu"
                if importar == False:
                    try:
                        _logger.error(
                            'Nuevos Valores Usuarios Editar: %s.' % new_value)
                        _logger.error(
                            'Viejos Valores Usuarios Editar: %s.' % old_value)
                        modlist=ldap.modlist.modifyModlist(
                            old_value, new_value)
                        l.modify_s(dn, modlist)
                    except ldap.LDAPError, e:
                        _logger.error("Error Editando \"%s\" " % e)
                        activides_values={'name': "Editando Usuario ",
                                            'notas': 'Error a Editando Usuario :' + self.nombre.encode(
                                                'utf-8') + " " + self.apellidos.encode('utf-8') + " Mensage: "}

                l.unbind()
        # Metodo que interviene al borrar un usuario
        return super(LdapUsuario, self).write(values)

    @api.multi
    @api.model
    def unlink(self):
        importar=False
        Ldap=self.env['res.company.ldap']
        for conf in Ldap:
            if conf.inportar == True:
                importar=True
        if importar == False:
            l=ldap.initialize("ldap://10.30.1.48")
            try:
                l.protocol_version=ldap.VERSION3
                l.set_option(ldap.OPT_REFERRALS, 0)
                bind=l.simple_bind_s(
                    "CN=Administrator,CN=Users,DC=uo,DC=edu,DC=cu", "*K3rn3ll1nu+*")
                usuarios=self.env['usermanagement.usuario'].browse(self.ids)
                for usuario in usuarios:
                    dn='CN=' + self.nombre.encode('utf-8') + " " + self.apellidos.encode('utf-8') + ',OU=Usuarios,DC=uo,DC=edu,DC=cu'
                    _logger.error("usuarios DN \"%s\" " % dn)
                    l.delete_s(dn)
            except ldap.LDAPError, e:
                _logger.error("nuevos \"%s\" " % e)
            finally:
                l.unbind()
        return super(LdapUsuario, self).unlink()

    def del_new(self, values, key, flag):
        A=[]
        B=[]
        for _key in self[key]:
            A.append(_key.id)
        if values[key]:
            for _key1 in values[key][0][2]:
                B.append(_key1)
        delete_keys=list(set(A) - set(B))
        new_keys=list(set(B) - set(A))
        if flag:
            rest_keys=list(set(A) - set(delete_keys))
            return delete_keys, new_keys, rest_keys
        else:
            return delete_keys, new_keys

    @api.multi
    @api.constrains('carnet_identidad')
    def _check_CI(self):
        importar=False
        Ldap=self.env['res.company.ldap'].search([])
        for conf in Ldap:
            if conf.inportar == True:
                importar=True
        if importar == False:
            '''Method allow only numbers'''
            pattern="^[0-9]+$"
            if self.carnet_identidad:
                if len(self.carnet_identidad) < 11:
                    raise ValidationError(
                        'El Carnet de Identidad debe tener 11 carateres.')
                if re.match(pattern, self.carnet_identidad) is None:
                    raise ValidationError(
                        'El Carnet de Identidad solo debe contener números.')
