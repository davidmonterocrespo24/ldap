# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
import ldap
import ldap.modlist as modlist
import hashlib
_logger = logging.getLogger(__name__)

class DelServiceUserWizard(models.TransientModel):
    _inherit = "usermanagement.delserviceuserwizard"
    _description = "Eliminar Servicio a Usuario"


    def del_service_from_user(self, user, service):
        if user.observacion != False:
            obs = user.observacion+'\n'+self.notes
            user.write({'observacion': obs})
        else:
            user.write({'observacion': self.notes})

        Ldap = self.env['res.company.ldap']
        for conf in Ldap.get_ldap_dicts():
            l = Ldap.connect(conf)
            l.protocol_version = ldap.VERSION3
            # l.set_option(ldap.OPT_REFERRALS, 0)vc
            ldap_password = conf['ldap_password'] or ''
            ldap_binddn = conf['ldap_binddn'] or ''
            try:
                l.simple_bind_s(ldap_binddn.encode('utf-8'), ldap_password.encode('utf-8'))
                l.modify_s(
                    "CN=" + service.nombre.encode('utf-8') + ",OU=Servicios,dc=uo,dc=edu,dc=cu",
                    [(ldap.MOD_DELETE, 'member',
                      'CN=' + self.nombre.encode('utf-8') + " " + self.apellidos.encode(
                          'utf-8') + ',OU=Usuarios,dc=uo,dc=edu,dc=cu')])
                self.env['usermanagement.ususerv'].search(
                    [('usuario_id', '=', user.id), ('servicio_id', '=', service.id)]).unlink()
            except ldap.LDAPError, e:
                raise ValidationError("No se pudo eliminar el grupo  al usuario")
            _logger.error("Error Editando \"%s\" " % + user.nombre + " " + user.apellidos)
    
    def do_restore_service_user_button(self):
        if self.users:
            for user in self.users:
                user.recalculate_services()
        else:
            raise ValidationError("No se ha seleccionado ningún usuario.")