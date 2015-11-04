from flask import Flask

import os
import sys
import nltk #make sure to do the formal download for this with the GUI 
#import nlp_script
import uuid
from flask import Flask, request, session, g, redirect, url_for, \
	 abort, render_template, flash
from contextlib import closing
from sqlite3 import dbapi2 as sqlite3
import datetime
from user import User
import time
import json

from flask.ext.login import *
import hashlib
import random 
import re

# configuration
DATABASE = '/tmp/flaskr.db'
DEBUG = True # leave disabled in production code
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

# manage user
login_manager = LoginManager()
login_manager.init_app(app)

def formatDate(d):
	monthDict={1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
	li = d.split('-')
	return '{0} {1}, {2}'.format(monthDict[int(li[1])], li[2], li[0])

def formatTime(t):
	li = t.split(':')
	meridiem = {0:'am', 1:'pm'}
	return  '{0}:{1} {2}'.format( int(li[0])%12,li[1],meridiem[int(li[0])/12])	

def formatTag(tags):
	return [tag.strip() for tag in tags.split('#')]

# connect to our db above
def connect_db():
	return sqlite3.connect(app.config['DATABASE'])


def init_db():
	with closing(connect_db()) as db:
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()


@app.before_request
def before_request():
	g.db = connect_db()
	g.db.executescript('PRAGMA foreign_keys=ON')


@app.teardown_request
def teardown_request(exception):
	db = getattr(g, 'db', None)
	if db is not None:
		db.close()


@login_manager.user_loader
def load_user(userid):
	cur = g.db.execute('select type from Person where username = (?)', [userid])
	person = [dict(type=row[0]) for row in cur.fetchall()]
	if len(person) == 0:
		return None
	else:
		return User(userid, person[0]['type'])

import flaskr.views.parseQuestions

import flaskr.views.student_views
import flaskr.views.professor_views
import flaskr.views.timeline_views
import flaskr.views.auth_views
import flaskr.views.subscribe_actions

if __name__ == '__main__':
	app.run()
