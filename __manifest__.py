{
    'name': 'Leads multiconector',
    'version': '1.0.0',
    'summary': 'Integración modular de Leads vía Webhooks (Facebook Lead Ads)',
    'category': 'Sales/CRM',
    'author': 'Odoo S.A.',
    'depends': ['crm', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/blazar_lead_log_views.xml',
        'views/res_config_settings_views.xml',
        'views/fb_page_views.xml',
        'data/cron_jobs.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}