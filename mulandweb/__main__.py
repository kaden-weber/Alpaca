#!/usr/bin/env python3
# coding: utf-8

from . import app

if __name__ == '__main__':
    import os
    cores = os.cpu_count()
    if cores is not None:
        workers = 2 * cores + 1
    else:
        workers = 9
    app.run(host='', port=8000, server='gunicorn',
            workers=workers)
