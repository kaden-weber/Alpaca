# coding: utf-8

from math import pi, acos, sin, cos, sqrt, log, atan, exp
from collections import namedtuple

from sqlalchemy import select, func, and_, text

from .muland import MulandData
from . import db

__all__ = ['MulandDB']

class MulandDBException(Exception):
    pass
class ModelNotFound(MulandDBException):
    pass

class MulandDB:
    '''Provides data retrival from Muland Database'''
    def __init__(self, model: str, locations: list):
        '''Initialize class'''
        assert isinstance(model, str)

        self.conn = db.engine.connect()

        s = select([db.models.c.id]).where(db.models.c.name == model)
        result = self.conn.execute(s)
        row = result.fetchone()
        result.close()
        if result is None:
            raise ModelNotFound

        points = []
        i = 0
        for loc in locations:
            assert isinstance(loc['lnglat'][0], (int, float))
            assert isinstance(loc['lnglat'][1], (int, float))
            for unit in loc['units']:
                point = {'id': i,
                         'lng': loc['lnglat'][0],
                         'lat': loc['lnglat'][1],
                         'types_id': unit['type']}
                points.append(point)
                i += 1

        self.models_id = row[0]
        self.points = points
        self.loc = locations

    def get(self):
        '''Get data for Muland'''
        data = {}
        headers = self._get_headers()

        # zones
        zone_map, zones_records = self._get_zones()
        data['zones'] = MulandData(header=['I_IDX'] + headers['zones_header'],
                                   records=zones_records)
        for point_idx, zones_id in zone_map:
            self.points[point_idx]['zones_id'] = zones_id

        # agents
        data['agents'] = MulandData(
            header=['IDAGENT', 'IDMARKET', 'IDAGGRA', 'UPPERBB'] + headers['agents_header'],
            records=self._get_agents_records()
        )

        # agents_zones
        data['agents_zones'] = MulandData(
            header=['H_IDX', 'I_IDX', 'ACC', 'P_LN_ATT'] + headers['agents_zones_header'],
            records=self._get_agents_zones_records()
        )

        # bids_adjustments
        data['bids_adjustments'] = MulandData(
            header=['H_IDX', 'V_IDX', 'I_IDX', 'BIDADJ'],
            records=self._get_bids_adjustments_records()
        )

        # bids_functions
        data['bids_functions'] = MulandData(
            header=['IDMARKET', 'IDAGGRA', 'IDATTRIB', 'LINEAPAR', 'CAGENT_X',
                    'CREST_X', 'CACC_X', 'CZONES_X', 'EXPPAR_X', 'CAGENT_Y',
                    'CREST_Y', 'CACC_Y', 'CZONES_Y', 'EXPPAR_Y'],
            records=self._get_bids_functions_records()
        )

        # demand
        data['demand'] = MulandData(
            header=['H_IDX', 'DEMAND'],
            records=self._get_demand_records()
        )

        # demand_exogenous_cutoff
        data['demand_exogenous_cutoff'] = MulandData(
            header=['H_IDX', 'V_IDX', 'I_IDX', 'DCUTOFF'],
            records=self._get_demand_exogenous_cutoff_records()
        )

        # real_estates_zones
        data['real_estates_zones'] = MulandData(
            header=['V_IDX', 'I_IDX', 'M_IDX'] + headers['real_estates_zones_header'],
            records=self._get_real_estates_zones()
        )

        # rent_adjustments
        data['rent_adjustments'] = MulandData(
            header=['V_IDX', 'I_IDX', 'RENTADJ'],
            records=self._get_rent_adjustments()
        )

        # rent_funtions
        data['rent_functions'] = MulandData(
            header=['IDMARKET', 'IDATTRIB', 'SCALEPAR', 'LINEAPAR', 'CREST_X',
                    'CZONES_X', 'EXPPAR_X', 'CREST_Y', 'CZONES_Y', 'EXPPAR_Y'],
            records=self._get_rent_functions()
        )

        # subsidies
        data['subsidies'] = MulandData(
            header=['H_IDX', 'V_IDX', 'I_IDX', 'SUBSIDIES'],
            records=self._get_subsidies()
        )

        # supply
        data['supply'] = MulandData(
            header=['V_IDX', 'I_IDX', 'NREST'],
            records=self._get_supply()
        )

        return data

    def _get_headers(self):
        '''Get CSV header records'''
        db_models = db.models

        s = (select([db_models.c.zones_header,
                    db_models.c.agents_header,
                    db_models.c.agents_zones_header,
                    db_models.c.real_estates_zones_header])
            .where(db_models.c.id == self.models_id)
            .limit(1))

        result = self.conn.execute(s)
        header = dict(result.fetchone())
        result.close()

        return header

    # zones
    #"I_IDX";"INDAREA";"COMAREA";"SERVAREA";"TOTAREA";"TOTBUILT";"INCOMEHH";"DIST_ACC"
    #1.00;2.7441056;0.4679935;3.2301371;8968.0590000;10.9089400;0.00;2.8959340
    def _get_zones(self):
        '''Get zones records

        Returns tuple (zone_map, records). The zone_map field carries a
        list of tuples (point_id, zone_id). The records field carries a list
        of records for the zones file.
        '''
        db_zones = db.zones
        db_models = db.models

        # Generated query like:
        #SELECT
        #    points.idx as point_id,
        #    zones.id as zones_id,
        #    zones.data
        #FROM
        #    models
        #    JOIN zones ON zones.models_id = models.id
        #    JOIN (VALUES
        #        (0, ST_Transform(ST_SetSRID(ST_Point(-70.5602732772102, 41.846681982857724), 4326), 900913)),
        #        (1, ST_Transform(ST_SetSRID(ST_Point(-70.548986695639755, 41.818260285896393), 4326), 900913)),
        #        (2, ST_Transform(ST_SetSRID(ST_Point(-70.5602832772102, 41.846691982857724), 4326), 900913))
        #    ) AS points (idx, geom) ON ST_Contains(zones.area, points.geom)
        #WHERE
        #    models.id = 1
        #ORDER BY
        #    points.idx

        values = ', '.join(
            ['(%s, ST_Transform(ST_SetSRID(ST_Point(%s, %s), 4326), 900913))' %
             (point['id'], point['lng'], point['lat'])
             for point in self.points])

        s = (select([text('points.idx '),
                     db_zones.c.id,
                     db_zones.c.data])
            .select_from(db_zones
                .join(text('(VALUES %s) AS points (idx, geom) ' % values),
                      func.ST_Contains(db_zones.c.area, text('points.geom'))))
            .where(db_zones.c.models_id == self.models_id)
            .order_by(text('points.idx')))

        result = self.conn.execute(s)
        zone_map = []
        records = []
        for row in result:
            data = [row[0] + 1]
            data.extend(row[2])
            records.append(data)
            zone_map.append([row[0], row[1]])
        result.close()

        return zone_map, records

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
            .where(db_agents.c.models_id == self.models_id))

        result = self.conn.execute(s)
        records = []
        for row in db.engine.execute(s):
            data = list(row[0:4])
            data.extend(row[4])
            records.append(data)
        result.close()

        return records

    # agents_zones
    #"H_IDX";"I_IDX";"ACC";"P_LN_ATT"
    #1.00;1.00;0.7308194;0.0000000
    def _get_agents_zones_records(self):
        '''Get agents records'''
        db_models = db.models
        db_azones = db.agents_zones

        values = ', '.join(['(%s, %s)' % (point['id'] + 1, point['zones_id'])
                            for point in self.points])

        s = (select([db_azones.c.agents_id,
                     text('points.idx'),
                     db_azones.c.acc,
                     db_azones.c.att,
                     db_azones.c.data])
            .select_from(db_azones
                .join(text('(VALUES %s) AS points (idx, zones_id) ' % values),
                      db_azones.c.zones_id == text('points.zones_id')))
            .where(db_azones.c.models_id == self.models_id))

        result = self.conn.execute(s)
        records = []
        for row in db.engine.execute(s):
            data = list(row[0:4])
            data.extend(row[4])
            records.append(data)
        result.close()

        return records

    # bids_adjustments
    #"H_IDX";"V_IDX";"I_IDX";"BIDADJ"
    #1.00;1.00;1.00;0.0000000000
    def _get_bids_adjustments_records(self):
        '''Get bids_adjustments records'''
        db_badj = db.bids_adjustments

        values = ', '.join(['(%s, %s, %s)' %
            (point['id'] + 1, point['zones_id'], point['types_id'])
            for point in self.points])

        s = (select([db_badj.c.agents_id,
                     db_badj.c.types_id,
                     text('points.idx'),
                     db_badj.c.bidadj])
            .select_from(db_badj
                .join(text('(VALUES %s) AS points (idx, zones_id, types_id) ' % values),
                      and_(db_badj.c.zones_id == text('points.zones_id'),
                           db_badj.c.types_id == text('points.types_id'))))
            .where(db_badj.c.models_id == self.models_id))

        result = self.conn.execute(s)
        records = [list(row) for row in result]
        result.close()

        return records

    # bids_functions
    #"IDMARKET";"IDAGGRA";"IDATTRIB";"LINEAPAR";"CAGENT_X";"CREST_X";"CACC_X";"CZONES_X";"EXPPAR_X";"CAGENT_Y";"CREST_Y";"CACC_Y";"CZONES_Y";"EXPPAR_Y"
    #1.0000;1.0000;1.0000;15.7300;0.0000;5.0000;0.0000;0.0000;1.0000;0.0000;0.0000;0.0000;0.0000;0.0000
    def _get_bids_functions_records(self):
        '''Get bids_functions records'''
        db_bfunc = db.bids_functions

        s = (select([db_bfunc.c.markets_id,
                     db_bfunc.c.aggra_id,
                     db_bfunc.c.idattrib,
                     db_bfunc.c.lineapar,
                     db_bfunc.c.cagent_x,
                     db_bfunc.c.crest_x,
                     db_bfunc.c.cacc_x,
                     db_bfunc.c.czones_x,
                     db_bfunc.c.exppar_x,
                     db_bfunc.c.cagent_y,
                     db_bfunc.c.crest_y,
                     db_bfunc.c.cacc_y,
                     db_bfunc.c.czones_y,
                     db_bfunc.c.exppar_y])
            .where(db_bfunc.c.models_id == self.models_id))

        result = self.conn.execute(s)
        records = [list(row) for row in result]
        result.close()

        return records

    # demand
    #"H_IDX";"DEMAND"
    #1.00;10562.7974402
    def _get_demand_records(self):
        '''Get demand records'''
        db_demand = db.demand
        db_models = db.models

        s = (select([db_demand.c.agents_id,
                     db_demand.c.demand])
            .where(db_demand.c.models_id == self.models_id))

        result = self.conn.execute(s)
        records = [list(row) for row in result]
        result.close()

        return records

    # demand_exogenous_cutoff
    #"H_IDX";"V_IDX";"I_IDX";"DCUTOFF"
    #1.00;1.00;1.00;1.00
    def _get_demand_exogenous_cutoff_records(self):
        '''Get demand_exogenous_cutoff records'''
        db_decutoff = db.demand_exogenous_cutoff
        db_models = db.models
        db_zones = db.zones

        values = ', '.join(['(%s, %s, %s)' %
            (point['id'] + 1, point['zones_id'], point['types_id'])
            for point in self.points])

        s = (select([db_decutoff.c.agents_id,
                     db_decutoff.c.types_id,
                     text('points.idx'),
                     db_decutoff.c.dcutoff])
            .select_from(db_decutoff
                .join(text('(VALUES %s) AS points (idx, zones_id, types_id) ' % values),
                      and_(db_decutoff.c.zones_id == text('points.zones_id'),
                           db_decutoff.c.types_id == text('points.types_id'))))
            .where(db_decutoff.c.models_id == self.models_id))

        result = self.conn.execute(s)
        records = [list(row) for row in result]
        result.close()

        return records

    # real_estates_zones
    #"V_IDX";"I_IDX";"M_IDX";"LOTSIZE";"BUILT";"IS_HOUSE";"IS_APT"
    #1.00;1.00;1.00;3.4800000;0.027670;1.00;0.00
    def _get_real_estates_zones(self):
        '''Get real_estates_zones records'''
        db_rezones = db.real_estates_zones
        db_models = db.models

        values = ', '.join(['(%s, %s, %s)' %
            (point['id'] + 1, point['zones_id'], point['types_id'])
            for point in self.points])

        s = (select([db_rezones.c.types_id,
                     text('points.idx'),
                     db_rezones.c.markets_id,
                     db_rezones.c.data])
            .select_from(db_rezones
                .join(text('(VALUES %s) AS points (idx, zones_id, types_id) ' % values),
                      and_(db_rezones.c.zones_id == text('points.zones_id'),
                           db_rezones.c.types_id == text('points.types_id'))))
            .where(db_rezones.c.models_id == self.models_id))

        result = self.conn.execute(s)
        records = []
        for row in result:
            data = list(row[:3])
            data.extend(row[3])
            records.append(data)

        result.close()
        return records

    # rent_adjustments
    #"V_IDX";"I_IDX";"RENTADJ"
    #1.00;1.00;0.00
    def _get_rent_adjustments(self):
        '''Get rent_adjustments records'''
        db_rentadj = db.rent_adjustments

        values = ', '.join(['(%s, %s, %s)' %
            (point['id'] + 1, point['zones_id'], point['types_id'])
            for point in self.points])

        s = (select([db_rentadj.c.types_id,
                     text('points.idx'),
                     db_rentadj.c.adjustment])
            .select_from(db_rentadj
                .join(text('(VALUES %s) AS points (idx, zones_id, types_id) ' % values),
                      and_(db_rentadj.c.zones_id == text('points.zones_id'),
                           db_rentadj.c.types_id == text('points.types_id'))))
            .where(db_rentadj.c.models_id == self.models_id))

        result = self.conn.execute(s)
        records = [list(row) for row in result]
        result.close()

        return records

    # rent_functions
    #"IDMARKET";"IDATTRIB";"SCALEPAR";"LINEAPAR";"CREST_X";"CZONES_X";"EXPPAR_X";"CREST_Y";"CZONES_Y";"EXPPAR_Y"
    #1.00;1.00;0.4000000000;0.323614000;5.00;0.00;1.00;0.00;0.00;0.00
    def _get_rent_functions(self):
        '''Get rent_functions records'''
        db_rentfunc = db.rent_functions
        db_models = db.models

        s = (select([db_rentfunc.c.markets_id,
                     db_rentfunc.c.idattrib,
                     db_rentfunc.c.scalepar,
                     db_rentfunc.c.lineapar,
                     db_rentfunc.c.crest_x,
                     db_rentfunc.c.czones_x,
                     db_rentfunc.c.exppar_x,
                     db_rentfunc.c.crest_y,
                     db_rentfunc.c.czones_y,
                     db_rentfunc.c.exppar_y])
            .where(db_rentfunc.c.models_id == self.models_id))

        result = self.conn.execute(s)
        records = [list(row) for row in result]
        result.close()

        return records

    # subsidies
    #"H_IDX";"V_IDX";"I_IDX";"SUBSIDIES"
    #1.00;1.00;1.00;0.0000000000
    def _get_subsidies(self):
        '''Get subsidies records'''
        db_subsidies = db.subsidies

        values = ', '.join(['(%s, %s, %s)' %
            (point['id'] + 1, point['zones_id'], point['types_id'])
            for point in self.points])

        s = (select([db_subsidies.c.agents_id,
                     db_subsidies.c.types_id,
                     text('points.idx'),
                     db_subsidies.c.subsidies])
            .select_from(db_subsidies
                .join(text('(VALUES %s) AS points (idx, zones_id, types_id) ' % values),
                      and_(db_subsidies.c.zones_id == text('points.zones_id'),
                           db_subsidies.c.types_id == text('points.types_id'))))
            .where(db_subsidies.c.models_id == self.models_id))

        result = self.conn.execute(s)
        records = [list(row) for row in result]
        result.close()

        return records

    # supply
    #"V_IDX";"I_IDX";"NREST"
    #1.00;1.00;0.0000000000
    def _get_supply(self):
        '''Get supply records'''
        db_supply = db.supply

        values = ', '.join(['(%s, %s, %s)' %
            (point['id'] + 1, point['zones_id'], point['types_id'])
            for point in self.points])

        s = (select([db_supply.c.types_id,
                     text('points.idx'),
                     db_supply.c.nrest])
            .select_from(db_supply
                .join(text('(VALUES %s) AS points (idx, zones_id, types_id) ' % values),
                      and_(db_supply.c.zones_id == text('points.zones_id'),
                           db_supply.c.types_id == text('points.types_id'))))
            .where(db_supply.c.models_id == self.models_id))

        result = self.conn.execute(s)
        records = [list(row) for row in result]
        result.close()

        return records
