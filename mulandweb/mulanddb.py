# coding: utf-8

from math import pi, acos, sin, cos, sqrt, log, atan, exp

from sqlalchemy import select, func, and_

from . import db
from .muland import MulandData

def wgs84_to_google(lat, lng):
    '''Converts a point from WGS84 to Google coordinates'''
    earth_radius = 6378137 # [m]
    max_lat = 85.0511287798

    lat = max(min(max_lat, lat), -max_lat)
    lat_sin = sin(lat / 180 * pi)

    x = lng / 180 * pi * earth_radius
    y = log((1 + lat_sin) / (1 - lat_sin)) / 2 * earth_radius

    return x, y

class MulandDB:
    '''Provides data retrival from Muland Database'''
    def __init__(self, model, lat, lng):
        '''Initialize class'''
        assert isinstance(model, str)
        assert isinstance(lat, (int, float))
        assert isinstance(lng, (int, float))
        x, y = wgs84_to_google(lat, lng)
        self.model = model
        self.x = x
        self.y = y

    # zones
    #"I_IDX";"INDAREA";"COMAREA";"SERVAREA";"TOTAREA";"TOTBUILT";"INCOMEHH";"DIST_ACC"
    #1.00;2.7441056;0.4679935;3.2301371;8968.0590000;10.9089400;0.00;2.8959340
    def _get_zones_records(self):
        '''Get zones records'''
        point_wkt = 'POINT(%d %d)' % (self.x, self.y)
        zones_table = db.zones
        models_table = db.models

        s = (select([zones_table.c.id, zones_table.c.data])
             .select_from(zones_table.join(
                models_table,
                zones_table.c.models_id == models_table.c.id))
             .where(func.ST_Contains(zones_table.c.area, point_wkt))
             .where(models_table.c.name == self.model)
        )

        records = []
        for row in db.engine.execute(s):
            data = [row['id']]
            data.extend(row['data'])
            records.append(data)

        return records

    # agents
    #"IDAGENT";"IDMARKET";"IDAGGRA";"UPPERBB";"HHINC";"RHO";"FNIP";"ONES"
    #1.00;1.00;1.00;50000.00;674.8841398;11.8789000;0.00;1.00
    def _get_agents_records(self):
        '''Get agents records'''
        db_models = db.models
        db_agents = db.agents

        s = (select([db_agents.c.id,
                     db_agents.c.markets_id,
                     db_agents.c.aggra_id,
                     db_agents.c.upperbb,
                     db_agents.c.data])
            .select_from(db_agents.join(db_models, db_agents.c.models_id == db_models.c.id))
            .where(db_models.c.name == self.model))

        records = []
        for row in db.engine.execute(s):
            data = row[0:4]
            data.extend(row[5])
            records.append(data)

        return records

# agents_zones
#"H_IDX";"I_IDX";"ACC";"P_LN_ATT"
#1.00;1.00;0.7308194;0.0000000

# bids_adjustments
#"H_IDX";"V_IDX";"I_IDX";"BIDADJ"
#1.00;1.00;1.00;0.0000000000

# bids_functions
#"IDMARKET";"IDAGGRA";"IDATTRIB";"LINEAPAR";"CAGENT_X";"CREST_X";"CACC_X";"CZONES_X";"EXPPAR_X";"CAGENT_Y";"CREST_Y";"CACC_Y";"CZONES_Y";"EXPPAR_Y"
#1.0000;1.0000;1.0000;15.7300;0.0000;5.0000;0.0000;0.0000;1.0000;0.0000;0.0000;0.0000;0.0000;0.0000

# demand
#"H_IDX";"DEMAND"
#1.00;10562.7974402

# demand_exogenous_cutoff
#"H_IDX";"V_IDX";"I_IDX";"DCUTOFF"
#1.00;1.00;1.00;1.00

# real_estates_zones
#"V_IDX";"I_IDX";"M_IDX";"LOTSIZE";"BUILT";"IS_HOUSE";"IS_APT"
#1.00;1.00;1.00;3.4800000;0.027670;1.00;0.00

# rent_adjustments
#"V_IDX";"I_IDX";"RENTADJ"
#1.00;1.00;0.00

# rent_functions
#"IDMARKET";"IDATTRIB";"SCALEPAR";"LINEAPAR";"CREST_X";"CZONES_X";"EXPPAR_X";"CREST_Y";"CZONES_Y";"EXPPAR_Y"
#1.00;1.00;0.4000000000;0.323614000;5.00;0.00;1.00;0.00;0.00;0.00

# subsidies
#"H_IDX";"V_IDX";"I_IDX";"SUBSIDIES"
#1.00;1.00;1.00;0.0000000000

# supply
#"V_IDX";"I_IDX";"NREST"
#1.00;1.00;0.0000000000
