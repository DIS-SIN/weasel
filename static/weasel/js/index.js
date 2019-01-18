$(function() {
	var synth = window.speechSynthesis;
	var pitchValue = 1;
	var rateValue = 1.3;

	var speak_back = function(inputTxt){
	    try {
		    if (synth.speaking) {
		        console.error('speechSynthesis.speaking');
		        return;
		    }
		    if (inputTxt !== '') {
			    var utterThis = new SpeechSynthesisUtterance(inputTxt);
			    utterThis.pitch = pitchValue;
			    utterThis.rate = rateValue;
			    synth.speak(utterThis);
			}
		} catch(error) {
			// do nothing, not all weasels squeak
		}
	};
	
	var weasel_speak = function() {
		if($('#weasel_spoken').length) { 
			speak_back( $('#weasel_spoken').text() );
		} else {
			speak_back( "Weasel ready!" );
		}
	};
	var weasel_dont_speak = function() { // no doubt: i know what you're thinking, I don't need your reasons
		synth.cancel();
	};
	weasel_speak();
	//speak_back( $("#q_asked").text() );

	var clear_text = function() {
		$("#transcript").val('');
		$("#weasel_console").html('');
		$("#q_asked").html('Weasel Ready!');
	};
	var send_speech_text = function() {
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

	var weasel_console_display = function() {
		$("#weasel_console").toggle();
	};

	$("#speech_icon").on("click", recognize_speech);
	$("#send_text").on("click", send_speech_text);
	$("#clear_text").on("click", clear_text);
	$("#talk_back").on("click", weasel_speak);
	$("#dont_talk_back").on("click", weasel_dont_speak);
	$("#toggle_weasel_console").on("click", weasel_console_display)
});


