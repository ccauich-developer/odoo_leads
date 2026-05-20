import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class OdooMultileadsWebhook(http.Controller):

    @http.route('/webhook/leads/facebook', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def facebook_receive(self, **kwargs):
        """
        Maneja tanto la verificación inicial de Meta (GET) como la recepción de leads (POST).
        """

        # 1. EL SALUDO INICIAL DE FACEBOOK (Verificación del Webhook)
        if request.httprequest.method == 'GET':
            # Vamos a la base de datos a leer la palabra secreta que guardaste en Ajustes
            mi_token_secreto = request.env['ir.config_parameter'].sudo().get_param('odoo_multileads.fb_verify_token')

            # Facebook nos manda su token y un "reto" (challenge)
            token_recibido = kwargs.get('hub.verify_token')
            challenge = kwargs.get('hub.challenge')

            if token_recibido and token_recibido == mi_token_secreto:
                _logger.info("¡Webhook de Facebook verificado con éxito!")
                # Si la contraseña coincide, le devolvemos su propio reto
                return request.make_response(challenge, headers=[('Content-Type', 'text/plain')])
            else:
                _logger.warning("Intento de verificación fallido. Token incorrecto.")
                return request.make_response("Error de validación", status=403)

        # 2. RECEPCIÓN DE LEADS ASÍNCRONA (POST)
        try:
            cuerpo_crudo = request.httprequest.data
            payload = json.loads(cuerpo_crudo)

            # SOLO GUARDAMOS EL LOG EN ESTADO PENDIENTE
            request.env['blazar.lead.log'].sudo().create({
                'source': 'facebook',
                'payload': json.dumps(payload),
                'state': 'pending'
            })

            # ¡RESPONDEMOS DE INMEDIATO A FACEBOOK!
            return request.make_response(
                json.dumps({"status": "success", "message": "Recibido y encolado"}),
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            _logger.error("Error procesando Webhook de Facebook: %s", str(e))
            return request.make_response(
                json.dumps({"status": "error", "reason": str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )