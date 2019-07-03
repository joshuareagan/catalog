# Udacity Serv Config Project

## Project Description

This repo contains code written to fulfill the "Linux Server Configuration" 
project in fulfillment of Udicity's Full Stack Developer Nanodegree program. 
The server is set up to serve the CRUD app we made in the last project.

## Website and Server Details

For hosting, I used a Digital Ocean droplet hosted at ip address 104.248.4.1. 
The URL to reach this app and run it correctly is 
[http://reagandev.com](http://reagandev.com).

The server used is `apache2`, so I first installed that. Then, to use a Flask 
app with `apache2`, I downloaded and installed `mod_wsgi` for python 3. Then I 
enabled `mod_wsgi` as follows:

```
$ sudo apt-get install apache2
$ sudo apt-get install libapache2-mod-wsgi-py3
$ sudo a2enmod wsgi
```

Next I created a directory for my flask app at `/var/www/catalog`, and put my 
app there. Then I created a virtual environment for my app's dependencies, 
using `virtualenv`. From the `/var/www/catalog` directory, I ran:

```
$ sudo pip install virtualenv
$ sudo virtualenv venv
$ source venv/bin/activate
```

With `venv` as the virtual environment, I installed all the Python 3 
dependencies needed for the app.

## Dependencies

The CRUD app uses Python 3 and the following Python libraries:

1. Flask
1. SQLAlchemy
1. Bleach
1. oauth2client
1. httplib2
1. Requests
1. psycopg2

Naturally all of these must be installed before running the app.

Because `cities.py` uses Google for third party authentication, one also needs 
a `client_secrets.json` file from Google in order to use their Oauth2 API. You 
can't have mine!

For information on how to get your own, see [Google's documentation 
here](https://developers.google.com/identity/protocols/OAuth2). Once you set up 
access to Google's API make sure to change the value of `client_id` to the 
value given to you by Google in the file `/templates/login.html`.

## Database Setup

The app uses a postgresql database, so I installed that. Then I created a 
postgre user, `catalog`, and a database, `cities`. My catalog CRUD app accesses `cities` using the user `catalog`.

## Server Settings

In order to set up a virtual host, I created and adjusted the settings of the 
config file `/etc/apache2/sites-available/catalog.conf`. Then I enabled the 
virtual host:

```
$ sudo a2ensite catalog
```

Then I needed to restart the server to put those settings into effect:

```
sudo service apache2 restart
```

Root login to the server has been disabled, and `git` was also installed.

## Usage

To get started using the app, go to [http://reagandev.com](http://reagandev.com) 
and login using your Google credentials. Have fun!

## Resources used

I followed the instructions from 
[this page](https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps) 
to get my server up and running.
