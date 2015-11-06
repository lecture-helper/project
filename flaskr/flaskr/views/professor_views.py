from flaskr import *
import parseQuestions

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

	# question_query = g.db.execute('select question_text from Question where question_id IN (select question_id from Asked_in where class_name="'+class_name1+'")  order by question_date desc, question_time desc')
	# # select last 10 questions
	# question_list = [str(row[0]) for row in question_query][:10]
	# # choose top 3 most relevant questions
	# top_questions = parseQuestions.relevantQuestions(question_list, 3)
	top_questions = []

	cur = g.db.execute('select question_text, question_date, question_time,question_confusion, question_tag from Question where question_id IN (select question_id from Asked_in where class_name="'+class_name1+'")  order by question_date desc, question_time desc')
	questions = [dict(text=row[0], date=formatDate(row[1]), time=formatTime(row[2]), confusion=row[3], tags=formatTag(row[4])) for row in cur.fetchall()]

	return render_template('class.html', questions=questions, class_name=class_name1, username = current_user.username, nlp_result = top_questions)

@app.route('/add_class', methods=['POST'])
def add_class():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	
	if current_user.isStudent: return redirect(url_for('student'))
	
	# sanity checks of inputs
	class_name = request.form['class_name'].strip()
	if len(class_name) == 0:
		return json.dumps({'status':'no_class', 'flash':'No class name received. Class not added.'})

	class_key = request.form['class_key'].strip()
	if len(class_key) == 0:
		return json.dumps({'status':'no_key', 'flash':'No class key received. Class not added'})

	class_admins = request.form['class_admins'].strip()
	if len(class_admins) == 0:
		return json.dumps({'status':'no_admin', 'flash':'No admins received. Class not added.'})
	for admin in class_admins.split(','):
		person = g.db.execute('select username from Person where username="' + admin.strip() + '"').fetchall()
		if len(person) == 0:
			return json.dumps({'status':'incorrect', 'flash':'One of the admins does not exist. Class not added.'})

	# insert class into db
	username = current_user.username
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

	# get admins for class
	class_name = request.form['class_name'].strip()
	cur = g.db.execute('Select class_admin from Class where class_name="' + class_name + '"')
	class_admins = cur.fetchall()[0][0]
	admins = [admin.strip() for admin in class_admins.split(',')]

	# check if user is class admin
	if current_user.username not in admins:
		return json.dumps({'status':'OK', 'flash':'You must be an admin to delete this class'})

	# delete class from db
	g.db.execute('Delete from Class where class_name = (?)', [class_name])
	g.db.execute('Delete from Subscribes where class_name = (?)', [class_name])
	g.db.commit()
	return json.dumps({'status':'deleted', 'flash':'Class deleted'})


@app.route('/update_key', methods=['POST'])
def update_key():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	
	if current_user.isStudent: return redirect(url_for('student'))

	newkey = request.form['newkey'].strip()
	oldkey = request.form['oldkey'].strip()

	# sanity check of new key input
	if len(newkey) == 0:
		return json.dumps({'status':'OK', 'class_key':oldkey, 'flash':'No key received'})

	# get admins for class
	class_name = request.form['class_name'].strip()
	cur = g.db.execute('Select class_admin from Class where class_name="' + class_name + '"')
	class_admins = cur.fetchall()[0][0]
	admins = [admin.strip() for admin in class_admins.split(',')]

	# check if user is class admin
	if current_user.username not in admins:
		return json.dumps({'status':'OK', 'class_key':oldkey, 'flash':'You must be an admin to change the key'})

	# update class key in db
	g.db.execute('Update Class Set class_key="' + newkey + '" where class_name="' + class_name + '"')
	g.db.commit()
	return json.dumps({'status':'OK', 'class_key':newkey, 'flash':'Key updated'})

@app.route('/update_admin', methods=['POST'])
def update_admin():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
	
	if current_user.isStudent: return redirect(url_for('student'))

	# sanity check of new admins input
	newadmins = request.form['newadmins'].strip()
	oldadmins = request.form['oldadmin'].strip()
	if len(newadmins) == 0:
		return json.dumps({'status':'no_admin', 'admin':oldadmins, 'flash':'No admins received'})

	# check if user is class admin
	oldadmins_split = [admin.strip() for admin in oldadmins.split(',')]
	if current_user.username not in oldadmins_split:
		return json.dumps({'status':'not_authorized', 'admin':oldadmins, 'flash':'You must be an admin to change the admins'})

	# check if all of the new admins are valid 
	for admin in newadmins.split(','):
		person = g.db.execute('select username from Person where username="' + admin.strip() + '"').fetchall()
		if len(person) == 0:
			return json.dumps({'status':'not_exist', 'admin':oldadmins, 'flash':'One of the admins does not exist'})

	# update admins in db
	class_name = request.form['class_name'].strip()
	g.db.execute('Update Class Set class_admin="' + newadmins + '" where class_name="' + class_name + '"')	
	g.db.commit()
	return json.dumps({'status':'OK', 'admin':newadmins, 'flash':'Admins updated'})