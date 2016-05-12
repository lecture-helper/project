// Support TLS-specific URLs, when appropriate.
if (window.location.protocol == "https:") {
  var ws_scheme = "wss://";
} else {
  var ws_scheme = "ws://"
};

var inbox = new ReconnectingWebSocket(ws_scheme + location.host + "/receive");

inbox.onmessage = function(message) {
  var data = JSON.parse(message.data);
  if (data.class_name == $("div#class_name").text().trim()) {
    $("div#all").prepend("<h4>" + data.question + "</h4>" + data.datetime + "<br>Confusion: " + data.confusion + " | Tags: " + data.tag + "<br>");
  }
};

inbox.onclose = function(){
    this.inbox = new WebSocket(inbox.url);
};

var get_best_questions = function() {
    $.getJSON('/best_questions', {
      class_name1: $("div#class_name").text().trim()
    }, function(data) {
        if (data.status == "OK") {
            var questions = data.result;
            var parent = $('#best');
            var children = parent.children('div');
            if (questions.length == 0) {
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
        }
    });
    return false;
};

var interval = setInterval(get_best_questions, 20000);
get_best_questions();

$(window).on('beforeunload', function() {
    clearInterval(interval);
}); 