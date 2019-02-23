# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api

class LdapLog(models.Model):
    _name = 'ldap.log'

    name = fields.Char()
    user_id = fields.Many2one('res.users', string='Responsable', select=True, default=lambda self: self.env.uid)
    fecha = fields.Datetime(string='Dia y Hora de la modificación', default=fields.datetime.now())
    notas = fields.Char(required=True)