from flask import Flask

import os
import sys
import nltk #make sure to do the formal download for this with the GUI 
#import nlp_script
import uuid
from flask import Flask, request, session, g, redirect, url_for, \
	 abort, render_template, flash, Response, current_app
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

from gevent import monkey
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin, BroadcastMixin
from threading import Thread

import logging
logging.basicConfig()

try:
	from flask import _app_ctx_stack as stack
except ImportError:
	from flask import _request_ctx_stack as stack

monkey.patch_all()

# configuration
PORT = 5000
DATABASE = '/tmp/flaskr.db'
DEBUG = True # leave disabled in production code
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create our little application :)
app = Flask(__name__)
app.debug = True
app.config.from_object(__name__)

# manage user
login_manager = LoginManager()
login_manager.init_app(app)

from views import parseQuestions

class QuestionsNamespace(BaseNamespace, RoomsMixin, BroadcastMixin):

	def initialize(self):
		self.room = ''
		self.logger = app.logger
		self.log("Socketio session started")
		self.thread = Thread(target=self.thread_func)
		self.thread.setDaemon(True)

	def log(self, message):
		self.logger.info("[{0}] {1}".format(self.socket.sessid, message))

	def thread_func(self):
		self.on_best_questions(self.room)
		self.on_all_questions(self.room)

	def on_join(self, room):
		self.room = room.strip()
		self.join(room)
		self.on_best_questions(room)
		return True

	def on_update(self, room):
		if not self.thread.is_alive():
			self.thread = Thread(target=self.thread_func)
			self.thread.setDaemon(True)
			self.thread.start()

	def on_all_questions(self, class_name):
		with app.app_context():
			global current_app
			global sqlite3

			db = sqlite3.connect(current_app.config['DATABASE'])

			cur = db.execute('select question_text, question_date, question_time,question_confusion, question_tag from Question where question_id IN (select question_id from Asked_in where class_name= (?) )  order by question_date desc, question_time desc', [class_name])
			questions = [dict(text=row[0], date=formatDate(row[1]), time=formatTime(row[2]), confusion=row[3], tags=formatTag(row[4])) for row in cur.fetchall()]
			self.emit('all_to_prof', json.dumps(questions), self.room)

			return True

	def on_best_questions(self, class_name):
		with app.app_context():
			global current_app
			global sqlite3

			db = sqlite3.connect(current_app.config['DATABASE'])

			question_query = db.execute('select question_text from Question where question_id IN (select question_id from Asked_in where class_name= (?) )  order by question_date desc, question_time desc', [class_name])
			# select last 10 questions
			question_list = [str(row[0]) for row in question_query][:10]
			# choose top 3 most relevant questions
			top_questions = parseQuestions.relevantQuestions(question_list, 3)
			self.emit('best_to_prof', json.dumps(top_questions), self.room)
			return True


def formatDate(d):
	monthDict={1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
	li = d.split('-')
	return '{0} {1}, {2}'.format(monthDict[int(li[1])], li[2], li[0])

def formatTime(t):
	li = t.split(':')
	meridiem = {0:'am', 1:'pm'}
	return  '{0}:{1} {2}'.format( int(li[0])%12,li[1],meridiem[int(li[0])/12])	

def formatTag(tags):
	return [tag.strip() for tag in tags.split('#') if len(tag) > 0]

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

@app.route('/socket.io/<path:remaining>')
def socketio(remaining):
	try:
		socketio_manage(request.environ, {'/questions': QuestionsNamespace}, request)
	except:
		app.logger.error("Exception while handling socketio connection", exc_info=True)
	return Response()

import flaskr.views.student_views
import flaskr.views.professor_views
import flaskr.views.timeline_views
import flaskr.views.auth_views
import flaskr.views.subscribe_actions

if __name__ == '__main__':
	 app.run() 
