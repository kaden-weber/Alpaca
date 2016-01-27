#!/usr/bin/env python3
# coding: utf-8

import bottle
import re
import json

from .muland import Muland, MulandRunError
from .mulanddb import Parcel, Unit, ModelNotFound
from . import app

__all__ = ['post_handler']

_model_re = re.compile('[a-z]')

@app.post('/<model>')
def post_handler(self, model):
    '''Handles POST requests to server'''
    # Validate model name
    if _model_re.match(model) is None:
        raise bottle.HTTPError(404)

    # Prepare data
    data_in = bottle.request.json
    if data_in is None:
        raise bottle.HTTPError(400, 'No input data.')

    if not isinstance(data_in, dict) or 'parcels' not in data_in:
        raise bottle.HTTPError(400, 'Invalid input data.')

    parcels = data_in['parcels']
    if not isinstance(parcels, list):
        raise bottle.HTTPError(400, "'parcels' isn't an array")

    dbparcels = []
    for parcel in parcels:
        if 'lnglat' not in parcel:
            raise bottle.HTTPError(400, "'lnglat' not in 'parcels' items")

        lnglat = parcel['lnglat']
        if not isinstance(lnglat, list) or len(lnglat) != 2:
            raise bottle.HTTPError(400, "'lnglat' isn't array with 2 elements")

        if not all((isinstance(x, (int, float)) for x in lnglat)):
            raise bottle.HTTPError(400, "lng or lat not a number")

        if 'units' not in parcel:
            raise bottle.HTTPError(400, "'units' not in 'parcels' items")
        units = parcel['units']
        if not isinstance(units, list):
            raise bottle.HTTPError(400, "'units' isn't an array")

        for unit in units:
            if 'type' not in unit:
                raise bottle.HTTPError(400, "'type' not in unit")
            if not isinstance(unit['type'], (int, float)):
                raise bottle.HTTPError(400, "'type' isn't a number")
            if 'amount' not in unit:
                raise bottle.HTTPError(400, "'amount' not in unit")
            if not isinstance(unit['amount'], (int, float)):
                raise bottle.HTTPError(400, "'amount' isn't a number")

        dbparcels.append(Parcel(
                   lnglat=tuple(lnglat),
                   unit=[Unit(type=unit['type'], amount=unit['amount'])
                         for unit in units]))

    # Get data from MulandDB
    try:
        mudata = MulandDB(model, parcels)
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
