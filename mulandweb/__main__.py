#!/usr/bin/env python3
# coding: utf-8

import os

from . import config, app

app.run(host=config.mulandweb_host,
        port=config.mulandweb_port,
        server='gunicorn',
        workers=config.mulandweb_workers)
