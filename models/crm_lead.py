from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # Campo personalizado para identificar visualmente de dónde llegó
    blazar_source_platform = fields.Selection([
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('whatsapp', 'WhatsApp'),
        ('other', 'Otro Webhook')
    ], string='Plataforma de Origen', readonly=True, copy=False)