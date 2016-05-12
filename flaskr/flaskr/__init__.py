from flask import Flask

import os
import sys
import nltk #make sure to do the formal download for this with the GUI 
#import nlp_script
import uuid
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, Response, current_app, jsonify

from flask_sockets import Sockets
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
import redis
import gevent

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

REDIS_URL = os.environ['REDIS_URL']
REDIS_CHAN = 'chat'

# create our little application :)
app = Flask(__name__)
app.debug = True
app.config.from_object(__name__)

sockets = Sockets(app)
redis = redis.from_url(REDIS_URL)

# manage user
login_manager = LoginManager()
login_manager.init_app(app)

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

from views import parseQuestions

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


class ChatBackend(object):
    """Interface for registering and updating WebSocket clients."""

    def __init__(self):
        self.clients = list()
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(REDIS_CHAN)

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get('data')
            if message['type'] == 'message':
                # app.logger.info(u'Sending message: {}'.format(data))
                yield data

    def register(self, client):
        """Register a WebSocket connection for Redis updates."""
        self.clients.append(client)

    def send(self, client, data):
        """Send given data to the registered client.
        Automatically discards invalid connections."""
        try:
            client.send(data)
        except Exception:
            self.clients.remove(client)

    def run(self):
        """Listens for new messages in Redis, and sends them to clients."""
        for data in self.__iter_data():
            for client in self.clients:
                gevent.spawn(self.send, client, data)

    def start(self):
        """Maintains Redis subscription in the background."""
        gevent.spawn(self.run)

chats = ChatBackend()
chats.start()

import flaskr.views.student_views
import flaskr.views.professor_views
import flaskr.views.timeline_views
import flaskr.views.auth_views
import flaskr.views.subscribe_actions


# this is new add question
@sockets.route('/submit')
def inbox(ws):
    """Receives incoming chat messages, inserts them into Redis."""
    while not ws.closed:
        # Sleep to prevent *constant* context-switches.
        gevent.sleep(0.1)
        message = ws.receive()
        print message

        if message:
            # app.logger.info(u'Inserting message: {}'.format(message))
            redis.publish(REDIS_CHAN, message)


@sockets.route('/receive')
def outbox(ws):
    """Sends outgoing chat messages, via `ChatBackend`."""
    chats.register(ws)

    while not ws.closed:
        # Context switch while `ChatBackend.start` is running in the background.
        gevent.sleep(0.1)

