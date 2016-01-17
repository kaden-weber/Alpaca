#!/usr/bin/env python3
# coding: utf-8

import bottle
import re
import json

from muland import Muland, ModelNotFound, MulandRunError

class MulandWeb:
    _model_re = re.compile('[a-z]')

    def __init__(self):
        self.app = bottle.Bottle()
        self.app.post('/<model>', callback=self.post_handler)

    def __getattr__(self, name):
        '''Fallback to bottle app attributes'''
        return getattr(self.app, name)

    def __call__(self, *args, **kwargs):
        '''Call on Bottle app'''
        return self.app(*args, **kwargs)

    def post_handler(self, model):
        '''Handles POST requests to server'''
        # Validate model name
        if self._model_re.match(model) is None:
            raise bottle.HTTPError(404)

        # Prepare data
        data_in = bottle.request.json
        if data_in is not None:
            if not isinstance(data_in, dict):
                raise bottle.HTTPError(400, 'JSON root isn\'t a dict')
            mudata = {}
            for key, value in data_in.items():
                if key not in Muland.input_files:
                    continue
                if not isinstance(value, list):
                    raise bottle.HTTPError(400, 'Input "%s" isn\'t a list' % key)
                if len(value) > 0:
                    rowlength = len(value[0])
                    if any((len(row) != rowlength for row in value)):
                        raise bottle.HTTPError(400, 'Variable length size for input "%s"' % key)
                mudata[key] = value
        else:
            mudata = {}

        # Run Mu-Land
        try:
            mu = Muland(model, **mudata)
        except ModelNotFound:
            raise bottle.HTTPError(404)
        try:
            mu.run()
        except MulandRunError as e:
            raise HTTPError(500, exception=e)

        # Send response
        bottle.response.headers['Content-Type'] = 'application/json'
        return json.dumps(mu.output_data)

app = application = MulandWeb()

if __name__ == '__main__':
    import os
    cores = os.cpu_count()
    if cores is not None:
        workers = 2 * cores + 1
    else:
        workers = 9
    app.run(host='', port=8000, server='gunicorn',
            workers=workers)
