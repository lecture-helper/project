from flaskr import *

@app.route('/subscribe', methods=['POST'])
def subscribe():
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))
		
	class_name = request.form['class_name'].strip()
	class_key = request.form['class_key'].strip()
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

	class_name = request.form['class_name'].strip()
	username = current_user.username
	g.db.execute('Delete from Subscribes where Subscribes.username="' + username + '" AND Subscribes.class_name="' + class_name + '"')
	g.db.commit()
	return json.dumps({'status':'OK', 'flash':'Unsubscribed from class'})