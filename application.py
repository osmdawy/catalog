from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Catagory, Base, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

# CLIENT_ID = json.loads(
#     open('client_secrets.json', 'r').read())['web']['client_id']
# APPLICATION_NAME = "Catalog Application"

# Connect to Database and create database session
engine = create_engine('sqlite:///itemscatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token


# Show all catagories
@app.route('/')
@app.route('/catagories/')
def showCatagories():
  catagories = session.query(Catagory).order_by(asc(Catagory.name))
  latest_items = session.query(Item).order_by(Item.created_at).limit(6)
  # if 'username' not in login_session:
  #     return render_template('publicrestaurants.html', restaurants=restaurants)
  # else:
  return render_template('index.html', catagories=catagories,items= latest_items, display_catagory = False)

#show items for specific catagory
@app.route('/catagory/<int:catagory_id>/items')
def showItems(catagory_id):
	catagory = session.query(Catagory).get(catagory_id)
	items = session.query(Item).params(catagory_id = catagory_id).order_by(asc(Item.name))
	return render_template('index.html', catagories= catagory,items= items, display_catagory = True)

@app.route('/items/<int:item_id>')
def showItem(item_id):
	item = session.query(Item).get(item_id)
	return render_template('item.html', item = item)
# Create a new restaurant


# @app.route('/restaurant/new/', methods=['GET', 'POST'])
# def newRestaurant():
#     if 'username' not in login_session:
#         return redirect('/login')
#     if request.method == 'POST':
#         newRestaurant = Restaurant(
#             name=request.form['name'], user_id=login_session['user_id'])
#         session.add(newRestaurant)
#         flash('New Restaurant %s Successfully Created' % newRestaurant.name)
#         session.commit()
#         return redirect(url_for('showRestaurants'))
#     else:
#         return render_template('newRestaurant.html')

# # Edit a restaurant


# @app.route('/restaurant/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
# def editRestaurant(restaurant_id):
#     editedRestaurant = session.query(
#         Restaurant).filter_by(id=restaurant_id).one()
#     if 'username' not in login_session:
#         return redirect('/login')
#     if editedRestaurant.user_id != login_session['user_id']:
#         return "<script>function myFunction() {alert('You are not authorized to edit this restaurant. Please create your own restaurant in order to edit.');}</script><body onload='myFunction()''>"
#     if request.method == 'POST':
#         if request.form['name']:
#             editedRestaurant.name = request.form['name']
#             flash('Restaurant Successfully Edited %s' % editedRestaurant.name)
#             return redirect(url_for('showRestaurants'))
#     else:
#         return render_template('editRestaurant.html', restaurant=editedRestaurant)


# # Delete a restaurant
# @app.route('/restaurant/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
# def deleteRestaurant(restaurant_id):
#     restaurantToDelete = session.query(
#         Restaurant).filter_by(id=restaurant_id).one()
#     if 'username' not in login_session:
#         return redirect('/login')
#     if restaurantToDelete.user_id != login_session['user_id']:
#         return "<script>function myFunction() {alert('You are not authorized to delete this restaurant. Please create your own restaurant in order to delete.');}</script><body onload='myFunction()''>"
#     if request.method == 'POST':
#         session.delete(restaurantToDelete)
#         flash('%s Successfully Deleted' % restaurantToDelete.name)
#         session.commit()
#         return redirect(url_for('showRestaurants', restaurant_id=restaurant_id))
#     else:
#         return render_template('deleteRestaurant.html', restaurant=restaurantToDelete)

# # Show a restaurant menu


# @app.route('/restaurant/<int:restaurant_id>/')
# @app.route('/restaurant/<int:restaurant_id>/menu/')
# def showMenu(restaurant_id):
#     restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
#     creator = getUserInfo(restaurant.user_id)
#     items = session.query(MenuItem).filter_by(
#         restaurant_id=restaurant_id).all()
#     if 'username' not in login_session or creator.id != login_session['user_id']:
#         return render_template('publicmenu.html', items=items, restaurant=restaurant, creator=creator)
#     else:
#         return render_template('menu.html', items=items, restaurant=restaurant, creator=creator)


# # Create a new menu item
# @app.route('/restaurant/<int:restaurant_id>/menu/new/', methods=['GET', 'POST'])
# def newMenuItem(restaurant_id):
#     if 'username' not in login_session:
#         return redirect('/login')
#     restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
#     if login_session['user_id'] != restaurant.user_id:
#         return "<script>function myFunction() {alert('You are not authorized to add menu items to this restaurant. Please create your own restaurant in order to add items.');}</script><body onload='myFunction()''>"
#         if request.method == 'POST':
#             newItem = MenuItem(name=request.form['name'], description=request.form['description'], price=request.form[
#                                'price'], course=request.form['course'], restaurant_id=restaurant_id, user_id=restaurant.user_id)
#             session.add(newItem)
#             session.commit()
#             flash('New Menu %s Item Successfully Created' % (newItem.name))
#             return redirect(url_for('showMenu', restaurant_id=restaurant_id))
#     else:
#         return render_template('newmenuitem.html', restaurant_id=restaurant_id)

# # Edit a menu item


# @app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET', 'POST'])
# def editMenuItem(restaurant_id, menu_id):
#     if 'username' not in login_session:
#         return redirect('/login')
#     editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
#     restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
#     if login_session['user_id'] != restaurant.user_id:
#         return "<script>function myFunction() {alert('You are not authorized to edit menu items to this restaurant. Please create your own restaurant in order to edit items.');}</script><body onload='myFunction()''>"
#     if request.method == 'POST':
#         if request.form['name']:
#             editedItem.name = request.form['name']
#         if request.form['description']:
#             editedItem.description = request.form['description']
#         if request.form['price']:
#             editedItem.price = request.form['price']
#         if request.form['course']:
#             editedItem.course = request.form['course']
#         session.add(editedItem)
#         session.commit()
#         flash('Menu Item Successfully Edited')
#         return redirect(url_for('showMenu', restaurant_id=restaurant_id))
#     else:
#         return render_template('editmenuitem.html', restaurant_id=restaurant_id, menu_id=menu_id, item=editedItem)


# # Delete a menu item
# @app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
# def deleteMenuItem(restaurant_id, menu_id):
#     if 'username' not in login_session:
#         return redirect('/login')
#     restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
#     itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
#     if login_session['user_id'] != restaurant.user_id:
#         return "<script>function myFunction() {alert('You are not authorized to delete menu items to this restaurant. Please create your own restaurant in order to delete items.');}</script><body onload='myFunction()''>"
#     if request.method == 'POST':
#         session.delete(itemToDelete)
#         session.commit()
#         flash('Menu Item Successfully Deleted')
#         return redirect(url_for('showMenu', restaurant_id=restaurant_id))
#     else:
#         return render_template('deleteMenuItem.html', item=itemToDelete)


# # Disconnect based on provider
# @app.route('/disconnect')
# def disconnect():
#     if 'provider' in login_session:
#         if login_session['provider'] == 'google':
#             gdisconnect()
#             del login_session['gplus_id']
#             del login_session['credentials']
#         if login_session['provider'] == 'facebook':
#             fbdisconnect()
#             del login_session['facebook_id']
#         del login_session['username']
#         del login_session['email']
#         del login_session['picture']
#         del login_session['user_id']
#         del login_session['provider']
#         flash("You have successfully been logged out.")
#         return redirect(url_for('showRestaurants'))
#     else:
#         flash("You were not logged in")
#         return redirect(url_for('showRestaurants'))


if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
app.run(host='0.0.0.0', port=8000)