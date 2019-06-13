# Udacity Item Catalog Project

## Project Description

This repo contains code written to fulfill the "Item Catalog" project in 
fulfillment of Udicity's Full Stack Developer Nanodegree program. The idea 
is to have a CRUD app that allows one to manage items relative to a set of 
categories. My implementation uses cities as the 'objects' and countries as 
their 'categories'.

Each city is in a country (naturally), and has a population and a description 
recorded.

## Dependencies

This app uses Python 3 and the following Python libraries:

1. Flask
1. SQLAlchemy
1. Bleach
1. oauth2client
1. httplib2
1. Requests

Make sure these are installed before running the program.

Because `cities.py` uses Google for third party authentication, one also needs 
a `client_secrets.json` file from Google in order to use their Oauth2 API. You 
can't have mine!

For information on how to get your own, see [Google's documentation 
here](https://developers.google.com/identity/protocols/OAuth2). Once you set up 
access to Google's API make sure to change the value of `client_id` to the 
value given to you by Google in the file `/templates/login.html`.

## Setup

You can install the program by cloning this repo from your command line:

```
$ git clone https://github.com/joshuareagan/catalog.git
```

A database is included in the repo with a with a few cities already recorded, 
`cities.db`. If you don't want to bother setting up your own database then you 
can skip the next step.

If you want to start with an empty database rather than use the one supplied, 
then delete `cities.db` and run `dbsetup.py` as follows:

```
$ python dbsetup.py
```

## Usage

Next, you can start the application by entering the following:

```
$ python cities.py
```

### Browser

Now it should be serving the app locally on port 8000. You can get to it by 
entering the following in your browser:

```
http://localhost:8000/
```

You won't be able to create, modify, or delete any records unless you sign in. 
You can sign in using your Google account. Just click the `Sign In` link and 
follow the instructions.

Once you're signed in, you won't be able to modify or delete records that you 
didn't create. But you will be able to create your own new records, and modify 
or delete those.

### JSON

You can do two sorts of JSON queries: (1) you can request data on all cities, 
broken down by country, and (2) you can request all data on a single city.

For the former, you can test it with `curl` from the command line:

```
$ curl -X GET "http://localhost:8000/countries/JSON"
```

If you just want information on a single city, make the same request on the URL 
`http://localhost:8000/city/XX/JSON`, but replace `XX` with the `city_id` number. 
For example, using `curl` again:

```
$ curl -X GET "http://localhost:8000/city/3/JSON"
{
  "id": 3, 
  "country_id": 1, 
  "description": "Dallas is a big city in northeastern Texas. It's really spread out!", 
  "name": "Dallas", 
  "population": 1345047
}
```

