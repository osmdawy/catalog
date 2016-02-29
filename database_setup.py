from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from datetime import datetime
# for image uploading
from sqlalchemy import Unicode
from sqlalchemy_imageattach.entity import Image, image_attachment
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(600), nullable=False)
    photo = Column(String(600), nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'email': self.email
        }


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class Item(Base):
    __tablename__ = 'item'

    name = Column(String(250), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    picture = image_attachment('ItemPicture')
    created_at = Column(
        DateTime, default=datetime.now(), onupdate=datetime.now())
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'category_id': self.category_id,
            'created_at': self.created_at,
            'creator_id': self.user_id,
        }


class ItemPicture(Base, Image):

    """Item picture model."""

    item_id = Column(Integer, ForeignKey('item.id'), primary_key=True)
    item = relationship('Item')

    __tablename__ = 'item_picture'

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'object_type': self.object_type,
            'object_id': self.object_id,
        }

engine = create_engine('postgresql://catalog:catalog@localhost/itemscatalog')


Base.metadata.create_all(engine)
