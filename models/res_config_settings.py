from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    blazar_enable_facebook = fields.Boolean(
        string='Habilitar Facebook',
        config_parameter='odoo_multileads.enable_facebook'
    )
    blazar_enable_instagram = fields.Boolean(
        string='Habilitar Instagram',
        config_parameter='odoo_multileads.enable_instagram'
    )
    blazar_enable_whatsapp = fields.Boolean(
        string='Habilitar WhatsApp',
        config_parameter='odoo_multileads.enable_whatsapp'
    )
    blazar_enable_telegram = fields.Boolean(
        string='Habilitar Telegram',
        config_parameter='odoo_multileads.enable_telegram'
    )

    blazar_fb_verify_token = fields.Char(
        string='Token de Verificación (Webhook)',
        config_parameter='odoo_multileads.fb_verify_token'
    )