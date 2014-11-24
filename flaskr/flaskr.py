# all the imports
import os
import uuid
from flask import Flask, request, session, g, redirect, url_for, \
	 abort, render_template, flash
from contextlib import closing
from sqlite3 import dbapi2 as sqlite3
import datetime


# configuration
#DATABASE = os.path.join(app.root_path, 'flaskr.db')
DATABASE = '/tmp/flaskr.db'
DEBUG = True # leave disabled in production code
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'


# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)


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

def formatDate(d):
	monthDict={1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
	li = d.split('-')
	return '{0} {1}, {2}'.format(monthDict[int(li[1])], li[2], li[0])

def formatTime(t):
	li = t.split(':')
	meridiem = {0:'am', 1:'pm'}
	return  '{0}:{1} {2}'.format( int(li[0])%12,li[1],meridiem[int(li[0])/12])	



##############################Professor Code########################################
@app.route('/temp')
def temp():
	return render_template('temp.html')

@app.route('/add_temp', methods=['POST'])
def add_temp():
	username = request.form['username']
	password = request.form['password']
	student_prof = request.form['student_prof']
	cur = g.db.execute('insert into Person(type, username, password) values (?,?,?)', [student_prof, username, password])
	g.db.commit()
	flash('Person added')
	return redirect(url_for('temp'))

@app.route('/professor')
def professor():
	username = 'prof1' #change later and pass through from login
	cur = g.db.execute('select Class.class_name, Class.class_key from Class, Subscribes where Class.class_name = Subscribes.class_name AND Subscribes.username="'+username+'"')
	prof_class = [dict(class_name=row[0], class_key=row[1]) for row in cur.fetchall()]
	prof_username = username
	return render_template('professor.html', classes=prof_class, prof_username = prof_username)


@app.route('/professor_class/<username>/<class_name1>')
def professor_class(username, class_name1):
	cur = g.db.execute('select question_text, question_date, question_time,question_confusion from Question where question_id IN (select question_id from Asked_in where class_name="'+class_name1+'")  order by question_date desc, question_time desc')
	questions = [dict(text=row[0], date=row[1], time=row[2], confusion=row[3]) for row in cur.fetchall()]
	prof_username = username
	return render_template('class.html', questions=questions, class_name=class_name1, prof_username = username)


@app.route('/add_class', methods=['POST'])
def add_class():
	username = request.form['username']
	class_name = request.form['class_name']
	class_key = request.form['class_key']
	if len(class_name) == 0:
		flash('No class name received and not added')
		return redirect(url_for('professor'))
	if len(class_key) == 0:
		flash('No class key received and not added')
		return redirect(url_for('professor'))
	try:
		g.db.execute('insert into Class (class_name, class_key) values (?, ?)', [class_name, class_key])
		g.db.execute('insert into Subscribes (username, class_name) values (?, ?)', [username, class_name])
		g.db.commit()
		flash('New class added')
	except:
		flash('This class already exists')
	return redirect(url_for('professor'))


@app.route('/delete_class', methods=['POST'])
def delete_class():
	username = request.form['username']	
	print username
	class_name = request.form['class_name']
	print class_name
	if len(class_name) == 0:
		flash('No class name received and not deleted')
		return redirect(url_for('professor'))
	g.db.execute('Delete from Class where class_name = (?)', [class_name])
	g.db.execute('Delete from Subscribes where class_name = (?)', [class_name])
	g.db.commit()
	flash('Class deleted')
	return redirect(url_for('professor'))

@app.route('/subscribe', methods=['POST'])
def subscribe():
	class_name = request.form['class_name']
	class_key = request.form['class_key']
	username = request.form['username']
	if len(class_name) == 0:
		flash('No class name received and not subscribed')
		return redirect(url_for('professor'))
	if len(class_key) == 0:
		flash('No class key received and not subscribed')
		return redirect(url_for('professor'))
	cur = g.db.execute('select * from Class where class_name ="' + class_name + '"')
	classes = cur.fetchall()
	if len(classes) == 0:
		print 'reached'
		flash('This class does not exist')
		return redirect(url_for('professor'))
	if class_key != classes[0][1]:
		flash('The key entered is not correct')
		return redirect(url_for('professor'))
	g.db.execute('insert into Subscribes (username, class_name) values (?, ?)',[username, class_name])
	g.db.commit()
	flash('Subcribed to class')
	return redirect(url_for('professor'))

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
	class_name = request.form['class_name']
	username = request.form['username']
	cur = g.db.execute('select * from Class where class_name ="' + class_name + '"')
	if len(cur.fetchall()) == 0:
		flash('This class does not exist')
		return redirect(url_for('professor'))
	g.db.execute('Delete from Subscribes where Subscribes.username="' + username + '" AND Subscribes.class_name="' + class_name + '"')
	g.db.commit()
	flash('Unsubscribed from class')
	return redirect(url_for('professor'))

##############################Student Code#####################################	
	
@app.route('/student')
def student():
	username = 'hxkoh2'
	cur = g.db.execute('select question_text, question_date, question_time, question_confusion from Question where Question.question_id IN (select question_id from Asked_in) order by question_date desc, question_time desc')
	questions = [dict(text=row[0], date=formatDate(row[1]), time=formatTime(row[2]), confusion=row[3]) for row in cur.fetchall()]
	return render_template('student.html', questions=questions)


@app.route('/add_question', methods=['POST'])
def add_question():
	txt = request.form['question']
	class_name1 = request.form['class_name']
	confusion = request.form['confusion']
	username = request.form['username']
	if len(txt) == 0:
		flash('Empty question received and not inserted into db')
		return redirect(url_for('student'))
	dt = datetime.datetime.now()
	date = str(dt.date())
	time = str(dt.time())
	g.db.execute('insert into Question (question_text, question_date, question_time, question_confusion) values (?, ?, ?,?)', [txt, date, time,confusion])
	cur = g.db.execute('select question_id from Question order by question_id desc limit 1')
	qid = cur.fetchall()[0][0]
	g.db.execute('insert into Asks (question_id, username) values(?,?)',[qid, username])
	try:
		g.db.execute('insert into Asked_in (question_id, class_name) values (?, ?)',[qid, class_name1])	
		flash('New question added to class')
	except:
		flash('Class does not exist. Question not added.')
	g.db.commit()
	return redirect(url_for('student'))


if __name__ == '__main__':
	app.run()

