from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Catagory, Base, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.client import AccessTokenCredentials
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///itemscatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog"

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

    # DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: ' 
    print login_session['username']
    if access_token is None:
      print 'Access Token is None'
      response = make_response(json.dumps('Current user not connected.'), 401)
      response.headers['Content-Type'] = 'application/json'
      return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
      del login_session['access_token'] 
      del login_session['gplus_id']
      del login_session['username']
      del login_session['email']
      del login_session['picture']
      response = 'Successfully disconnected.'
      return render_template('logout.html', response= response)
    else:
      response = 'Failed to revoke token for given user.'
      return render_template('logout.html', response= response)

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], photo=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Show all catagories
@app.route('/')
@app.route('/catagories/')
def showCatagories():
  users = session.query(User).order_by(asc(User.email))
  catagories = session.query(Catagory).order_by(asc(Catagory.name))
  
  latest_items = session.query(Item).order_by(Item.created_at.desc()).limit(6)
  # if 'username' not in login_session:
  #     return render_template('publicrestaurants.html', restaurants=restaurants)
  # else:
  return render_template('index.html', catagories=catagories,items= latest_items, display_catagory = '',
    login_session = login_session)

#show items for specific catagory
@app.route('/catagory/<int:catagory_id>/items')
def showItems(catagory_id):
  catagories = session.query(Catagory).order_by(asc(Catagory.name))
  catagory_name = session.query(Catagory).get(catagory_id).name
  items = session.query(Item).filter_by(catagory_id = catagory_id).order_by(asc(Item.name))
  return render_template('index.html', catagories= catagories,items= items, display_catagory = catagory_name,
    login_session = login_session)

@app.route('/items/<int:item_id>')
def showItem(item_id):
	item = session.query(Item).get(item_id)
	return render_template('item.html', item = item, login_session = login_session)


# Create a new item
@app.route('/items/create/', methods=['GET', 'POST'])
def createItem():
  if 'username' not in login_session:
    return redirect(url_for('showLogin'))
  if request.method == 'POST':
    catagory = session.query(Catagory).filter_by(name = request.form['item-catagory']).first()
    newItem = Item(name = request.form['item-name'],description = request.form['description'], catagory = catagory)
    session.add(newItem)
    session.commit()
    return redirect(url_for('showCatagories'))
  else:
    catagories = session.query(Catagory).order_by(asc(Catagory.name))
    return render_template('create_item.html',catagories = catagories, login_session = login_session)

# Edit an exisiting item
@app.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id):
  if 'username' not in login_session:
    return redirect(url_for('showLogin'))
  item = session.query(Item).get(item_id)
  if request.method == 'POST':
    if request.form['item-name']:
      item.name = request.form['item-name']
    if request.form['description']:
      item.description = request.form['description']
    return redirect(url_for('showCatagories'))
  else:
    catagories = session.query(Catagory).order_by(asc(Catagory.name))
    return render_template('edititem.html',catagories = catagories, item = item, login_session = login_session)

# delete an existing item
@app.route('/items/<int:item_id>/delete', methods= ['GET','POST'])
def deleteItem(item_id):
  if 'username' not in login_session:
    return redirect(url_for('showLogin'))
  deletedItem = session.query(Item).get(item_id)
  if request.method == 'POST':
    session.delete(deletedItem)
    session.commit()
    return redirect(url_for('showCatagories'))
  else:
    return render_template("deleteItem.html",item = deletedItem, login_session = login_session)


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