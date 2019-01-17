$(function() {
	//startDictation
	var send_speech_text = function() {
		//alert( "Going to send: " + $("#transcript").val());
		document.getElementById('weaselfrm').submit();
	};
	var recognize_speech = function() {
		if (window.hasOwnProperty('webkitSpeechRecognition')) {
			var recognition = new webkitSpeechRecognition();

			recognition.continuous = false;
			recognition.interimResults = false;

			recognition.lang = "en-US";
			recognition.start();

			recognition.onresult = function(e) {
				document.getElementById('transcript').value = e.results[0][0].transcript;
				recognition.stop();
				document.getElementById('weaselfrm').submit();
			};

			recognition.onerror = function(e) {
				recognition.stop();
			}
		} else {
			$("#result_set").html("<div class='remark alert'><p><strong>Weasel is sorry...</strong> This page uses experimental voice recognition APIs.</p><p>It appears this browser doesnt support speech recognition. You might have more luck with <a href='https://www.google.com/chrome'>Chrome</a> or <a href='https://www.mozilla.org/firefox'>Firefox</a></p></div>");
		}
	};

	$("#speech_icon").on("click", recognize_speech);
	$("#send_text").on("click", send_speech_text);
});
