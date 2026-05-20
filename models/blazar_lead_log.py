from odoo import models, fields, api
import json
from ..tools.facebook_processor import FacebookLeadProcessor

class BlazarLeadLog(models.Model):
    _name = 'blazar.lead.log'
    _description = 'Logs de Leads Externos'
    _order = 'create_date desc'

    source = fields.Selection([
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('whatsapp', 'WhatsApp'),
        ('manual', 'Manual/Otros')
    ], string='Origen', required=True)

    state = fields.Selection([
        ('success', 'Éxito'),
        ('error', 'Error'),
        ('pending', 'Pendiente')
    ], string='Estado', default='pending')

    payload = fields.Text(string='JSON Original (Payload)')
    error_message = fields.Text(string='Mensaje de Error')
    lead_id = fields.Many2one('crm.lead', string='Lead Creado')

    def action_retry_processing(self):
        """
        Toma el JSON guardado e intenta procesarlo nuevamente.
        """
        for record in self:
            try:
                # 1. Recuperamos el JSON crudo que falló
                payload = json.loads(record.payload)

                # 2. Llamamos a tu procesador (le pasamos el entorno y este mismo registro)
                procesador = FacebookLeadProcessor(self.env, record)
                procesador.process_payload(payload)

                # 3. Si llega hasta aquí, fue un éxito
                record.write({
                    'state': 'success',
                    'error_message': False
                })
            except Exception as e:
                # Si vuelve a fallar, actualizamos el error
                record.write({
                    'state': 'error',
                    'error_message': f"Reintento fallido: {str(e)}"
                })

    @api.model
    def process_pending_leads_cron(self):
        """ Función que ejecuta Odoo automáticamente cada 5 minutos """
        pending_logs = self.search([('state', '=', 'pending')])
        for record in pending_logs:
            try:
                payload = json.loads(record.payload)
                procesador = FacebookLeadProcessor(self.env, record)
                procesador.process_payload(payload)

                record.write({
                    'state': 'success',
                    'error_message': False
                })
            except Exception as e:
                record.write({
                    'state': 'error',
                    'error_message': f"Error en cron: {str(e)}"
                })