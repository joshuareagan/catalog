#!/usr/bin/env python3

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
# import psycopg2

Base = declarative_base()

# This file is run to initialize the database for cities.py.
# It defines three tables: User, Country, and City


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)


class Country(Base):
    __tablename__ = 'countries'
    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


class City(Base):
    __tablename__ = 'cities'
    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False)
    population = Column(Integer)
    description = Column(String)
    country_id = Column(Integer, ForeignKey('countries.id'))
    country = relationship(Country)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'population': self.population,
            'description': self.description,
            'country_id': self.country_id
        }


engine = create_engine('postgresql://catalog:notagoodpassword@localhost:5432/cities')

Base.metadata.create_all(engine)
