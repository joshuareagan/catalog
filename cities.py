#!/usr/bin/env python3

from flask import Flask, render_template, url_for, request
from flask import redirect, jsonify, flash
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from dbsetup import Base, Country, City, User

# Scrub all text inputs.
from bleach import clean

# Libs for generating tokens.
import random
import string

# Provide third party OAuth support.
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
from flask import make_response
from flask import session as login_session

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('/var/www/catalog/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog of Cities Application"

engine = create_engine('postgresql://catalog:notagoodpassword@localhost:5432/cities')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# session = DBSession()


# Anti-forgery state token created for each new session.
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# When Google sign in is successful put data in login_session.
@app.route('/gconnect', methods=['POST'])
def gconnect():

    # Validate state token
    if request.args.get('state') != login_session['state']:
        flash("401 error: invalid state parameter.")
        return redirect(url_for('countriesMain'))

    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/catalog/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        flash("401 error: failed to upgrade the authorization code.")
        return redirect(url_for('countriesMain'))

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        flash("500 error: %s" % result.get('error'))
        return redirect(url_for('countriesMain'))

    # Verify that the access token is used for the intended user.
    g_id = credentials.id_token['sub']
    if result['user_id'] != g_id:
        flash("401 error: token's user ID doesn't match given user ID.")
        return redirect(url_for('countriesMain'))

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        flash("401 error: token's client ID doesn't match app's.")
        return redirect(url_for('countriesMain'))

    stored_access_token = login_session.get('access_token')
    stored_g_id = login_session.get('g_id')
    if stored_access_token is not None and g_id == stored_g_id:
        flash("200: Current user is already connected.")
        return redirect(url_for('countriesMain'))

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['g_id'] = g_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if a user exists, if not make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    flash("Successfully logged in as %s" % login_session['username'])
    return "Logged in as %s." % login_session['username']


def createUser(login_session):
    session = DBSession()
    newUser = User(username=login_session['username'],
                   email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    session.close()
    return user.id


def getUserInfo(user_id):
    session = DBSession()
    user = session.query(User).filter_by(id=user_id).one()
    session.close()
    return user


def getUserID(email):
    try:
        session = DBSession()
        user = session.query(User).filter_by(email=email).one()
        session.close()
        return user.id
    except NoResultFound:
        return None


@app.route('/logout')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        flash("401 error: current user not connected.")
        return redirect(url_for('countriesMain'))

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    del login_session['access_token']
    del login_session['g_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']

    if result['status'] == '200':
        # Reset the user's sesson.
        flash("Successfully signed out.")
        return redirect(url_for('countriesMain'))
    else:
        # For whatever reason, the given token was invalid.
        # Possibly an old Google cookie
        flash("400 error: failed to revoke token for given user.")
        return redirect(url_for('countriesMain'))


def getCountry(x):
    try:
        session = DBSession()
        country = session.query(Country).filter_by(id=x).one()
        session.close()
        return country
    except NoResultFound:
        return None


def getCity(x):
    try:
        session = DBSession()
        city = session.query(City).filter_by(id=x).one()
        session.close()
        return city
    except NoResultFound:
        return None


# Turn a string with commas into an integer, if possible.
def intify(x):
    comma_free = x.replace(',', '')
    try:
        return int(comma_free)
    except ValueError:
        return None


def loggedIn():
    return login_session.get('user_id')


# Show all countries and a list of 10 most populous cities.
@app.route('/')
@app.route('/countries')
def countriesMain():
    session = DBSession()
    countries = session.query(Country)
    cities = session.query(City).order_by(desc('population')).limit(10)
    session.close()
    return render_template('countries.html', countries=countries,
                           cities=cities, format=format, loggedIn=loggedIn())


# API endpoint for a dump of all city data, by country.
@app.route('/countries/JSON')
def countriesJSON():
    session = DBSession()
    countries = session.query(Country)
    result = {}
    for country in countries:
        result[country.id] = {
            'name': country.name,
            'cities': {}
        }
        cities = session.query(City).filter_by(country_id=country.id)
        for city in cities:
            result[country.id]['cities'][city.id] = {
                'name': city.name,
                'population': city.population,
                'description': city.description
            }
    session.close()
    return jsonify(result)


# Show the cities of one given country.
@app.route('/country/<int:country_id>/')
def countryOne(country_id):
    country = getCountry(country_id)
    session = DBSession()
    cities = session.query(City).filter_by(
            country_id=country_id).order_by(desc('population'))
    session.close()
    return render_template('country.html', country=country,
                           cities=cities, format=format, loggedIn=loggedIn())


# Show all data on a given city.
@app.route('/city/<int:city_id>')
def cityOne(city_id):
    city = getCity(city_id)
    country = getCountry(city.country_id)
    return render_template('city.html', country=country, city=city,
                           format=format, loggedIn=loggedIn())


# API endpoint for all data on a single given city.
@app.route('/city/<int:city_id>/JSON')
def cityOneJSON(city_id):
    city = getCity(city_id)
    return jsonify(city.serialize)


# Create a new country.
@app.route('/newCountry', methods=['GET', 'POST'])
def newCountry():
    if request.method == 'POST':
        if not loggedIn():
            flash("You must be logged in to add a country record.")
        elif request.form['name']:
            session = DBSession()
            clean_name = clean(request.form['name'])
            country = Country(name=clean_name,
                              user_id=loggedIn())
            session.add(country)
            session.commit()
            flash("%s successfully added as a country." % country.name)
            session.close()
        else:
            flash("Cannot add country without name.")
        return redirect(url_for('countriesMain'))
    return render_template('newCountry.html', loggedIn=loggedIn())


# Create a new city.
@app.route('/newCity/<int:country_id>/', methods=['GET', 'POST'])
def newCity(country_id):
    country = getCountry(country_id)
    if request.method == 'POST':
        pop_int = intify(request.form['pop'])
        if not loggedIn():
            flash("You must log in to add a city record.")
        elif (request.form['name'] and request.form['pop'] and
              request.form['desc'] and pop_int):
                session = DBSession()
                clean_name = clean(request.form['name'])
                clean_desc = clean(request.form['desc'])
                city = City(name=clean_name,
                            population=pop_int,
                            description=clean_desc,
                            country_id=country.id,
                            user_id=loggedIn())
                session.add(city)
                session.commit()
                city_name = city.name
                city_id = city.id
                session.close()
                flash("%s successfully added as a city." % city_name)
                return redirect(url_for('cityOne', city_id=city_id))
        else:
            if not pop_int:
                flash("Population must be a number.")
            else:
                flash("One or more field(s) are empty.")
            return redirect(url_for('newCity', country_id=country_id))
        return redirect(url_for('countryOne', country_id=country_id))
    return render_template('newCity.html', country=country,
                           loggedIn=loggedIn())


# Edit an existing country name.
@app.route('/editCountry/<int:country_id>/', methods=['GET', 'POST'])
def editCountry(country_id):
    country = getCountry(country_id)
    if request.method == 'POST':
        if loggedIn() != country.user_id:
            flash("You are not authorized to modify the record for %s."
                  % country.name)
        elif request.form['name']:
            session = DBSession()
            country.name = clean(request.form['name'])
            session.add(country)
            session.commit()
            session.close()
        else:
            flash("Country must have a name.")
        return redirect(url_for('countriesMain'))
    return render_template('editCountry.html', country=country,
                           loggedIn=loggedIn())


# Edit data for an existing city.
@app.route('/editCity/<int:city_id>/', methods=['GET', 'POST'])
def editCity(city_id):
    city = getCity(city_id)
    country = getCountry(city.country_id)
    if request.method == 'POST':
        pop_int = intify(request.form['pop'])
        if loggedIn() != city.user_id:
            flash("You are not authorized to modify the record for %s."
                  % city.name)
        elif (request.form['name'] and request.form['pop'] and
              request.form['desc'] and pop_int):
                session = DBSession()
                city.name = clean(request.form['name'])
                city.population = pop_int
                city.description = clean(request.form['desc'])
                session.add(city)
                session.commit()
                session.close()
                return redirect(url_for('cityOne', city_id=city_id))
        else:
            if not pop_int:
                flash("Population must be a number.")
            else:
                flash("One or more field(s) are empty.")
            redirect(url_for('editCity', city_id=city_id))
        return redirect(url_for('countryOne', country_id=country_id))
    return render_template('editCity.html', country=country, city=city,
                           loggedIn=loggedIn())


# Delete a country and all its cities.
@app.route('/deleteCountry/<int:country_id>/', methods=['GET', 'POST'])
def deleteCountry(country_id):
    country = getCountry(country_id)
    if request.method == 'POST':
        if loggedIn() != country.user_id:
            flash("You are not authorized to delete %s." % country.name)
        elif country:
            session = DBSession()
            cities = session.query(City).filter_by(
                country_id=country_id).all()
            for city in cities:
                session.delete(city)
            session.delete(country)
            session.commit()
            session.close()
        return redirect(url_for('countriesMain'))
    return render_template('deleteCountry.html', country=country,
                           loggedIn=loggedIn())


# Delete a city.
@app.route('/deleteCity/<int:city_id>/', methods=['GET', 'POST'])
def deleteCity(city_id):
    city = getCity(city_id)
    country = getCountry(city.country_id)
    if request.method == 'POST':
        if loggedIn() != city.user_id:
            flash("You are not authorized to delete %s." % city.name)
        elif city:
            session = DBSession()
            session.delete(city)
            session.commit()
            session.close()
        return redirect(url_for('countryOne', country_id=country.id))
    return render_template('deleteCity.html', country=country, city=city,
                           loggedIn=loggedIn())


if __name__ == '__main__':
    app.secret_key = "This key is not all that secure"
    # app.debug = True
    app.run()
