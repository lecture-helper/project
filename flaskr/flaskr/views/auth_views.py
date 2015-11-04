from flaskr import *

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
	user_type = request.form['type'].lower().strip()
	if user_type == 'student': user_type = 0
	else: user_type = 1

	username = request.form['username'].strip()
	password = request.form['password']
	email = request.form['email'].strip()
	if len(email.split('@')) != 2: 
		flash('Error: Not a valid email')
		return redirect(url_for('home'))
	if len(email) < 6:
		flash('Error: Email too short to be valid')
		return redirect(url_for('home'))
	if email[len(email)-4:len(email)] != '.edu':
		flash('Error: Please use a .edu email')
		return redirect(url_for('home'))

	# password encryption
	m = hashlib.sha384()
	m.update(password)
	password = unicode(m.hexdigest())

	try:
		cur = g.db.execute('insert into Person(type, username, password, email) values (?,?,?,?)', [user_type, username, password, email])
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
	username = request.form['username'].strip()
	password = request.form['password']

	# password encryption
	m = hashlib.sha384()
	m.update(password)
	password = unicode(m.hexdigest())

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