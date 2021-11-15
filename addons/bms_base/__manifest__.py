# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Deby Wahyu Kurdian <deby.wahyu.kurdian@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

{
    'name'      : "Base Module for Bumi Maju Sawit",
    'category'  : 'Palm Oil Mills',
    'version'   : '1.0.0.1',
    'author'    : "Konsaltén Indonesia",
    'website'   : "www.kosaltenindonesia.com",
    'license'   : 'AGPL-3',
    'depends'   : ['base', 'c10i_base'],
    'summary'   : """
                        BMS Base Module
                    """,
    'description'   : """
                        Customize Modul Base BMS
                    """,
    'data'      : [
        'data/base_data.xml',
        # 'data/ir_config_parameter_background.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
}
