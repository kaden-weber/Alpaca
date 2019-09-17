# coding: utf-8
# pylint: disable=bad-continuation,invalid-name
'''Specifies database tables and provides function to create them'''

from sqlalchemy import create_engine, Table, Column, MetaData
from sqlalchemy import Integer, String, Float, ForeignKey, Sequence
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from geoalchemy2 import Geometry
from . import config
from sqlalchemy.orm import sessionmaker


engine = create_engine(config.db_url)
meta = MetaData()
Session = sessionmaker(bind=engine)
session = Session()

models = Table(config.db_prefix + 'models', meta,
    Column('id', Integer, Sequence(config.db_prefix + 'models_id_seq'), primary_key=True),
    Column('name', String, index=True, nullable=False, unique=True),
    Column('zones_header', ARRAY(String, zero_indexes=True), nullable=False),
    Column('agents_header', ARRAY(String, zero_indexes=True), nullable=False),
    Column('agents_zones_header', ARRAY(String, zero_indexes=True), nullable=False),
    Column('real_estates_zones_header', ARRAY(String, zero_indexes=True), nullable=False),
)

zones = Table(config.db_prefix + 'zones', meta,
    Column('id', Integer, primary_key=True),
    Column('models_id', Integer, ForeignKey(models.c.id), primary_key=True),
    Column('area', Geometry(srid=900913, spatial_index=True), nullable=False),
    Column('data', ARRAY(Float, zero_indexes=True), nullable=False),
)

rent_adjustments = Table(config.db_prefix + 'rent_adjustments', meta,
    Column('types_id', Integer, primary_key=True),
    Column('zones_id', Integer, primary_key=True),
    Column('models_id', Integer, ForeignKey(models.c.id), primary_key=True),
    Column('adjustment', Float, nullable=False),
    ForeignKeyConstraint(['zones_id', 'models_id'],
                         [zones.c.id, zones.c.models_id]),
)

supply = Table(config.db_prefix + 'supply', meta,
    Column('types_id', Integer, primary_key=True),
    Column('zones_id', Integer, primary_key=True),
    Column('models_id', Integer, ForeignKey(models.c.id), primary_key=True),
    Column('nrest', Float, nullable=False),
    ForeignKeyConstraint(['zones_id', 'models_id'],
                         [zones.c.id, zones.c.models_id]),
)

real_estates_zones = Table(config.db_prefix + 'real_estates_zones', meta,
    Column('types_id', Integer, primary_key=True),
    Column('zones_id', Integer, primary_key=True),
    Column('markets_id', Integer, primary_key=True),
    Column('models_id', Integer, ForeignKey(models.c.id), primary_key=True),
    Column('data', ARRAY(Float, zero_indexes=True), nullable=False),
    ForeignKeyConstraint(['zones_id', 'models_id'],
                         [zones.c.id, zones.c.models_id]),
)

agents = Table(config.db_prefix + 'agents', meta,
    Column('id', Integer, primary_key=True),
    Column('models_id', Integer, ForeignKey(models.c.id), primary_key=True),
    Column('markets_id', Integer, nullable=False),
    Column('aggra_id', Integer, nullable=False),
    Column('upperbb', Float, nullable=False),
    Column('data', ARRAY(Float, zero_indexes=True), nullable=False),
)

demand = Table(config.db_prefix + 'demand', meta,
    Column('agents_id', Integer, primary_key=True),
    Column('models_id', Integer, ForeignKey(models.c.id), primary_key=True),
    Column('demand', Float, nullable=False),
    ForeignKeyConstraint(['agents_id', 'models_id'],
                         [agents.c.id, agents.c.models_id]),
)

subsidies = Table(config.db_prefix + 'subsidies', meta,
    Column('agents_id', Integer, primary_key=True),
    Column('types_id', Integer, primary_key=True),
    Column('zones_id', Integer, primary_key=True),
    Column('models_id', Integer, ForeignKey(models.c.id), primary_key=True),
    Column('subsidies', Float, nullable=False),
    ForeignKeyConstraint(['zones_id', 'models_id'],
                         [zones.c.id, zones.c.models_id]),
    ForeignKeyConstraint(['agents_id', 'models_id'],
                         [agents.c.id, agents.c.models_id]),
)

demand_exogenous_cutoff = Table(config.db_prefix + 'demand_exogenous_cutoff', meta,
    Column('agents_id', Integer, primary_key=True),
    Column('types_id', Integer, primary_key=True),
    Column('zones_id', Integer, primary_key=True),
    Column('models_id', Integer, ForeignKey(models.c.id), primary_key=True),
    Column('dcutoff', Float, nullable=False),
    ForeignKeyConstraint(['zones_id', 'models_id'],
                         [zones.c.id, zones.c.models_id]),
    ForeignKeyConstraint(['agents_id', 'models_id'],
                         [agents.c.id, agents.c.models_id]),
)

agents_zones = Table(config.db_prefix + 'agents_zones', meta,
    Column('agents_id', Integer, primary_key=True),
    Column('zones_id', Integer, primary_key=True),
    Column('models_id', Integer, ForeignKey(models.c.id), primary_key=True),
    Column('acc', Float, nullable=False),
    Column('att', Float, nullable=False),
    Column('data', ARRAY(Float, zero_indexes=True)),
    ForeignKeyConstraint(['zones_id', 'models_id'],
                         [zones.c.id, zones.c.models_id]),
    ForeignKeyConstraint(['agents_id', 'models_id'],
                         [agents.c.id, agents.c.models_id]),
)

bids_adjustments = Table(config.db_prefix + 'bids_adjustments', meta,
    Column('agents_id', Integer, primary_key=True),
    Column('types_id', Integer, primary_key=True),
    Column('zones_id', Integer, primary_key=True),
    Column('models_id', Integer, ForeignKey(models.c.id), primary_key=True),
    Column('bidadj', Float, nullable=False),
    ForeignKeyConstraint(['zones_id', 'models_id'],
                         [zones.c.id, zones.c.models_id]),
    ForeignKeyConstraint(['agents_id', 'models_id'],
                         [agents.c.id, agents.c.models_id]),
)

bids_functions = Table(config.db_prefix + 'bids_functions', meta,
    Column('id', Integer, primary_key=True),
    Column('models_id', Integer, ForeignKey(models.c.id), primary_key=True),
    Column('markets_id', Integer, nullable=False),
    Column('aggra_id', Integer, nullable=False),
    Column('idattrib', Float, nullable=False),
    Column('lineapar', Float, nullable=False),
    Column('cagent_x', Float, nullable=False),
    Column('crest_x', Float, nullable=False),
    Column('cacc_x', Float, nullable=False),
    Column('czones_x', Float, nullable=False),
    Column('exppar_x', Float, nullable=False),
    Column('cagent_y', Float, nullable=False),
    Column('crest_y', Float, nullable=False),
    Column('cacc_y', Float, nullable=False),
    Column('czones_y', Float, nullable=False),
    Column('exppar_y', Float, nullable=False),
)

rent_functions = Table(config.db_prefix + 'rent_functions', meta,
    Column('id', Integer, primary_key=True),
    Column('models_id', Integer, ForeignKey(models.c.id), primary_key=True),
    Column('markets_id', Integer, nullable=False),
    Column('idattrib', Float, nullable=False),
    Column('scalepar', Float, nullable=False),
    Column('lineapar', Float, nullable=False),
    Column('crest_x', Float, nullable=False),
    Column('czones_x', Float, nullable=False),
    Column('exppar_x', Float, nullable=False),
    Column('crest_y', Float, nullable=False),
    Column('czones_y', Float, nullable=False),
    Column('exppar_y', Float, nullable=False),
)

def create_tables():
    '''Create tables at the database'''
    meta.create_all(engine)

def delM(session,tablename,modelCol,model_id):
    # create query of  elements to delete
    toDelete = session.query(tablename).filter(modelCol == model_id)
    toDelete.delete(synchronize_session=False)  #Delete the elements
    session.commit()   # Commit the changes 

def delete_tables(name):
    model_id = session.query(models).filter_by(name=name).first()  # Search Model
    if model_id: 
        # If model is present
        model_id=model_id[0]   # Get models ID

        tabs=[rent_functions,bids_functions,bids_adjustments,agents_zones,demand_exogenous_cutoff,
                        subsidies,demand,agents,real_estates_zones,supply,rent_adjustments,zones] # List of all tables to update 
        for k,t in enumerate(tabs):
            delM(session,t,t.c.models_id,model_id) # Delete records from tables
            print ("Deleting Tables: ",str(round((k+1)*100/float(len(tabs)+1),2))+"%",end="\r")
        delM(session,models,models.c.id,model_id)  # Delete from models table
        print ("Delete Complete"," "*50)
    else:
        print ("Model Not Found") # If model is not present
