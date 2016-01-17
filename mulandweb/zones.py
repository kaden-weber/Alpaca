# coding: utf-8

from collections import namedtuple
from sqlalchemy.orm import sessionmaker
from . import db

Zone = namedtuple('Zone', ['id', 'info'])

class Zones:
    '''Manages zone information'''
    def __init__(self, session=None):
        if session is None:
            Session = sessionmaker(bind=db.engine)
            session = Session()
        self.session = session

    def add(self, shape, info):
        '''Adds zone and information'''
        pass

    def get(self, points):
        '''Retrieve zone information for points'''
        pass

    def delete(self, id):
        '''Delete zone from id'''
        pass

    def update(self, id, info):
        '''Updates zone information'''
