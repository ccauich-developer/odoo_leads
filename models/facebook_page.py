from odoo import models, fields

class FacebookPageAlias(models.Model):
    _name = 'odoo_multileads.fb_page'
    _description = 'Alias de Páginas de Facebook'

    name = fields.Char(string='Nombre del Alias', help="Ej: Página de Facebook", required=True)
    page_id = fields.Char(string='ID de la Página de Meta', help="El identificador numérico de la página", required=True)
    access_token = fields.Char(string='Token de Acceso (Meta)', help="El token permanente de esta página específica", required=True)

    _sql_constraints = [
        ('page_id_unique', 'unique(page_id)', 'El ID de la página ya está registrado.')
    ]