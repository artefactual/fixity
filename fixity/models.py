import os

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

db_path = os.path.join(os.path.dirname(__file__), "fixity.db")
engine = create_engine(f"sqlite:///{db_path}", echo=False)

Session = sessionmaker(bind=engine)
Base = declarative_base()


class AIP(Base):
    __tablename__ = "aips"
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False)


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    aip_id = Column(Integer, ForeignKey("aips.id"))
    begun = Column(DateTime)
    ended = Column(DateTime)
    success = Column(Boolean)
    posted = Column(Boolean)
    report = Column(String(1000))

    aip = relationship("AIP", backref=backref("reports", order_by=id))


Base.metadata.create_all(engine)
