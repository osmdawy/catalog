from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
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

class Category(Base):
    __tablename__ = 'category'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id,
       }
 
class Item(Base):
    __tablename__ = 'item'


    name =Column(String(250), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    photo = Column(String(600), nullable=False)
    created_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    category_id = Column(Integer,ForeignKey('category.id'))
    category = relationship(Category)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'description'         : self.description,
           'id'         : self.id,
           'category_id' : self.category_id,
           'photo_url'  : photo,
       }



engine = create_engine('sqlite:///itemscatalog.db')
 

Base.metadata.create_all(engine)
