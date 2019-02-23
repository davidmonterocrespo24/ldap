import logging
from odoo import api, fields, models, registry, SUPERUSER_ID, exceptions
import ldap
import ldap.modlist as modlist
import hashlib
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
import logging


# modelo para manejar los usaurios
class LdapGrupo(models.Model):
    _inherit = 'usermanagement.grupo'

    # ultima revicion 6/3/2018
    @api.model
    @api.returns('self', lambda rec: rec.id)
    def create(self, values):
        importar=True
        Ldap = self.env['res.company.ldap'].search([])
        for conf in Ldap:
            if conf.inportar == True:
                importar = True
        if importar == False:
            Ldap = self.env['res.company.ldap']
            for conf in Ldap.get_ldap_dicts():
                l = Ldap.connect(conf)
                l.protocol_version = ldap.VERSION3
                # l.set_option(ldap.OPT_REFERRALS, 0)vc
                ldap_password = conf['ldap_password'] or ''
                ldap_binddn = conf['ldap_binddn'] or ''
                try:
                    l.simple_bind_s(ldap_binddn.encode('utf-8'), ldap_password.encode('utf-8'))
                except ldap.LDAPError, e:
                    raise ValidationError('No se puede conectar con el Servidor LDAP,pruebe mas tarde.')
                attrs = {}
                attrs['name'] = values["nombre"].encode('utf-8')
                attrs['objectclass'] = ['top', 'group']
                attrs['instanceType'] = "4"
                attrs['sAMAccountname'] = values["nombre"].encode('utf-8')
                ldif = modlist.addModlist(attrs)
                importar = False
                Ldap = self.env['res.company.ldap'].search([])
                for conf in Ldap:
                    if conf.inportar == True:
                        importar = True
                usuarioAdd = {}
                attrs = {}
                attrs['name'] = values["nombre"].encode('utf-8')
                attrs['objectclass'] = ['top', 'group']
                attrs['instanceType'] = "4"

                importar = False
                Ldap = self.env['res.company.ldap'].search([])
                for conf in Ldap:
                    if conf.inportar == True:
                        importar = True
                if importar == True:
                    attrs['sAMAccountname'] = values["nombre"]
                    _logger.error("Importar True")
                else:
                    attrs['sAMAccountname'] = values["nombre"].encode('utf-8')

                attrs['member'] = []
                if 'usuarios_ids' in values.keys():
                    ## insertar usuarios en grupos################################################################################################################
                    for usuario in values['usuarios_ids']:
                        for one_user in usuario[2]:
                            u = self.env['usermanagement.usuario'].browse(one_user)
                            _logger.error("Usuarios En grupos \"%s\" " % u.nombre)
                            attrs['member'].append(
                                ("CN=" + u.nombre + " " + u.apellidos + ",OU=Usuarios,dc=uo,dc=edu,dc=cu").encode('utf-8'))
                try:
                    ldif = modlist.addModlist(attrs)
                    l.add_s("CN=" + values["nombre"].encode('utf-8') + ",OU=GRUPOS,dc=uo,dc=edu,dc=cu", ldif)
                except ldap.LDAPError, e:
                    _logger.error("Error crear el Grupo \"%s\" " % e)

                l.unbind()

        return super(LdapGrupo, self).create(values)

    @api.multi
    @api.model
    def unlink(self):
        importar=True
        Ldap = self.env['res.company.ldap'].search([])
        for conf in Ldap:
            if conf.inportar == True:
                importar = True
        if importar == False:
            Ldap = self.env['res.company.ldap']
            for conf in Ldap.get_ldap_dicts():
                l = Ldap.connect(conf)
                l.protocol_version = ldap.VERSION3
                # l.set_option(ldap.OPT_REFERRALS, 0)vc
                ldap_password = conf['ldap_password'] or ''
                ldap_binddn = conf['ldap_binddn'] or ''
                try:
                    l.simple_bind_s(ldap_binddn.encode('utf-8'), ldap_password.encode('utf-8'))
                except ldap.LDAPError, e:
                    raise ValidationError('No se puede conectar con el Servidor LDAP,pruebe mas tarde.')
                grups = self.env['usermanagement.grupo'].browse(self.ids)
                for grup in grups:
                    dn = "CN=" + grup.nombre + ",OU=GRUPOS,dc=uo,dc=edu,dc=cu"

                    try:
                        l.delete_s(dn)
                        _logger.error("Servicio DN \"%s\" " % dn)
                    except ldap.LDAPError, e:
                        activides_values = {'name': "Incluyendo Eliminando Grupo ",
                                            'notas': 'Error Eliminando Grupo :' + grup.nombre + " Mensage: "}
                        _logger.error("Error Eliminando Grupo \"%s\" " % e)

                l.unbind()
        return super(LdapGrupo, self).unlink()

    @api.multi
    def write(self, values):
        importar=True
        Ldap = self.env['res.company.ldap'].search([])
        for conf in Ldap:
            if conf.inportar == True:
                importar = True
        if importar == False:
            Ldap = self.env['res.company.ldap']
            for conf in Ldap.get_ldap_dicts():
                l = Ldap.connect(conf)
                l.protocol_version = ldap.VERSION3
                # l.set_option(ldap.OPT_REFERRALS, 0)vc
                ldap_password = conf['ldap_password'] or ''
                ldap_binddn = conf['ldap_binddn'] or ''
                try:
                    l.simple_bind_s(ldap_binddn.encode('utf-8'), ldap_password.encode('utf-8'))
                except ldap.LDAPError, e:
                    raise ValidationError('No se puede conectar con el Servidor LDAP,pruebe mas tarde.')
                if 'usuarios_ids' in values.keys():
                    delete_users, new_users, rest_users = self.del_new(values, 'usuarios_ids', True)
                    if delete_users:
                        for user in delete_users:
                            try:
                                usuario = self.env['usermanagement.usuario'].browse(user)
                                l.modify_s("CN=" + self.nombre.encode('utf-8') + ",OU=GRUPOS,dc=uo,dc=edu,dc=cu",
                                        [(ldap.MOD_DELETE, 'member',
                                            'CN=' + usuario.nombre.encode(
                                                'utf-8') + " " + usuario.apellidos.encode(
                                                'utf-8') + ',OU=Usuarios,dc=uo,dc=edu,dc=cu')])
                            except ldap.LDAPError, e:
                                _logger.error("Eliminando usuario del Grupo \"%s\" " % e)
                    if new_users:
                        for user in delete_users:
                            try:
                                usuario = self.env['usermanagement.usuario'].browse(user)
                                l.modify_s("CN=" + self.nombre.encode('utf-8') + ",OU=GRUPOS,dc=uo,dc=edu,dc=cu",
                                    [(ldap.MOD_ADD, 'member',
                                        'CN=' + usuario.nombre.encode(
                                            'utf-8') + " " + usuario.apellidos.encode(
                                            'utf-8') + ',OU=Usuarios,dc=uo,dc=edu,dc=cu')])
                            except ldap.LDAPError, e:
                                    _logger.error("Adicionar usuario del Grupo \"%s\" " % e)
                l.unbind()
        # raise ValidationError("fdf")
        return super(LdapGrupo, self).write(values)
    def del_new(self, values, key, flag):
        A = []
        B = []
        for _key in self[key]:
            A.append(_key.id)
        if values[key]:
            for _key1 in values[key][0][2]:
                B.append(_key1)
        delete_keys = list(set(A) - set(B))
        new_keys = list(set(B) - set(A))
        if flag:
            rest_keys = list(set(A) - set(delete_keys))
            return delete_keys, new_keys, rest_keys
        else:
            return delete_keys, new_keys
