$(document).ready(function() {
	resetStatus()
	attachPlayHandler();
	attachStopHandler();
	setInterval(getStatus, 2000);
});

function attachPlayHandler() {
	// attach the handler for the play button
	$("a.play").each(function() {
		var that = $(this);
		$(this).click(function() {
			// load the layer data
			playTrack(that.attr("data-track"));
		});
	});
}

function attachStopHandler() {
	// attach the handler for the stop button
	$("a.stop").each(function() {
		var that = $(this);
		$(this).click(function() {
			// load the layer data
			stopTrack();
		});
	});
}

function playTrack(track_id) {
	$.ajax({
		url : '/music/api/v1.0/player',
		type : 'PUT',
		data : '{"command":"play","track":"' + track_id + '"}',
		contentType : 'application/json',
		dataType : 'json',
		success : function(data) {
			showStatus(data, track_id);
		}
	});
}

function stopTrack() {
	$.ajax({
		url : '/music/api/v1.0/player',
		type : 'PUT',
		data : '{"command":"stop"}',
		contentType : 'application/json',
		dataType : 'json',
		success : function(data) {
			resetStatus();
		}
	});
}

function resetStatus() {
	$(".status").each(function() {

		$(this).html("<span class=\"label label-info\"> stopped </span>");
	});
}

function getStatus(){
	$.get("/music/api/v1.0/player", function(data) {
		showStatus(data);
	});
}

function showStatus(data) {	
	//get the right row
	$("#"+data.current.id+"_status").html("<span class=\"label label-info\">"
			+ data.status + "</span>");
}