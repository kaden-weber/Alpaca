# coding: utf-8

from math import pi, acos, sin, cos, sqrt, log, atan, exp

from sqlalchemy import select, func, and_, text

from . import db
from .muland import MulandData

class MulandDB:
    '''Provides data retrival from Muland Database'''
    def __init__(self, model, points):
        '''Initialize class'''
        assert isinstance(model, str)
        points = list(points)
        for lat, lng in points:
            assert isinstance(lat, (int, float))
            assert isinstance(lng, (int, float))
        self.model = model
        self.points = points

    def get(self):
        '''Get data for Muland'''
        data = {}
        headers = self._get_headers()

        # zones
        data['zones'] = MulandData(header=['I_IDX'] + headers['zones_header'],
                                   records=self._get_zones_records())

        return data

    def _get_headers(self):
        '''Get CSV header records'''
        db_models = db.models

        s = (select([db_models.c.zones_header,
                    db_models.c.agents_header,
                    db_models.c.agents_zones_header,
                    db_models.c.real_estates_zones_header])
            .where(db_models.c.name == self.model)
            .limit(1))

        return dict(db.engine.execute(s).fetchone())

    # zones
    #"I_IDX";"INDAREA";"COMAREA";"SERVAREA";"TOTAREA";"TOTBUILT";"INCOMEHH";"DIST_ACC"
    #1.00;2.7441056;0.4679935;3.2301371;8968.0590000;10.9089400;0.00;2.8959340
    def _get_zones_records(self):
        '''Get zones records'''
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
        #    models.name = 'boston'
        #ORDER BY
        #    points.idx

        values = ', '.join(
            ['(%s, ST_Transform(ST_SetSRID(ST_Point(%s, %s), 4326), 900913))' % (idx, lng, lat)
             for idx, (lat, lng) in zip(range(len(self.points)), self.points)])

        s = (select([text('points.idx AS point_id '),
                     db_zones.c.id.label('zones_id'),
                     db_zones.c.data])
            .select_from(db_models
                .join(db_zones, db_models.c.id == db_zones.c.models_id)
                .join(text('(VALUES %s) AS points (idx, geom) ' % values),
                      func.ST_Contains(db_zones.c.area, text('points.geom'))))
            .where(db_models.c.name == self.model)
            .order_by(text('points.idx')))

        records = []
        zone_id = 1
        for row in db.engine.execute(s):
            data = [zone_id]
            data.extend(row[2])
            records.append(data)
            zone_id += 1

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
    def _get_agents_zones_records(self):
        '''Get agents records'''
        db_models = db.models
        db_zones = db.zones
        db_azones = db.agents_zones

        s = (select([db_azones.c.agents_id,
                     db_azones.c.zones_id,
                     db_azones.c.acc,
                     db_azones.c.att,
                     db_azones.c.data])
            .select_from(db_azones
                .join(db_zones, and_(db_azones.c.zones_id == db_zones.c.id,
                                     db_azones.c.models_id == db_zones.c.models_id))
                .join(db_models, db_azones.c.models_id == db_models.c.id))
            .where(func.ST_Contains(db_zones.c.area, self.point_wkt))
            .where(db_models.c.name == self.model))

        records = []
        for row in db.engine.execute(s):
            data = row[0:4]
            data.extend(row[5])
            records.append(data)

        return records

    # bids_adjustments
    #"H_IDX";"V_IDX";"I_IDX";"BIDADJ"
    #1.00;1.00;1.00;0.0000000000
    def _get_bids_adjustments(self):
        '''Get bids_adjustments records'''
        db_badj = db.bids_adjustments
        db_zones = db.zones
        db_models = db.models

        s = (select([db_badj.c.agents_id,
                     db_badj.c.types_id,
                     db_badj.c.zones_id,
                     db_badj.c.bidadj])
            .select_from(db_badj
                .join(db_zones, and_(db_badj.c.zones_id == db_zones.c.id,
                                     db_badj.c.models_id == db_zones.c.models_id))
                .join(db_models, db_badj.c.models_id == db_models.c.id))
            .where(func.ST_Contains(db_zones.c.area, self.point_wkt))
            .where(db_models.c.name == self.model))

        records = [list(row) for row in db.engine.execute(s)]

        return records

    # bids_functions
    #"IDMARKET";"IDAGGRA";"IDATTRIB";"LINEAPAR";"CAGENT_X";"CREST_X";"CACC_X";"CZONES_X";"EXPPAR_X";"CAGENT_Y";"CREST_Y";"CACC_Y";"CZONES_Y";"EXPPAR_Y"
    #1.0000;1.0000;1.0000;15.7300;0.0000;5.0000;0.0000;0.0000;1.0000;0.0000;0.0000;0.0000;0.0000;0.0000
    def _get_bids_functions(self):
        db_bfunc = db.bids_functions
        db_models = db.models

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
            .select_from(db_bfunc
                .join(db_models, db_bfunc.c.models_id == db_models.c.id))
            .where(db_models.c.name == self.model))

        records = [list(row) for row in db.engine.execute(s)]

    # demand
    #"H_IDX";"DEMAND"
    #1.00;10562.7974402
    def _get_demand(self):
        '''Get demand records'''
        db_demand = db.demand
        db_models = db.models

        s = (select([db_demand.c.agents_id,
                     db_demand.c.demand])
            .select_from(db_demand
                .join(db_models, db_demand.c.models_id == db_models.c.id))
            .where(db_models.c.name == self.model))

        records = [list(row) for row in db.engine.execute(s)]
        return records

    # demand_exogenous_cutoff
    #"H_IDX";"V_IDX";"I_IDX";"DCUTOFF"
    #1.00;1.00;1.00;1.00
    def _get_demand_exogenous_cutoff(self):
        '''Get demand_exogenous_cutoff records'''
        db_decutoff = db.demand_exogenous_cutoff
        db_models = db.models
        db_zones = db.zones

        s = (select([db_decutoff.c.agents_id,
                     db_decutoff.c.types_id,
                     db_decutoff.c.zones_id,
                     db_decutoff.c.dcutoff])
            .select_from(db_decutoff
                .join(db_models, db_decutoff.c.models_id == db_models.c.id)
                .join(db_zones, and_(db_decutoff.c.zones_id == db_zones.c.id,
                                     db_decutoff.c.models_id == db_zones.c.models_id)))
            .where(func.ST_Contains(db_zones.c.area, self.point_wkt))
            .where(db_models.c.name == self.model))

        records = [list(row) for row in db.engine.execute(s)]
        return records

    # real_estates_zones
    #"V_IDX";"I_IDX";"M_IDX";"LOTSIZE";"BUILT";"IS_HOUSE";"IS_APT"
    #1.00;1.00;1.00;3.4800000;0.027670;1.00;0.00
    def _get_real_estates_zones(self):
        '''Get real_estates_zones records'''
        db_rezones = db.real_estates_zones
        db_zones = db.zones
        db_models = db.models

        s = (select([db_rezones.c.types_id,
                     db_rezones.c.zones_id,
                     db_rezones.c.markets_id,
                     db_rezones.c.data])
            .select_from(db_rezones
                .join(db_models, db_rezones.c.models_id == db_models.c.id)
                .join(db_zones, _and(db_rezones.c.zones_id == db_zones.c.id,
                                     db_rezones.c.models_id == db_zones.c.models_id)))
            .where(db_models.c.name == self.model)
            .where(func.ST_Contains(db_zones.c.area, self.point_wkt)))

        records = []
        for row in db.engine.execute(s):
            data = row[0:3]
            data.extend(row[4])
            records.append(data)

        return records

    # rent_adjustments
    #"V_IDX";"I_IDX";"RENTADJ"
    #1.00;1.00;0.00
    def _get_rent_adjustments(self):
        '''Get rent_adjustments records'''
        db_rentadj = db.rent_adjustments
        db_models = db.models
        db_zones = db.zones

        s = (select([db_rentadj.c.types_id,
                     db_rentadj.c.zones_id,
                     db_rentadj.c.adjustment])
            .select_from(db_rentadj
                .join(db_models, db_rentadj.c.models_id == db_models.c.id)
                .join(db_zones, and_(db_rentadj.c.zones_id == db_zones.c.id,
                                     db_rentadj.c.models_id == db_zones.c.models_id)))
            .where(func.ST_Contains(db_zones.c.area, self.point_wkt))
            .where(db_models.c.name == self.model))

        records = [list(row) for row in db.engine.execute(s)]
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
            .select_from(db_rentfunc
                .join(db_models, db_rentfunc.c.models_id == db_models.c.id))
            .where(db_models.c.name == self.model))

        records = [list(row) for row in db.engine.execute(s)]
        return records

    # subsidies
    #"H_IDX";"V_IDX";"I_IDX";"SUBSIDIES"
    #1.00;1.00;1.00;0.0000000000
    def _get_subsidies(self):
        '''Get subsidies records'''
        db_subsidies = db.subsidies
        db_models = db.models
        db_zones = db.zones

        s = (select([db_subsidies.c.agents_id,
                     db_subsidies.c.types_id,
                     db_subsidies.c.zones_id,
                     db_subsidies.c.subsidies])
            .select_from(db_subsidies
                .join(db_models, db_subsidies.c.models_id == db_models.c.id)
                .join(db_zones, and_(db_subsidies.c.zones_id == db_zones.c.id,
                                     db_subsidies.c.models_id == db_zones.c.models_id)))
            .where(func.ST_Contains(db_zones.c.area, self.point_wkt))
            .where(db_models.c.name == self.model))

        records = [list(row) for row in db.engine.execute(s)]
        return records

    # supply
    #"V_IDX";"I_IDX";"NREST"
    #1.00;1.00;0.0000000000
    def _get_supply(self):
        '''Get supply records'''
        db_supply = db.supply
        db_models = db.models
        db_zones = db.zones

        s = (select([db_supply.c.types_id,
                     db_supply.c.zones_id,
                     db_supply.c.nrest])
            .select_from(db_supply
                .join(db_models, db_supply.c.models_id == db_models.c.id)
                .join(db_zones, and_(db_supply.c.zones_id == db_zones.c.id,
                                     db_supply.c.models_id == db_zones.c.models_id)))
            .where(func.ST_Contains(db_zones.c.area, self.point_wkt))
            .where(db_models.c.name == self.model))

        records = [list(row) for row in db.engine.execute(s)]
        return records
