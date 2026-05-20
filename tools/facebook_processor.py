import json
import logging
import requests
from odoo import fields

_logger = logging.getLogger(__name__)

class FacebookLeadProcessor:
    def __init__(self, env, log_record):
        self.env = env
        self.log_record = log_record
        # ELIMINAMOS la búsqueda del token global aquí.
        self.api_url = "https://graph.facebook.com/v19.0"

    def process_payload(self, payload):
        """
        Atrapa el ID del webhook de Facebook y detona la búsqueda de datos reales.
        """
        # 1. Navegar por el JSON de Facebook para encontrar el ticket (leadgen_id) y la página (page_id)
        try:
            entry = payload.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            leadgen_id = value.get('leadgen_id')
            fb_page_id = value.get('page_id')
        except Exception:
            leadgen_id = None
            fb_page_id = None

        if not leadgen_id or not fb_page_id:
            self.log_record.sudo().write({'state': 'error', 'error_message': 'Falta leadgen_id o page_id en el payload'})
            _logger.error("No se encontró leadgen_id o page_id en el payload de Facebook")
            return

        # 2. Ejecutar la llamada a la Graph API pasando AMBOS IDs
        fb_data = self._fetch_lead_from_facebook(leadgen_id, fb_page_id)

        if 'error' in fb_data:
            _logger.error("Error de Graph API: %s", fb_data)
            self.log_record.sudo().write({'state': 'error', 'error_message': fb_data.get('error')})
            return

        # 3. Mandar a crear el lead con los datos extraídos
        self._create_odoo_lead(fb_data, fb_page_id)

    def _fetch_lead_from_facebook(self, lead_id, page_id):
        """
        Paso 2: BÚSQUEDA DINÁMICA DEL TOKEN Y CONSULTA A META
        """
        _logger.info("Consultando la API Graph para el ID: %s", lead_id)

        # 1. Buscamos la página específica en nuestra tabla de Alias
        pagina_en_odoo = self.env['odoo_multileads.fb_page'].sudo().search([('page_id', '=', page_id)], limit=1)

        # 2. Validamos que exista y que el administrador le haya puesto un token
        if not pagina_en_odoo or not pagina_en_odoo.access_token:
            error_msg = f"La página {page_id} no está registrada en los Alias o le falta el Token de Acceso."
            _logger.error(error_msg)
            return {'error': error_msg}

        # 3. Extraemos la llave específica
        token_dinamico = pagina_en_odoo.access_token

        # 4. Hacemos la consulta con el token correcto
        graph_url = f"{self.api_url}/{lead_id}?access_token={token_dinamico}"
        response = requests.get(graph_url)

        if response.status_code != 200:
            return {'error': f"Error de Meta: {response.text}"}

        return response.json()

    def _create_odoo_lead(self, fb_data, fb_page_id=None):
        """
        Paso 3: Traducir los campos de FB a campos de Odoo, incluyendo Etiquetas y Campañas.
        """
        # Extraemos los datos de la lista 'field_data'
        raw_fields = fb_data.get('field_data', [])
        extracted_data = {field['name']: field['values'][0] for field in raw_fields}

        # ---------------------------------------------------------
        # LÓGICA DE ALIAS: BÚSQUEDA DEL NOMBRE PARA EL PREFIJO
        # ---------------------------------------------------------
        page_record = None
        if fb_page_id:
            # Como ya validamos en el paso anterior que la página existe, solo la buscamos para extraer el nombre
            page_record = self.env['odoo_multileads.fb_page'].sudo().search([('page_id', '=', fb_page_id)], limit=1)

        # 3. Armamos el texto final para el Lead
        alias_prefix = f"[{page_record.name}]" if page_record else "[FB]"

        # 1. LÓGICA DE ETIQUETAS (RF-006)
        tag_id = self.env['crm.tag'].sudo().search([('name', '=', 'Facebook')], limit=1)
        if not tag_id:
            tag_id = self.env['crm.tag'].sudo().create({'name': 'Facebook', 'color': 10})

        # 2. LÓGICA DE CAMPAÑAS (RF-004)
        campaign_name = fb_data.get('campaign_name', 'Facebook - General')
        campaign_id = self.env['utm.campaign'].sudo().search([('name', '=', campaign_name)], limit=1)
        if not campaign_id:
            campaign_id = self.env['utm.campaign'].sudo().create({'name': campaign_name})

        # 3. CREACIÓN DEL LEAD EN EL CRM
        lead_vals = {
            'name': f"{alias_prefix} {extracted_data.get('full_name', 'Nuevo Prospecto')}",
            'contact_name': extracted_data.get('full_name'),
            'email_from': extracted_data.get('email'),
            'phone': extracted_data.get('phone_number'),
            'blazar_source_platform': 'facebook',
            'description': f"Lead ID de Facebook: {fb_data.get('id')}\nFormulario: {fb_data.get('form_id')}",

            # Vinculaciones
            'campaign_id': campaign_id.id,
            'tag_ids': [(4, tag_id.id)]
        }

        nuevo_lead = self.env['crm.lead'].sudo().create(lead_vals)

        # --- LÓGICA DE NOTIFICACIÓN POR CORREO ---
        try:
            # 1. Buscar la plantilla que acabamos de crear
            template = self.env.ref('odoo_multileads.email_template_new_fb_lead')

            # 2. Definir quiénes reciben el correo
            admins = self.env['res.users'].sudo().search([('groups_id', 'in', self.env.ref('base.group_system').id)])
            emails_list = ",".join([admin.email for admin in admins if admin.email])

            if template and emails_list:
                # Enviamos el correo usando la plantilla y forzamos el destinatario
                template.sudo().send_mail(nuevo_lead.id, force_send=True, email_values={'email_to': emails_list})
                _logger.info("Notificación de nuevo lead enviada a: %s", emails_list)

        except Exception as e:
            _logger.error("No se pudo enviar la notificación por correo: %s", str(e))

        # 4. Actualizamos la bitácora (RF-007)
        self.log_record.sudo().write({
            'lead_id': nuevo_lead.id,
            'state': 'success'
        })

        _logger.info("Lead creado con éxito desde Facebook: %s", nuevo_lead.name)
        return nuevo_lead