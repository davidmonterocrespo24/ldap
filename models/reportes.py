# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ldap
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)



class GestionActualizarGrupo(models.TransientModel):
    _name = 'gestion.actualizargrupo'
    _description = 'Reporte'
    usuario_ids = fields.Many2many('gestion.usuario', string='Usuario')
    grupo_ids = fields.Many2one('gestion.grupo', string='Grupo')

    @api.one
    def actualizar_grupo(self):
        self.usuario_ids.update({'grupo_ids': self.grupo_ids})


class GestionEstadisticas(models.TransientModel):
    _name = 'gestion.estadistica'
    _description = 'Reporte'
    usuario_ids = fields.Many2many('gestion.usuario', string='Usuario')
    grupo_ids = fields.Many2one('gestion.grupo', string='Grupo')
    cantidad = fields.Integer('Cantidad de Integrantes')

    @api.multi
    def _reopen_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,  # this model
            'res_id': self.id,  # the current wizard record
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'}

    @api.multi
    def cantidad_usuario_por_grupo(self):
        self.cantidad = len(self.grupo_ids.usuario_ids)
        self.usuario_ids = self.grupo_ids.usuario_ids
        return self._reopen_form()
