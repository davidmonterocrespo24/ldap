# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import ldap
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class GestionWizard(models.TransientModel):
    _name = 'ldap.importar'
    _description = 'Reporte'

    @api.multi
    def importar_todo4(self):
        Ldap = self.env['res.company.ldap'].search([])
        for conf in Ldap:
            conf.write({'inportar': True})
        try:
            userLadpList = []
            userGestorList = []
            Ldap = self.env['res.company.ldap']
            for conf in Ldap.get_ldap_dicts():
                l = Ldap.connect(conf)
                l.protocol_version = ldap.VERSION3
                # l.set_option(ldap.OPT_REFERRALS, 0)vc
                ldap_password = conf['ldap_password'] or ''
                ldap_binddn = conf['ldap_binddn'] or ''
                l.simple_bind_s(ldap_binddn.encode('utf-8'), ldap_password.encode('utf-8'))
                base = "OU=Usuarios,dc=uo,dc=edu,dc=cu"
                # criteria = "(|(objectClass=user)(objectClass=person))"
                attributes = ['cn']
                criteria = "(|(objectClass=user)(objectClass=person))"
                # attributes = ['uid', 'ou', 'fullName']
                result = l.search_st(base, ldap.SCOPE_SUBTREE, criteria)
                for entry in result:
                    nombre_usuario_ldap = entry[1]['sAMAccountName'][0]
                    userLadpList.append(nombre_usuario_ldap.decode('utf-8').encode('utf-8'))
            user_gestor = self.env['usermanagement.usuario'].search([])

            for user in user_gestor:
                nombre_usuario_gestor = user.nombre_usuario
                userGestorList.append(nombre_usuario_gestor.encode('utf-8'))
            delete_keys = list(set(userGestorList) - set(userLadpList))
            new_keys = list(set(userLadpList) - set(userGestorList))
            for n in new_keys:
                self.importar_usuario(n)
            #for d in delete_keys:
                #self.env['usermanagement.usuario'].search([('nombre_usuario', '=', d)]).unlink()
            _logger.error('Borrar: %s.' % delete_keys)
            _logger.error('Nuevos: %s.' % new_keys)
            Ldap = self.env['res.company.ldap'].search([])
            self.actualizar_grupos()
            self.actualizar_servicios()
            self.actualizar_usuarios()

            for conf in Ldap:
                conf.write({'inportar': False})
                l.unbind()
        except ldap.LDAPError, e:
                _logger.error('Error Ldap: %s.' % e)
                raise ValidationError('LDAPError: %s.' % e)


    @api.multi
    def importar_todo2(self):
        Ldap = self.env['res.company.ldap'].search([])
        for conf in Ldap:
            conf.write({'inportar': True})
            conf.write({'inportar': False})

    def importar_usuario(self, usuario):
        Ldap = self.env['res.company.ldap'].search([])
        for conf in Ldap:
            conf.write({'inportar': True})
        Ldap = self.env['res.company.ldap']
        for conf in Ldap.get_ldap_dicts():
            l = Ldap.connect(conf)
            l.protocol_version = ldap.VERSION3
            # l.set_option(ldap.OPT_REFERRALS, 0)vc
            ldap_password = conf['ldap_password'] or ''
            ldap_binddn = conf['ldap_binddn'] or ''
            l.simple_bind_s(ldap_binddn.encode('utf-8'), ldap_password.encode('utf-8'))
            base = "OU=Usuarios,dc=uo,dc=edu,dc=cu"
            attributes = ['cn']
            criteria = "(sAMAccountName=" + usuario + ")"

            # attributes = ['uid', 'ou', 'fullName']
            result = l.search_st(base, ldap.SCOPE_SUBTREE, criteria)
            for entry in result:
                telefono = ""
                direccion = ""
                apellidos = ""
                mail = ""
                carnet_identidad = ""
                if 'physicalDeliveryOfficeName' in entry[1]:
                    direccion = entry[1]['physicalDeliveryOfficeName'][0]
                    # direccion = direccion.decode('utf-8')
                    # direccion = direccion.encode('utf-8')
                if 'telephoneNumber' in entry[1]:
                    telefono = entry[1]['telephoneNumber'][0]
                if 'mail' in entry[1]:
                    mail = entry[1]['mail'][0]
                if 'sn' in entry[1]:
                    apellidos = entry[1]['sn'][0]
                if 'title' in entry[1]:
                    carnet_identidad = entry[1]['title'][0]
                if 'departmentNumber' in entry[1]:
                    if entry[1]['departmentNumber'][0][:-4].strip() != '':
                        cuota = int(entry[1]['departmentNumber'][0][:-4].strip())
                        if entry[1]['departmentNumber'][0].find('g') > 0:
                            cuota = int(entry[1]['departmentNumber'][0][:-4].strip())
                            cuota = cuota * 1024
                    else:
                        cuota = 0
                else:
                    cuota = 0

                nombre_usuario = entry[1]['sAMAccountName'][0]
                nombre_usuario = nombre_usuario.decode('utf-8')
                nombre_usuario = nombre_usuario.encode('utf-8')
                nombre = entry[1]['givenName'][0]
                nombre = nombre.decode('utf-8')
                nombre = nombre.encode('utf-8')
                foto = 0
                if 'jpegPhoto' in entry[1]:
                    foto = entry[1]['jpegPhoto'][0].encode('base64')

                partner_val = {'nombre': nombre,
                               'apellidos': apellidos,
                               'nombre_usuario': nombre_usuario,
                               'telefono': telefono,
                               'direccion': direccion,
                               'correo': mail,
                               'carnet_identidad': carnet_identidad,
                               'estado': 'activado',
                               'contrasena': 'Contrasena02++',
                               'confirmar_contrasena': 'Contrasena02++',
                               'tiempo_expiracion': fields.datetime.now(),
                               'foto': foto,
                               'cuota': cuota
                               }
                try:
                    record = self.env['usermanagement.usuario'].create(partner_val)
                    _logger.error('Buscar Grupos: %s.' % nombre_usuario)
                    criteria = "(sAMAccountName=" + nombre_usuario + ")"
                    attributes = ['memberOf']
                    result = l.search_st(base, ldap.SCOPE_SUBTREE, criteria, attributes)
                    for entry in result:
                        if 'memberOf' in entry[1].keys():
                            for grupos in entry[1]['memberOf']:
                                nombre = grupos.split(",")
                                salida = nombre[0].replace("CN=", "")
                                _logger.error('Miembro de : %s.' % salida)
                                _logger.error('Usuario de : %s.' % nombre_usuario)
                                wt_grupo = self.env['usermanagement.grupo']
                                id_needed_grupo = wt_grupo.search([('nombre', '=', salida)])
                                wt_usuario = self.env['usermanagement.usuario']
                                id_needed_usuario = wt_usuario.search([('nombre_usuario', '=', nombre_usuario)])
                                for id_user in id_needed_usuario:
                                    id_user.grupo_ids |= id_needed_grupo
                                # Actualizar servicios
                                wt_servicio = self.env['usermanagement.servicio']
                                id_needed_servicio = wt_servicio.search([('nombre', '=', salida)])
                                for id_user in id_needed_usuario:
                                    # id_user.grupo_ids |= id_needed_grupo
                                    id_user.servicio_ids |= id_needed_servicio

                except ldap.LDAPError, e:
                    _logger.error('Nuevos: %s.' % e)
            l.unbind()
        Ldap = self.env['res.company.ldap'].search([])
        for conf in Ldap:
            conf.write({'inportar': False})

    @api.one
    def actualizar_usuarios(self):
        _logger.error('Actualizar Usuarios#########################################################################################################')
        Ldap = self.env['res.company.ldap'].search([])
        for conf in Ldap:
            conf.write({'inportar': True})
        Ldap = self.env['res.company.ldap']
        for conf in Ldap.get_ldap_dicts():
            l = Ldap.connect(conf)
            l.protocol_version = ldap.VERSION3
            # l.set_option(ldap.OPT_REFERRALS, 0)vc
            ldap_password = conf['ldap_password'] or ''
            ldap_binddn = conf['ldap_binddn'] or ''
            l.simple_bind_s(ldap_binddn.encode('utf-8'), ldap_password.encode('utf-8'))
            base = "OU=Usuarios,dc=uo,dc=edu,dc=cu"
            criteria = "(|(objectClass=user)(objectClass=person))"
            attributes = ['cn']
            #criteria = "(|(objectClass=user)(objectClass=person))"
            # attributes = ['uid', 'ou', 'fullName']
            #criteria = "(sAMAccountName=david.montero)"
            result = l.search_st(base, ldap.SCOPE_SUBTREE, criteria)
            for entry in result:
                telefono = "".decode('utf-8')
                direccion = "".decode('utf-8')
                if 'physicalDeliveryOfficeName' in entry[1]:
                    direccion = entry[1]['physicalDeliveryOfficeName'][0].decode('utf-8')
                if 'telephoneNumber' in entry[1]:
                    telefono = entry[1]['telephoneNumber'][0].decode('utf-8')
                if 'mail' in entry[1]:
                    mail = entry[1]['mail'][0].decode('utf-8')
                if 'sn' in entry[1]:
                    apellidos = entry[1]['sn'][0].decode('utf-8')
                if 'title' in entry[1]:
                    carnet_identidad = entry[1]['title'][0].decode('utf-8')


                nombre_usuario = entry[1]['sAMAccountName'][0]
                nombre_usuario = nombre_usuario.decode('utf-8')
                nombre = entry[1]['givenName'][0]
                nombre = nombre.decode('utf-8')
                estado=entry[1]['userAccountControl'][0].decode('utf-8')
                if estado=='512':
                    estado='activado'
                else:
                    estado='desactivado'
                foto = 0
                if 'jpegPhoto' in entry[1]:
                    foto = entry[1]['jpegPhoto'][0].encode('base64')
                partner_val = {'nombre': nombre,
                               'apellidos': apellidos,
                               'telefono': telefono,
                               'direccion': direccion,
                               'correo': mail,
                               'carnet_identidad': carnet_identidad,
                               'estado':estado
                               }
                user=self.env['usermanagement.usuario'].search([('nombre_usuario', '=', nombre_usuario)])
                try:

                    if user.nombre!=partner_val['nombre'] or user.apellidos!=partner_val['apellidos'] or user.correo!=partner_val['correo'] or user.carnet_identidad!=partner_val['carnet_identidad']or user.estado!=partner_val['estado'] :
                        _logger.error('Actualizar ..............................................................................................: %s.' % nombre_usuario)
                        _logger.error('estado ldap!: %s.' % estado)
                        _logger.error('estado user!: %s.' % user.estado)
                        _logger.error('nombre user!: %s.' % user.nombre)
                        _logger.error('nombre ldap!: %s.' % partner_val['nombre'])
                        _logger.error('apellidos user!: %s.' % user.apellidos)
                        _logger.error('apellidos ldap!: %s.' % partner_val['apellidos'])
                        _logger.error('nombre user!: %s.' % user.correo)
                        _logger.error('nombre ldap!: %s.' % partner_val['correo'])
                        _logger.error('apellidos user!: %s.' % user.carnet_identidad)
                        _logger.error('apellidos ldap!: %s.' % partner_val['carnet_identidad'])
                        user.write(partner_val)

                except ldap.LDAPError, e:
                    _logger.error('Actualizar Error!: %s.' % e)

                #Actualizar los grupos y los servicios
                #buscamos los mienbros en el ldap
                if 'memberOf' in entry[1]:
                    valores= entry[1]['memberOf']
                    grupoLDAPList = []
                    grupoGDUList = []
                    servicioLDAPList = []
                    servicioGDUList = []
                    for g in valores:
                        member=g.split(",")
                        member_name= member[0].replace("CN=","")
                        tipo= member[1].replace("OU=","")
                        #vemos si es un servicio
                        if tipo=="Servicios":
                            servicioLDAPList.append(member_name.decode('utf-8').encode('utf-8'))
                        #vemos si es un grupo
                        if tipo=="GRUPOS":
                            grupoLDAPList.append(member_name.decode('utf-8').encode('utf-8'))
                    #buscamos los mienbros en la Base de datos

                    for g in user.grupo_ids:
                        grupoGDUList.append(g.nombre.decode('utf-8').encode('utf-8'))

                    for g in user.servicio_ids:
                        servicioGDUList.append(g.nombre.decode('utf-8').encode('utf-8'))
                    #GRUPOS
                    delete_keys = list(set(grupoGDUList) - set(grupoLDAPList))
                    new_keys = list(set(grupoLDAPList) - set(grupoGDUList))
                    for n in delete_keys:
                        wt_grupo = self.env['usermanagement.grupo'].search([('nombre', '=', n)])
                        user.grupo_ids -= wt_grupo
                    for n in new_keys:
                        wt_grupo = self.env['usermanagement.grupo'].search([('nombre', '=', n)])
                        for u in user:
                            u.grupo_ids |= wt_grupo
                    #SERVICIOS
                    delete_keys = list(set(servicioGDUList) - set(servicioLDAPList))
                    new_keys = list(set(servicioLDAPList) - set(servicioGDUList))
                    for n in delete_keys:
                        if(user.nombre):
                            wt_servicio = self.env['usermanagement.servicio'].search([('nombre', '=', n)])
                            user.servicio_ids -= wt_servicio
                    for n in new_keys:
                        if(user.nombre):
                            _logger.error('nombre Actualizar servicio!: %s.' % user.nombre)
                            _logger.error('apellidos Actualizar servicio!: %s.' % user.apellidos)
                            wt_servicio = self.env['usermanagement.servicio'].search([('nombre', '=', n)])
                            user.servicio_ids |= wt_servicio
            l.unbind()
        Ldap = self.env['res.company.ldap'].search([])
        for conf in Ldap:
            conf.write({'inportar': False})
        _logger.error('Fin Usuarios*********************************************************************************************************************')


    @api.multi
    def actualizar_grupos(self):
        _logger.error('Actualizar Grupos!!!!!!')
        Ldap = self.env['res.company.ldap'].search([])
        for conf in Ldap:
            conf.write({'inportar': True})
            try:
                grupoLadpList = []
                grupoGestorList = []
                Ldap = self.env['res.company.ldap']
                for conf in Ldap.get_ldap_dicts():
                    l = Ldap.connect(conf)
                    l.protocol_version = ldap.VERSION3
                    # l.set_option(ldap.OPT_REFERRALS, 0)vc
                    ldap_password = conf['ldap_password'] or ''
                    ldap_binddn = conf['ldap_binddn'] or ''
                    l.simple_bind_s(ldap_binddn.encode('utf-8'), ldap_password.encode('utf-8'))
                    base = "OU=GRUPOS,dc=uo,dc=edu,dc=cu"
                    attributes = ['cn']
                    criteria = "objectClass=group"
                    result = l.search_st(base, ldap.SCOPE_SUBTREE, criteria, attributes)
                    result2 = l.search_st(base, ldap.SCOPE_SUBTREE, criteria)
                    for entry in result:
                        nombre_grupo = entry[1]['cn'][0]
                        nombre_grupo = nombre_grupo.decode('utf-8')
                        nombre_grupo = nombre_grupo.encode('utf-8')
                        grupo_val = {'nombre': nombre_grupo}
                        grupoLadpList.append(nombre_grupo.decode('utf-8').encode('utf-8'))

                    grupos = self.env['usermanagement.grupo'].search([])
                    for g in grupos:
                        nombre_grupo = g.nombre
                        grupoGestorList.append(nombre_grupo.encode('utf-8'))

                    delete_keys = list(set(grupoGestorList) - set(grupoLadpList))
                    new_keys = list(set(grupoLadpList) - set(grupoGestorList))
                    for n in new_keys:
                        grupo_val = {'nombre': n}
                        self.env['usermanagement.grupo'].create(grupo_val)
                    for n in delete_keys:
                        wt_grupo = self.env['usermanagement.grupo']
                        wt_grupo.search([('nombre', '=', n)]).unlink()
                    l.unbind()
#Actualizar los usuarios en los grupos

            except ldap.LDAPError, e:
                _logger.error("Ldap usuarios \"%s\" " % e)

        Ldap = self.env['res.company.ldap'].search([])
        for conf in Ldap:
            conf.write({'inportar': False})
    @api.multi
    def actualizar_servicios(self):
        _logger.error("Actualizar Servicio")
        Ldap = self.env['res.company.ldap'].search([])
        for conf in Ldap:
            conf.write({'inportar': True})
            try:
                servicioLadpList = []
                servicioGestorList = []
                Ldap = self.env['res.company.ldap']
                for conf in Ldap.get_ldap_dicts():
                    l = Ldap.connect(conf)
                    l.protocol_version = ldap.VERSION3
                    # l.set_option(ldap.OPT_REFERRALS, 0)vc
                    ldap_password = conf['ldap_password'] or ''
                    ldap_binddn = conf['ldap_binddn'] or ''
                    l.simple_bind_s(ldap_binddn.encode('utf-8'), ldap_password.encode('utf-8'))
                    base = "OU=Servicios,dc=uo,dc=edu,dc=cu"
                    attributes = ['cn']
                    criteria = "objectClass=group"
                    result = l.search_st(base, ldap.SCOPE_SUBTREE, criteria, attributes)
                    for entry in result:
                        nombre_grupo = entry[1]['cn'][0]
                        nombre_grupo = nombre_grupo.decode('utf-8')
                        nombre_grupo = nombre_grupo.encode('utf-8')
                        grupo_val = {'nombre': nombre_grupo}
                        servicioLadpList.append(nombre_grupo.decode('utf-8').encode('utf-8'))
                    servicio = self.env['usermanagement.servicio'].search([])
                    for s in servicio:
                        nombre_grupo = s.nombre
                        nombre_servicio = s.nombre
                        servicioGestorList.append(nombre_servicio.encode('utf-8'))

                    delete_keys = list(set(servicioGestorList) - set(servicioLadpList))
                    new_keys = list(set(servicioLadpList) - set(servicioGestorList))
                    for n in new_keys:
                        grupo_val = {'nombre': n}
                        self.env['usermanagement.servicio'].create(grupo_val)
                    for n in delete_keys:
                        wt_grupo = self.env['usermanagement.servicio']
                        wt_grupo.search([('nombre', '=', n)]).unlink()
                    l.unbind()
            except ldap.LDAPError, e:
                _logger.error("Ldap usuarios \"%s\" " % e)

        Ldap = self.env['res.company.ldap'].search([])
        for conf in Ldap:
            conf.write({'inportar': False})
