from sqlalchemy import create_engine
from sqlalchemy import Column, ForeignKey, Boolean, DateTime, Integer, String
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///fixity/fixity.db', echo=True)

Session = sessionmaker(bind=engine)
Base = declarative_base()


class AIP(Base):
    __tablename__ = 'aips'
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False)


class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    aip_id = Column(Integer, ForeignKey('aips.id'))
    begun = Column(DateTime)
    ended = Column(DateTime)
    success = Column(Boolean)
    posted = Column(Boolean)
    report = Column(String(1000))

    aip = relationship("AIP", backref=backref('reports', order_by=id))

Base.metadata.create_all(engine)
