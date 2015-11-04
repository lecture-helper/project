from flaskr import *
from math import ceil
from collections import defaultdict 

MAX_TIME = 75
NUM_INTERVALS = 5

@app.route('/professor_class/<username1>/<class_name1>/timeline/')
def timeline_main_page(username1, class_name1):
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))

	if current_user.isStudent: return redirect(url_for('student'))

	dates_query = g.db.execute('select question_date from Question where (question_id IN (select question_id from Asked_in where class_name= (?) )) order by question_date desc', [class_name1])
	dates = list(set([row[0] for row in dates_query.fetchall()]))

	return render_template('timeline_main_page.html', username = current_user.username, class_name = class_name1, date_list = dates)

@app.route('/professor_class/<username>/<class_name1>/timeline/<question_date1>')
def timeline(username, class_name1, question_date1):
	from flask.ext.login import current_user
	if not current_user.is_authenticated():
		return redirect(url_for('login'))

	if current_user.isStudent: return redirect(url_for('student'))
	
	# min_time is the starting point of the timeline (minimum of question_time for all questions asked on given date)
	min_time = g.db.execute('select min(question_time) from Question where question_date = (?) AND (question_id IN (select question_id from Asked_in where class_name= (?) ))', [question_date1, class_name1]).fetchall()[0][0]
	
	# title is a large title above the timeline - used only to indicate when no questions were asked
	if(min_time != None): 
		title  = ""
		min_time = parse_time(min_time, question_date1)
	else: 
		title = "No Questions Were Asked"
		min_time = 0

	# gets lists of questions per confusion - questions[0] are yellow, questions[1] are orange, questions[2] are red
	questions = [get_questions_by_confusion(class_name1, question_date1, confusion, min_time) for confusion in range(1,4)]
	
	# redundant
	cur_tags = g.db.execute('select question_tag, question_time from Question where question_date = (?) AND (question_id IN (select question_id from Asked_in where class_name= (?) ))', [question_date1, class_name1])

	interval = int(float(MAX_TIME)/float(NUM_INTERVALS))
	interval_time_list = range(interval, MAX_TIME+1, interval)

	tag_dict = defaultdict(list)
	tag_freq_dict = defaultdict(int)
	for row in cur_tags.fetchall():
		tag_time = max(float(parse_time(row[1], question_date1) - min_time), interval)
		key = int(ceil(tag_time/15)*15)

		tag = row[0].strip('#')
		tag_dict[key].append(tag)
		tag_freq_dict[tag] += 1

	tags = [get_tag_element(tag_dict, tag_freq_dict, curr_interval, interval) for curr_interval in range(5)]

	return render_template('timeline.html',tags1 = tags[0], tags2=tags[1], tags3 = tags[2], tags4 = tags[3], tags5=tags[4], max_time = MAX_TIME, questions_y=questions[0], questions_o = questions[1], questions_r = questions[2], class_name=class_name1, prof_username = username, date = question_date1, exist_questions = title)


def get_tag_element(tag_lists, tag_freq_dict, curr_interval, interval):
	tags = list(set(tag_lists[(curr_interval+1)*interval]))
	return [dict(indexLabel=str(tag), x=(curr_interval+1)*interval + random.uniform(-3,3), y= idx*16+1, indexLabelFontSize=((tag_freq_dict[tag]*5.5)+3)) for (idx, tag) in enumerate(tags)]

def get_questions_by_confusion(class_name, question_date, confusion, min_time):
	questions = g.db.execute('select question_text, question_time from Question where question_date = (?) AND question_confusion = (?) AND (question_id IN (select question_id from Asked_in where class_name=(?) ))', [question_date, str(confusion), class_name])
	return [dict(label=str(row[0]),x=parse_time(row[1], question_date)-min_time+ random.uniform(0,1), y=confusion*3, z=10) for row in questions.fetchall()] 


def parse_time(t, d): 
	new_time = datetime.datetime.strptime(t, '%H:%M:%S.%f')
	new_date = datetime.datetime.strptime(d, '%Y-%m-%d')

	dt2 = datetime.datetime(new_date.year, new_date.month , new_date.day, new_time.hour, new_time.minute)
	time_seconds = time.mktime(dt2.timetuple())+1e-6*new_time.microsecond
	time_minutes = time_seconds/60
	return time_minutes 