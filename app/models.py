from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import declarative_base
from database import Base

# Таблица связи многие-ко-многим
organization_activity  = Table(
    'organization_activity',
    Base.metadata,
    Column('organization_id', Integer, ForeignKey('organizations.id'), primary_key=True),
    Column('activity_id', Integer, ForeignKey('activities.id'), primary_key=True)
)


class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey('activities.id'))

    children = relationship("Activity", backref=backref('parent', remote_side=[id]))
    organizations = relationship(
        "Organization",
        secondary=organization_activity,
        back_populates="activities"
    )


class Building(Base):
    __tablename__ = 'buildings'
    id = Column(Integer, primary_key=True)
    address = Column(String(500), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    organizations = relationship("Organization", back_populates="building")


class Phone(Base):
    __tablename__ = 'phones'
    id = Column(Integer, primary_key=True)
    number = Column(String(50), nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'))

    organization = relationship("Organization", back_populates="phones")


class Organization(Base):
    __tablename__ = 'organizations'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    building_id = Column(Integer, ForeignKey('buildings.id'))

    phones = relationship("Phone", back_populates="organization", cascade="all, delete-orphan")
    building = relationship("Building", back_populates="organizations")
    activities = relationship(
        "Activity",
        secondary=organization_activity,
        back_populates="organizations"
    )