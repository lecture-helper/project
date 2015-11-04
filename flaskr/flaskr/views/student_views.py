from flaskr import *
	
@app.route('/student')
def student():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	if current_user.isProfessor: return redirect(url_for('professor'))
	cur = g.db.execute('select Class.class_name from Class, Subscribes where Subscribes.class_name=Class.class_name AND Subscribes.username="' + current_user.username + '"')
	classes = [dict(class_name=row[0]) for row in cur.fetchall()]

	return render_template('student.html', classes=classes)

@app.route('/student_class/<username>/<class_name1>')
def student_class(username, class_name1):
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	if current_user.isProfessor: return redirect(url_for('professor'))
	username = current_user.username
	cur = g.db.execute('select question_text, question_date, question_time, question_confusion, question_tag from Question, Asks where Question.question_id IN (select question_id from Asked_in where Asked_in.class_name="'+ class_name1 +'") AND Question.question_id=Asks.question_id AND Asks.username="'+username+'" order by question_date desc, question_time desc')
	questions = [dict(text=row[0], date=formatDate(row[1]), time=formatTime(row[2]), confusion=row[3], tags=formatTag(row[4])) for row in cur.fetchall()]
	return render_template('questions.html', questions=questions, class_name = class_name1)


@app.route('/add_question', methods=['POST'])
def add_question():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	if current_user.isProfessor: return redirect(url_for('professor'))
	txt = request.form['question'].strip()
	class_name1 = request.form['class_name'].strip()
	confusion = request.form['confusion'].strip()
	username = current_user.username.strip()
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
		return json.dumps({'status':'OK', 'flash':'New question added to class', 'text':txt, 'date':formatDate(date), 'time':formatTime(time), 'confusion':confusion, 'tag':formatTag(tags)})
	except:
		return json.dumps({'status':'no_class', 'flash':'Class does not exist. Question not added.'})