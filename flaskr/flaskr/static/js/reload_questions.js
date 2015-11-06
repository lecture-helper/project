
$(function(){

	var class_name = $('#class_name').text();
	console.log('connecting');
	socket = io.connect('/questions');

	socket.on('connect', function () {
		socket.emit('join', class_name);
	});


	socket.on('all_to_prof', function (msg, room) {
		console.log('updating all');
		var questions = JSON.parse(msg);
		var parent = $('#all');
		var children = parent.children('div');
		if (room != class_name) {
			
		}
		else if (questions.length == 0) {
			$('#no_questions').show();
		} else {
			$('#no_questions').hide();
			for (i = 0; i < questions.length; i++) {
				console.log(questions[i]['text']);
				var content = '<h4>' + questions[i]['text'] + '</h4>' + questions[i]['date'] + ',' + questions[i]['time'] + '<br>';
				content += 'Confusion: ' + questions[i].confusion + ' | Tags:';
				for (tag_i = 0; tag_i < questions[i]['tags'].length; tag_i++ ) {
					content += questions[i]['tags'][tag_i] + ' ';
				}
				if (i < children.length) {
					$(children[i]).replaceWith('<div>' + content + '<br></div>');
				} else {
					parent.append('<div>' + content + '<br></div>');
				}
			}
		}
	});

	socket.on('best_to_prof', function (msg, room) {
		console.log('updating best');
		var questions = JSON.parse(msg);
		var parent = $('#best');
		var children = parent.children('div');
		if (room != class_name) {
			
		}
		else if (questions.length == 0) {
			$('#no_best_questions').show();
		} else {
			$('#no_best_questions').hide();
			$('#loading').hide();
			for (i = 0; i < questions.length; i++) {
				var content = '<h4>' + questions[i] + '</h4>';
				if (i < children.length) {
					$(children[i]).replaceWith('<div>' + content + '<br></div>');
				} else {
					parent.append('<div>' + content + '<br></div>');
				}
			}
		}
	});
});

