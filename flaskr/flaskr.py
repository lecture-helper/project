# all the imports
import os
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

@app.route('/')
def show_questions():
    cur = g.db.execute('select question_text, question_date, question_time from Question order by question_date desc, question_time desc')
    questions = [dict(text=row[0], date=row[1], time=row[2]) for row in cur.fetchall()]
    return render_template('show_questions.html', questions=questions)

@app.route('/add', methods=['POST'])
def add_question():
    txt = request.form['text']
    print txt
    if len(txt) == 0:
        flash('Empty question received and not inserted into db')
        return redirect(url_for('show_questions'))

    dt = datetime.datetime.now()
    date = str(dt.date())
    time = str(dt.time())
    g.db.execute('insert into Question (question_text, question_date, question_time) values (?, ?, ?)',
        [txt, date, time])
    g.db.commit()
    flash('New question received and inserted into db')
    return redirect(url_for('show_questions'))

if __name__ == '__main__':
    app.run()


