from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from database_setup import Catagory, Base, Item, User

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


# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             photo='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Menu for UrbanBurger
college = Catagory(name="College",
                   photo="http://images.clipartpanda.com/college-clip-art-college-clip-art-5.png")

session.add(college)
session.commit()

books = Item(user_id=1, name="Books", description="Non-fiction books for the college.", 
             catagory=college)

session.add(books)
session.commit()


pens = Item(user_id=1, name="Pens", description="new pens for the college", 
                    catagory=college)

session.add(pens)
session.commit()

backpack = Item(user_id=1, name="backpack", description="A backpack to carry my books and laptop", 
                    catagory=college)

session.add(backpack)
session.commit()

laptop = Item(user_id=1, name="laptop", description="a laptop to use in the college", 
                   catagory=college)

session.add(laptop)
session.commit()


print "added all items!"
