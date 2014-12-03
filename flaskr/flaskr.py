import os
import sys
#import nltk #make sure to do the formal download for this with the GUI 
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
import parseQuestions 

from flask.ext.login import *


# configuration
#DATABASE = os.path.join(app.root_path, 'flaskr.db')
DATABASE = '/tmp/flaskr.db'
DEBUG = True # leave disabled in production code
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'


# create our little application :)
login_manager = LoginManager()
app = Flask(__name__)
app.config.from_object(__name__)
login_manager.init_app(app)


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


def formatDate(d):
	monthDict={1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
	li = d.split('-')
	return '{0} {1}, {2}'.format(monthDict[int(li[1])], li[2], li[0])

def formatTime2(t):
	li = t.split(':')
	meridiem = {0:'am', 1:'pm'}
	return  '{0}:{1} {2}'.format( int(li[0])%12,li[1],meridiem[int(li[0])/12])	

def formatTime(t):
	return t
	#li = t.split(':')
	#meridiem = {0:'am', 1:'pm'}
	#return  '{0}:{1} {2}'.format( int(li[0])%12,li[1],meridiem[int(li[0])/12])	

def formatTag(tags):
	return [tag.strip() for tag in tags.split('#')]



##############################Professor Code########################################
@app.route('/')
def home():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return render_template('index.html')
	else:
		if current_user.isStudent:
			return redirect(url_for('student'))
		else:
			return redirect(url_for('professor'))

@app.route('/signup')
def signup():
	return render_template('signup.html')

@app.route('/add_user', methods=['POST'])
def add_user():
	type = request.form['type'].lower().strip()
	if type == 'student': type = 0
	else: type = 1

	username = request.form['username']
	password = request.form['password']
	email = request.form['email']

	try:
		cur = g.db.execute('insert into Person(type, username, password, email) values (?,?,?,?)', [type, username, password, email])
		g.db.commit()
		flash('Account created - you may login')
		return redirect(url_for('login'))
	except:
		flash('Error: Username already exists - select new username')
		return redirect(url_for('home'))

@app.route('/logout')
def logout():
	from flask.ext.login import logout_user
	logout_user()
	return redirect(url_for('home'))

@app.route('/login')
def login():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return render_template('login.html')
	else:
		if current_user.isStudent:
			return redirect(url_for('student'))
		else:
			return redirect(url_for('professor'))


@app.route('/submit_login', methods=['POST'])
def submit_login():
	username = request.form['username']
	password = request.form['password']
	cur = g.db.execute('select type from Person where username = (?) and password = (?)', [username, password])
	person = [dict(type=row[0]) for row in cur.fetchall()]
	if len(person) == 0:
		flash('Incorrect username or password')
		return redirect(url_for('home'))
	user = User(username, person[0]['type'])
	from flask.ext.login import login_user
	login_user(user)
	if person[0]['type'] == 0:
		return redirect(url_for('student'))
	else:
		return redirect(url_for('professor'))

@app.route('/professor')
def professor():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	
	if current_user.isStudent: return redirect(url_for('student'))
	username = current_user.username
	cur = g.db.execute('select * from Class, Subscribes where Class.class_name = Subscribes.class_name AND Subscribes.username="'+username+'"')
	prof_class = [dict(class_name=row[0], class_key=row[1], class_admin=row[2]) for row in cur.fetchall()]
	return render_template('professor.html', classes=prof_class)


@app.route('/professor_class/<username>/<class_name1>')
def professor_class(username, class_name1):
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	
	if current_user.isStudent: return redirect(url_for('student'))
	#cur_time_in_minutes = 
	question_query_result = g.db.execute('select question_text from Question where question_id IN (select question_id from Asked_in where class_name="'+class_name1+'")  order by question_date desc, question_time desc')
	question_list = []
	for row in question_query_result: 
		question_list.append(str(row[0]))
	print question_list
	nlp_script_question_results = parseQuestions.relevantQuestions(question_list, 3)

	cur = g.db.execute('select question_text, question_date, question_time,question_confusion, question_tag from Question where question_id IN (select question_id from Asked_in where class_name="'+class_name1+'")  order by question_date desc, question_time desc')
	questions = [dict(text=row[0], date=formatDate(row[1]), time=formatTime2(row[2]), confusion=row[3], tags=formatTag(row[4])) for row in cur.fetchall()]
	prof_username = current_user.username
	return render_template('class.html', questions=questions, class_name=class_name1, username = prof_username, nlp_result = nlp_script_question_results)

@app.route('/professor_class/<username1>/<class_name1>/timeline/')
def timeline_main_page(username1, class_name1):
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	if current_user.isStudent: return redirect(url_for('student'))
	prof_username = current_user.username
	dates_temp= g.db.execute('select question_date from Question where (question_id IN (select question_id from Asked_in where class_name="'+class_name1+'")) order by question_date desc')
	dates = []
	for row in dates_temp.fetchall():
		if(row[0] not in dates):
			dates.append(row[0])

	return render_template('timeline_main_page.html', username = prof_username, class_name = class_name1, date_list = dates)

@app.route('/professor_class/<username>/<class_name1>/timeline/<question_date1>')
def timeline(username, class_name1, question_date1):
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	if current_user.isStudent: return redirect(url_for('student'))

	cur = g.db.execute('select question_text, question_time, question_date, question_confusion from Question where question_date = (?) AND (question_id IN (select question_id from Asked_in where class_name="'+class_name1+'"))', [question_date1])
	cur_yellow = g.db.execute('select question_text, question_time,question_date, question_confusion from Question where question_date = (?) AND question_confusion = 1 AND (question_id IN (select question_id from Asked_in where class_name="'+class_name1+'"))', [question_date1])
	cur_orange = g.db.execute('select question_text, question_time, question_date,question_confusion from Question where question_date = (?) AND question_confusion = 2 AND (question_id IN (select question_id from Asked_in where class_name="'+class_name1+'"))', [question_date1])
	cur_red = g.db.execute('select question_text, question_time, question_date, question_confusion from Question where question_date = (?) AND question_confusion = 3 AND (question_id IN (select question_id from Asked_in where class_name="'+class_name1+'"))', [question_date1])
	time_list = []
	for row in cur: 
		time_list.append(parse_time(row[1], row[2]))
	min_time = 0
	exist_questions1  = " "
	if(len(time_list)>0): 
		min_time = min(time_list)
	else: 
		exist_questions1 = "No Questions Were Asked"
	
	questions_yellow = [dict(label=str(row[0]),x=parse_time(row[1], row[2])-min_time, y=row[3]*3, z=20) for row in cur_yellow.fetchall()]
	#questions_yellow = [dict(x=2, y=1, z=30, label=row[0] for row in cur_yellow.fetchall()]

	#questions_orange = [dict(x=1, y=2, z=30, label=row[0] for row in cur_orange.fetchall()]
	questions_orange = [dict(label=str(row[0]),x=parse_time(row[1], row[2])-min_time, y=row[3]*3, z=20) for row in cur_orange.fetchall()]

	#questions_red = [dict(x=0, y=3, z=30, label=row[0] for row in cur_red.fetchall()]
	questions_red = [dict(label=str(row[0]),x=parse_time(row[1], row[2])-min_time, y=row[3]*3, z=20) for row in cur_red.fetchall()]
	
	prof_username = username

	return render_template('timeline.html', questions_y=questions_yellow, questions_o = questions_orange, questions_r = questions_red, class_name=class_name1, prof_username = prof_username, date = question_date1, exist_questions = exist_questions1)

def parse_time(t, d): 
	new_time = datetime.datetime.strptime(t, '%H:%M:%S.%f')
	new_date = datetime.datetime.strptime(d, '%Y-%m-%d')
	month_temp = new_date.month 
	day_temp = new_date.day
	year_temp = new_date.year 
	hour_temp = new_time.hour
	min_temp = new_time.minute
	dt2 = datetime.datetime(year_temp, month_temp, day_temp, hour_temp, min_temp)
	time_seconds = time.mktime(dt2.timetuple())+1e-6*new_time.microsecond
	time_minutes = time_seconds/60
	return time_minutes 

@app.route('/add_class', methods=['POST'])
def add_class():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	
	if current_user.isStudent: return redirect(url_for('student'))
	username = current_user.username
	class_name = request.form['class_name']
	class_key = request.form['class_key']
	class_admins = request.form['class_admins']
	if len(class_name) == 0:
		flash('No class name received. Class not added')
		return redirect(url_for('professor'))
	if len(class_key) == 0:
		flash('No class key received. Class not added')
		return redirect(url_for('professor'))
	if len(class_admins) == 0:
		flash('No admins received. Class not added')
		return redirect(url_for('professor'))
	for admin in class_admins.split(','):
		person = g.db.execute('select username from Person where username="' + admin.strip() + '"').fetchall()
		if len(person) == 0:
			return json.dumps({'status':'incorrect', 'flash':'One of the admins does not exist. Class not added.'})
	try:
		g.db.execute('insert into Class (class_name, class_key, class_admin) values (?, ?, ?)', [class_name, class_key, class_admins])
		g.db.execute('insert into Subscribes (username, class_name) values (?, ?)', [username, class_name])
		g.db.commit()
		return json.dumps({'status':'OK', 'flash':'New class added', 'class_name':class_name, 'class_key':class_key, 'class_admin':class_admins, 'username':username})
	except:
		return json.dumps({'status':'exists', 'flash':'This class already exists'})


@app.route('/delete_class', methods=['POST'])
def delete_class():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	
	if current_user.isStudent: return redirect(url_for('student'))
	class_name = request.form['class_name']
	cur = g.db.execute('Select class_admin from Class where class_name="' + class_name + '"')
	class_admins = cur.fetchall()[0][0]
	admins = [admin.strip() for admin in class_admins.split(',')]
	if current_user.username not in admins:
		return json.dumps({'status':'OK', 'flash':'You must be an admin to delete this class'})
	g.db.execute('Delete from Class where class_name = (?)', [class_name])
	g.db.execute('Delete from Subscribes where class_name = (?)', [class_name])
	g.db.commit()
	return json.dumps({'status':'deleted', 'flash':'Class deleted'})


@app.route('/subscribe', methods=['POST'])
def subscribe():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	
	#if current_user.isStudent: return redirect(url_for('student'))
	class_name = request.form['class_name']
	class_key = request.form['class_key']
	username = current_user.username
	if len(class_name) == 0:
		return json.dumps({'status':'no_class', 'flash':'No class name received and not subscribed'})
	if len(class_key) == 0:
		return json.dumps({'status':'no_key', 'flash':'No class key received and not subscribed'})
	cur = g.db.execute('select * from Class where class_name ="' + class_name + '"')
	classes = cur.fetchall()
	if len(classes) == 0:
		return json.dumps({'status':'not_exist', 'flash':'This class does not exist'})
	if class_key != classes[0][1]:
		return json.dumps({'status':'wrong_key', 'flash':'The key entered is not correct'})
	try:
		g.db.execute('insert into Subscribes (username, class_name) values (?, ?)',[username, class_name])
		g.db.commit()
		cur = g.db.execute('Select class_admin from Class where class_name="' + class_name + '"')
		class_admin = cur.fetchall()[0][0]
		return json.dumps({'status':'OK', 'flash':'Subcribed to class', 'class_name':class_name, 'class_key':class_key, 'class_admin':class_admin, 'username': username})
	except:
		return json.dumps({'status':'already_subscribed', 'flash':'You are already subscribed to this class'})


@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))

	#if current_user.isStudent: return redirect(url_for('student'))
	class_name = request.form['class_name']
	username = current_user.username
	#cur = g.db.execute('select * from Class where class_name ="' + class_name + '"')
	#if len(cur.fetchall()) == 0:
	#	flash('This class does not exist')
	#	return redirect(url_for('professor'))
	g.db.execute('Delete from Subscribes where Subscribes.username="' + username + '" AND Subscribes.class_name="' + class_name + '"')
	g.db.commit()
	#flash('Unsubscribed from class')
	#return redirect(url_for('professor'))
	return json.dumps({'status':'OK', 'flash':'Unsubscribed from class'})

@app.route('/update_key', methods=['POST'])
def update_key():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	
	if current_user.isStudent: return redirect(url_for('student'))
	newkey = request.form['newkey']
	oldkey = request.form['oldkey']
	if len(newkey) == 0:
		return json.dumps({'status':'OK', 'class_key':oldkey, 'flash':'No key received'})
	class_name = request.form['class_name']
	print class_name
	cur = g.db.execute('Select class_admin from Class where class_name="' + class_name + '"')
	class_admins = cur.fetchall()[0][0]
	admins = [admin.strip() for admin in class_admins.split(',')]
	if current_user.username not in admins:
		return json.dumps({'status':'OK', 'class_key':oldkey, 'flash':'You must be an admin to change the key'})
	g.db.execute('Update Class Set class_key="' + newkey + '" where class_name="' + class_name + '"')
	g.db.commit()
	return json.dumps({'status':'OK', 'class_key':newkey, 'flash':'Key updated'})

@app.route('/update_admin', methods=['POST'])
def update_admin():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	
	if current_user.isStudent: return redirect(url_for('student'))
	newadmins = request.form['newadmins']
	class_name = request.form['class_name']
	oldadmins = request.form['oldadmin']
	if len(newadmins) == 0:
		return json.dumps({'status':'OK', 'admin':oldadmins, 'flash':'No admins received'})
	old_admins = [admin.strip() for admin in oldadmins.split(',')]
	if current_user.username not in old_admins:
		return json.dumps({'status':'OK', 'admin':oldadmins, 'flash':'You must be an admin to change the admins'})
	for admin in newadmins.split(','):
		person = g.db.execute('select username from Person where username="' + admin.strip() + '"').fetchall()
		if len(person) == 0:
			return json.dumps({'status':'OK', 'admin':oldadmins, 'flash':'One of the admins does not exist'})
	g.db.execute('Update Class Set class_admin="' + newadmins + '" where class_name="' + class_name + '"')	
	g.db.commit()
	return json.dumps({'status':'OK', 'admin':newadmins, 'flash':'Admins updated'})

##############################Student Code#####################################	
	
@app.route('/student')
def student():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	if current_user.isProfessor: return redirect(url_for('professor'))
	cur = g.db.execute('select Class.class_name from Class, Subscribes where Subscribes.class_name=Class.class_name AND Subscribes.username="' + current_user.username + '"')
	classes = [dict(class_name=row[0]) for row in cur.fetchall()]
	print classes
	return render_template('student.html', classes=classes)

@app.route('/student_class/<username>/<class_name1>')
def student_class(username, class_name1):
	print class_name1
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	if current_user.isProfessor: return redirect(url_for('professor'))
	username = current_user.username
	cur = g.db.execute('select question_text, question_date, question_time, question_confusion, question_tag from Question where Question.question_id IN (select question_id from Asked_in where Asked_in.class_name="'+ class_name1 +'") order by question_date desc, question_time desc')
	questions = [dict(text=row[0], date=formatDate(row[1]), time=formatTime2(row[2]), confusion=row[3], tags=formatTag(row[4])) for row in cur.fetchall()]
	return render_template('questions.html', questions=questions, class_name = class_name1)


@app.route('/add_question', methods=['POST'])
def add_question():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	if current_user.isProfessor: return redirect(url_for('professor'))
	txt = request.form['question']
	class_name1 = request.form['class_name']
	confusion = request.form['confusion']
	username = current_user.username
	tag = request.form['tag']
	if len(txt) == 0:
		return json.dumps({'status':'no_question', 'flash': 'No question received'})
	dt = datetime.datetime.now()
	date = str(dt.date())
	time = str(dt.time())
	g.db.execute('insert into Question (question_text, question_date, question_time, question_confusion, question_tag) values (?, ?, ?, ?, ?)', [txt, date, time, confusion, tag])
	cur = g.db.execute('select question_id from Question order by question_id desc limit 1')
	qid = cur.fetchall()[0][0]
	g.db.execute('insert into Asks (question_id, username) values(?,?)',[qid, username])
	g.db.commit()
	try:
		g.db.execute('insert into Asked_in (question_id, class_name) values (?, ?)',[qid, class_name1])	
		g.db.commit()
		tags = " ".join(formatTag(tag))
		return json.dumps({'status':'OK', 'flash':'New question added to class', 'text':txt, 'date':formatDate(date), 'time':formatTime2(time), 'confusion':confusion, 'tag':formatTag(tags)})
	except:
		return json.dumps({'status':'no_class', 'flash':'Class does not exist. Question not added.'})


if __name__ == '__main__':
	app.run()
