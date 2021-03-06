from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
# dor preventing CSRF attack
from flask.ext.seasurf import SeaSurf
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from database_setup import Category, Base, Item, User
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
# for images uploading
from sqlalchemy_imageattach.stores.fs import HttpExposedFileSystemStore
from sqlalchemy_imageattach.context import store_context
from urllib import urlopen
# for xml
from dicttoxml import dicttoxml
import os
import sys

app = Flask(__name__)
csrf = SeaSurf(app)

# Connect to Database and create database session
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
engine = create_engine('postgresql://catalog:catalog@localhost/itemscatalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# session = DBSession()
Session = scoped_session(DBSession)
session = Session()
# for images uploading
fs_store = HttpExposedFileSystemStore('/tmp/itemimages', 'images/')
app.wsgi_app = fs_store.wsgi_middleware(app.wsgi_app)
dummy_item_photo = '''http://www.canadacontestsonline.com
                      /wp-content/themes/Wordie/images/no_image.png'''

CLIENT_ID = json.loads(
    open(os.path.join(BASE_DIR, 'client_secrets.json'), 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog"

# Create anti-forgery state token


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

# For connecting to G+ and create new user I used a code
# from udacity authentication and authorization course

# Connect using G+


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
        oauth_flow = flow_from_clientsecrets(os.path.join(BASE_DIR, 'client_secrets.json'), scope='')
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
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
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
    output += ''' " style = "width: 300px; height: 300px;border-radius:
                    150px;-webkit-border-radius: 150px;
                    -moz-border-radius: 150px;"> '''
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
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s' %
           login_session['access_token'])
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
        return render_template('logout.html', response=response)
    else:
        response = 'Failed to revoke token for given user.'
        return render_template('logout.html', response=response)

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


# Show all categories
@app.route('/')
@app.route('/categories/')
def showCategories():
   # print >>sys.stderr, '=============show'
    users = session.query(User).order_by(asc(User.email))
   # print >>sys.stderr, '======================   ', str(users.all()) 
    categories = session.query(Category).order_by(asc(Category.name))
   # print >>sys.stderr, '=============show     ', str(categories.all())
    latest_items = session.query(Item).order_by(Item.created_at.desc()).limit(6)
    return render_template('index.html', categories=categories,items=latest_items, display_category='',login_session=login_session)

# show items for specific category


@app.route('/category/<int:category_id>/items')
def showItems(category_id):
    categories = session.query(Category).order_by(asc(Category.name))
    category_name = session.query(Category).get(category_id).name
    items = session.query(Item).filter_by(
        category_id=category_id).order_by(asc(Item.name))
    return render_template('index.html', categories=categories, items=items,
                           display_category=category_name,
                           login_session=login_session)

# show one item data


@app.route('/items/<int:item_id>')
def showItem(item_id):
    item = session.query(Item).get(item_id)
    with store_context(fs_store):
        picture_url = item.picture.locate()
    user_id = getUserID(login_session['email'])
    return render_template('item.html', item=item, login_session=login_session,
                           picture_url=picture_url, user_id=user_id)


# Create a new item
@app.route('/items/create/', methods=['GET', 'POST'])
def createItem():
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        category = session.query(Category).filter_by(
            name=request.form['item-category']).first()
        newItem = Item()
        newItem.name = request.form['item-name']
        newItem.description = request.form['description']
        newItem.category = category
        newItem.user_id = getUserID(login_session['email'])
        try:
            with store_context(fs_store):
                if request.files['item_photo']:
                    newItem.picture.from_file(request.files['item_photo'])
                else:
                    newItem.picture.from_file(urlopen(dummy_item_photo))
                session.add(newItem)
                session.commit()
        except Exception:
            session.rollback()
            raise
        return redirect(url_for('showCategories'))
    else:
        categories = session.query(Category).order_by(asc(Category.name))
        return render_template('create_item.html', categories=categories,
                               login_session=login_session)

# Edit an exisiting item


@app.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    item = session.query(Item).get(item_id)
    user_id = getUserID(login_session['email'])
    if item.user_id != user_id:
        response = make_response(
            json.dumps('You are not authorized to edit this item.'), 200)
        return response
    if request.method == 'POST':
        if request.form['item-name']:
            item.name = request.form['item-name']
        if request.form['description']:
            item.description = request.form['description']
        if request.files['item_photo']:
            try:
                with store_context(fs_store):
                    item.picture.from_file(request.files['item_photo'])
                    session.commit()
            except Exception:
                session.rollback()
                raise
        return redirect(url_for('showCategories'))
    else:
        categories = session.query(Category).order_by(asc(Category.name))
        return render_template('edititem.html', categories=categories,
                               item=item, login_session=login_session)

# delete an existing item


@app.route('/items/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(item_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    deletedItem = session.query(Item).get(item_id)
    user_id = getUserID(login_session['email'])
    if deletedItem.user_id != user_id:
        response = make_response(
            json.dumps('You are not authorized to delete this item.'), 200)
        return response
    if request.method == 'POST':
        with store_context(fs_store):
            session.delete(deletedItem)
            session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template("deleteItem.html",
                               item=deletedItem, login_session=login_session)

# helper methods for json and xml end points


def convertCategoriesToDict():
    categories = session.query(Category).order_by(asc(Category.name))
    categoriesDict = [i.serialize for i in categories]
    return categoriesDict


def convertItemsToDict(category_id):
    items = session.query(Item).filter_by(
        category_id=category_id).order_by(asc(Item.name))
    itemsDict = [i.serialize for i in items]
    return itemsDict


# JSON end points

@app.route('/categories/JSON')
def showCategoriesJSON():
    return jsonify(Categories=convertCategoriesToDict())


@app.route('/category/<int:category_id>/items/JSON')
def showItemsJSON(category_id):
    return jsonify(Items=convertItemsToDict(category_id))


@app.route('/items/<int:item_id>/JSON')
def showItemJSON(item_id):
    item = session.query(Item).get(item_id)
    return jsonify(Item=item.serialize)


@app.route('/users/JSON')
def showUsersJSON():
    users = session.query(User).order_by(User.name)
    return jsonify(Users=[i.serialize for i in users])


# XML end points
@app.route('/categories/XML')
def showCategoriesXML():
    categoriesXML = dicttoxml(convertCategoriesToDict())
    return app.response_class(categoriesXML, mimetype='application/xml')


@app.route('/category/<int:category_id>/items/XML')
def showItemsXML(category_id):
    itemsXML = dicttoxml(convertItemsToDict(category_id))
    return app.response_class(itemsXML, mimetype='application/xml')


@app.route('/items/<int:item_id>/XML')
def showItemXML(item_id):
    item = session.query(Item).get(item_id)
    itemXML = dicttoxml(item.serialize)
    return app.response_class(itemXML, mimetype='application/xml')

app.secret_key = 'super_secret_key'
if __name__ == '__main__':
   # app.debug = True
    app.secret_key = 'super_secret_key'
    app.run()
