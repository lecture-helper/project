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


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route('/professor')
def professor():
    cur = g.db.execute('select * from Class')
    prof_class = [dict(class_name=row[0], class_key=row[1]) for row in cur.fetchall()]
    return render_template('professor.html', classes=prof_class)



@app.route('/professor_class/<class_name1>')
def professor_class():
    cur = g.db.execute('select question_text, question_date, question_time from Question where question_id = (select question_id from Asked_in where class_name=class_name1)  order by question_date desc, question_time desc')
    questions = [dict(text=row[0], date=row[1], time=row[2]) for row in cur.fetchall()]
    return render_template('class.html', questions=questions, class_name=class_name1)

@app.route('/add_class', methods=['POST'])
def add_class():
    class_name = request.form['class_name']
    class_key = request.form['class_key']
    if len(class_name) == 0:
        flash('No class name received and not inserted into db')
        return redirect(url_for('professor'))

    if len(class_key) == 0:
        flash('No class key received and not inserted into db')
        return redirect(url_for('professor'))

    g.db.execute('insert into Class (class_name, class_key) values (?, ?)',
        [class_name, class_key])
    g.db.commit()
    flash('New class added')
    return redirect(url_for('professor'))


@app.route('/delete_class', methods=['POST'])
def delete_class():
    class_name = request.form['class_name']
    if len(class_name) == 0:
        flash('No class name received and not deleted from db')
        return redirect(url_for('professor'))


    g.db.execute('Delete from Class where class_name = (?)',
        [class_name])
    g.db.commit()
    flash('Class deleted')
    return redirect(url_for('professor'))
	
	

@app.route('/student')
def student():
    cur = g.db.execute('select question_text, question_date, question_time from Question order by question_date desc, question_time desc')
    questions = [dict(text=row[0], date=row[1], time=row[2]) for row in cur.fetchall()]
    return render_template('student.html', questions=questions)


@app.route('/add_question', methods=['POST'])
def add_question():
    txt = request.form['question']
    class_name = request.form['class_name']
    qid = uuid.uuid1()
    if len(txt) == 0:
        flash('Empty question received and not inserted into db')
        return redirect(url_for('student'))

    dt = datetime.datetime.now()
    date = str(dt.date())
    time = str(dt.time())
    g.db.execute('insert into Question (question_id, question_text, question_date, question_time) values (?, ?, ?, ?)',
        [qid, txt, date, time])
    g.db.execute('insert into Asked_in (question_id, class_name) values (?, ?)',
        [qid, class_name])
    g.db.commit()
    flash('New question received and inserted into db')
    return redirect(url_for('student'))

if __name__ == '__main__':
    app.run()


