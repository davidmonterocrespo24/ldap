# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, registry, SUPERUSER_ID
import ldap
import ldap.modlist as modlist
import hashlib

_logger = logging.getLogger(__name__)


# modelo para manejar los usaurios
class LdapConfig(models.Model):
    _inherit = 'res.company.ldap'
    inportar=fields.Boolean("Importar",default=True)
