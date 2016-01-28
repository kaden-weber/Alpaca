# coding: utf-8

'''Configuration parameters of MulandWeb'''

import os

# Muland Binary interface
muland_binary = os.getenv('MULAND_BINARY_PATH', 'bin/muland')
muland_model = os.getenv('MULAND_MODEL_PATH', 'model')
muland_work = os.getenv('MULAND_WORK_PATH', 'work')

# MulandWeb
mulandweb_host = os.getenv('MULANDWEB_HOST', '0.0.0.0')
mulandweb_port = os.getenv('MULANDWEB_PORT', 8000)

# Database
db_url = os.getenv('MULAND_DB_URL', 'postgresql://gis:gis@localhost/gis')

try:
    from mulandlocal import *
except ImportError:
    pass
