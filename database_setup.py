from sqlalchemy import Column, ForeignKey, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from datetime import datetime

Base = declarative_base()


class User(Base):
  __tablename__ = 'user'
  
  id = Column(Integer, primary_key=True)
  name = Column(String(250), nullable=False)
  email = Column(String(600), nullable=False)
  photo = Column(String(600), nullable=False)

class Catagory(Base):
    __tablename__ = 'catagory'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    photo = Column(String(600), nullable=False)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id,
           'photo_url'    : self.photo,
       }
 
class Item(Base):
    __tablename__ = 'item'


    name =Column(String(250), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    created_at = Column(Date, default = datetime.now(),onupdate = datetime.now())
    catagory_id = Column(Integer,ForeignKey('catagory.id'))
    catagory = relationship(Catagory)
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'description'         : self.description,
           'id'         : self.id,
           'catagory_id' : self.catagory_id,
           'creator_id'   : self.user_id,
       }



engine = create_engine('sqlite:///itemscatalog.db')
 

Base.metadata.create_all(engine)
