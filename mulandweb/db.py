# coding: utf-8

from sqlalchemy import create_engine, Table, Column, MetaData
from sqlalchemy import Integer, String, Float, ARRAY, ForeignKey
from geoalchemy2 import Geometry
import config

engine = create_engine(config.db_url)
meta = MetaData()

models = Table('models', meta,
    Column('id', Integer, Sequence('models_id_seq'), primary_key=True),
    Column('name', String),
)

real_estate_types = Table('real_estate_types', meta,
    Column('id', Integer, primary_key=True),
    Column('description', String),
)

markets = Table('markets', meta,
    Column('id', Integer, primary_key=True),
    Column('description', String),
)

rent_adjustments = Table('rent_adjustments', meta,
    Column('types_id', None, ForeignKey('real_estate_types.id'), primary_key=True),
    Column('zones_id', None, ForeignKey('zones.id'), primary_key=True),
    Column('models_id', None, ForeignKey('models.id'), primary_key=True),
    Column('adjustment', Float),
)

supply = Table('supply', meta,
    Column('types_id', None, ForeignKey('real_estate_types.id'), primary_key=True),
    Column('zones_id', None, ForeignKey('zones.id'), primary_key=True),
    Column('models_id', None, ForeignKey('models.id'), primary_key=True),
    Column('nrest', Float),
)

real_estates_zones = Table('real_estates_zones', meta,
    Column('types_id', None, ForeignKey('real_estate_types.id'), primary_key=True),
    Column('zones_id', None, ForeignKey('zones.id'), primary_key=True),
    Column('markets_id', None, ForeignKey('markets.id'), primary_key=True),
    Column('models_id', None, ForeignKey('models.id'), primary_key=True),
    Column('header', ARRAY(String, zero_indexes=True)),
    Column('data', ARRAY(Float, zero_indexes=True)),
)

agents = Table('agents', meta,
    Column('id', Integer, primary_key=True),
    Column('models_id', None, ForeignKey('models.id'), primary_key=True),
    Column('markets_id', None, ForeignKey('markets.id')),
    Column('aggra_id', Integer),
    Column('header', ARRAY(String, zero_indexes=True)),
    Column('data', ARRAY(Float, zero_indexes=True)),
)

zones = Table('zones', meta,
    Column('id', Integer, primary_key=True),
    Column('models_id', None, ForeignKey('models.id'), primary_key=True),
    Column('area', Geometry('POLYGON', srid=900913, spatial_index=True)),
    Column('header', ARRAY(String, zero_indexes=True)),
    Column('data', ARRAY(Float, zero_indexes=True)),
)

demand = Table('demand', meta,
    Column('id', Integer, primary_key=True),
    Column('models_id', None, ForeignKey('models.id'), primary_key=True),
    Column('demand', Float),
)

subsidies = Table('subsidies', meta,
    Column('demand_id', None, ForeignKey('demand.id'), primary_key=True),
    Column('types_id', None, ForeignKey('real_estate_types.id'), primary_key=True),
    Column('zones_id', None, ForeignKey('zones.id'), primary_key=True),
    Column('models_id', None, ForeignKey('models.id'), primary_key=True),
    Column('subsidies', Float),
)

demand_exogenous_cutoff = Table('demand_exogenous_cutoff', meta,
    Column('demand_id', None, ForeignKey('demand.id'), primary_key=True),
    Column('types_id', None, ForeignKey('real_estate_types.id'), primary_key=True),
    Column('zones_id', None, ForeignKey('zones.id'), primary_key=True),
    Column('models_id', None, ForeignKey('models.id'), primary_key=True),
    Column('dcutoff', Float),
)

agents_zones = Table('agents_zones', meta,
    Column('demand_id', None, ForeignKey('demand.id'), primary_key=True),
    Column('zones_id', None, ForeignKey('zones.id'), primary_key=True),
    Column('models_id', None, ForeignKey('models.id'), primary_key=True),
    Column('acc', Float),
    Column('att', Float),
    Column('header', ARRAY(String, zero_indexes=True)),
    Column('data', ARRAY(Float, zero_indexes=True)),
)

meta.create_all(engine)
