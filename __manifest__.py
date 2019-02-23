# -*- coding: utf-8 -*-
{
    'name': "Gestion de usuario LDAP",

    'summary': """
        Moulo para la gestion de Usuarios  en la universidad de oriente """,

    'description': """
        Guia Primer tutorial
    """,

    'author': "David Montero",
    'website': "http://www.davidmontero.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tutorial',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'base_setup','auth_ldap'],

    # always loaded
    'data': [
        'views/menu.xml',
        'views/wizar.xml',
        'security/ir.model.access.csv',

    ],


    'external_dependencies' : {
        'python' : ['ldap']
    }
}
