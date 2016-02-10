from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from database_setup import Category, Base, Item, User

engine = create_engine('sqlite:///itemscatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()
photo_url = "https://www.lg.com/us/content/img/support/img-dummy-product.jpg"

# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             photo='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()


college = Category(name="College")

session.add(college)
session.commit()

books = Item( name="Books", description="Non-fiction books for the college.", 
             category=college, photo = photo_url)

session.add(books)
session.commit()


pens = Item(name="Pens", description="new pens for the college", 
                    category=college, photo = photo_url)

session.add(pens)
session.commit()

backpack = Item(name="backpack", description="A backpack to carry my books and laptop", 
                    category=college, photo = photo_url)

session.add(backpack)
session.commit()

laptop = Item(name="laptop", description="a laptop to use in the college", 
                   category=college, photo = photo_url)

session.add(laptop)
session.commit()


soccer = Category(name="Soccer")

session.add(soccer)
session.commit()

basketball = Category(name="Basketball")

session.add(basketball)
session.commit()

print "added all items!"
