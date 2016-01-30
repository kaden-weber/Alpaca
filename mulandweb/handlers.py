#!/usr/bin/env python3
# coding: utf-8

import bottle
import re
import json

from .muland import Muland, MulandRunError
from .mulanddb import MulandDB, ModelNotFound
from . import app

__all__ = ['post_handler']

_model_re = re.compile('[a-z]')

@app.post('/<model>')
def post_handler(model):
    '''Handles POST requests to server'''
    # Validate model name
    if _model_re.match(model) is None:
        raise bottle.HTTPError(404)

    # Prepare data
    data_in = bottle.request.json
    if data_in is None:
        raise bottle.HTTPError(400, 'No input data.')

    if not isinstance(data_in, dict):
        raise bottle.HTTPError(400, 'Input data isn\'t an object.')

    if 'loc' not in data_in:
        raise bottle.HTTPError(400, "'loc' is not present at input data.")

    locations = data_in['loc']
    if not isinstance(locations, list):
        raise bottle.HTTPError(400, "'loc' isn't an array")

    for loc in locations:
        if 'lnglat' not in loc:
            raise bottle.HTTPError(400, "'lnglat' not in 'loc' items")

        lnglat = loc['lnglat']
        if not isinstance(lnglat, list) or len(lnglat) != 2:
            raise bottle.HTTPError(400, "'lnglat' isn't array with 2 elements")

        if not all((isinstance(x, (int, float)) for x in lnglat)):
            raise bottle.HTTPError(400, "lng or lat not a number")

        if 'units' not in loc:
            raise bottle.HTTPError(400, "'units' not in 'loc' items")
        units = loc['units']
        if not isinstance(units, list):
            raise bottle.HTTPError(400, "'units' isn't an array")

        for unit in units:
            if 'type' not in unit:
                raise bottle.HTTPError(400, "'type' not in unit")
            if not isinstance(unit['type'], (int, float)):
                raise bottle.HTTPError(400, "'type' isn't a number")

    # Get data from MulandDB
    try:
        mudata = MulandDB(model, locations).get()
    except ModelNotFound:
        raise bottle.HTTPError(404)

    # Run Mu-Land
    mu = Muland(**mudata)
    try:
        mu.run()
    except MulandRunError as e:
        raise HTTPError(500, exception=e)

    # Send response
    bottle.response.headers['Content-Type'] = 'application/json'
    return json.dumps(mu.output_data)
