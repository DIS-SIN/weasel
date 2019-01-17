from flask import (Blueprint, render_template, request, Markup)
from wit import Wit
import json

bp = Blueprint('weasel', __name__, url_prefix = '/weasel')

# route/render the home page
@bp.route('/weasel-index', methods = ('GET', 'POST'))
def render_index():
	if request.method == 'GET':
		return render_template('weasel/index.html',q="Weasel Ready!", weaselanswer=Markup("<p><strong>Weasel Ready</strong></p>"), rawweaselanswer="", rawjson="", rawanswerjson="")

# route and render the results (we're subbing back to the index with extra data)
# might want to consider changing this to a template on its own down the road
@bp.route('/weasel-process-result', methods = ('GET', 'POST'))
def render_process_result():
	if request.method == 'GET':
		text = request.args.get('weasel_ask', False)
		if not text:
			text = "Weasel is waiting for your input"

		# wit client access token
		# See wit dash https://wit.ai/mightyweasel/
		client = Wit("OTUZQQXJ4DTVBPRLWAXJMSZXSOROZ4PZ")
		resp = client.message( str(text) )
		return handle_weasel_message(resp)

# returns None on key miss, requires error handling for odd requests
def first_entity_value(entities, entity):
	if entity not in entities:
		return None
	val = entities[entity][0]['value']
	if not val:
		return None
	return val

# short circuit, returns a blank string on key miss
def first_entity_value_rs(entities, entity):
	if entity not in entities:
		return ""
	val = entities[entity][0]['value']
	if not val:
		return ""
	return val

# pull in the json file and load it for use
def get_weasel_answers_json(answerfile):
	with open("static/data/can-live/"+answerfile+'.json') as f:
		data = json.load(f)
		return data

weasel_answers = get_weasel_answers_json('weasel-answers-en');
weasel_miss_signature_json = '{"intent":"!","topic_interest":"!","impact_on":"!","key_party":"!"}'
weasel_miss_signature = json.loads(weasel_miss_signature_json)

def check_answer(ans,q):
	answer_applies = False

	intent_applies = False
	if ans['intent'] == q['intent'] or ans['intent'] == "*":
		intent_applies = True

	topic_applies = False
	if ans['topic_interest'] == q['topic_interest'] or ans['topic_interest'] == "*":
		topic_applies = True

	impact_applies = False
	if ans['impact_on'] == q['impact_on'] or ans['impact_on'] == "*":
		impact_applies = True

	party_applies = False
	if ans['key_party'] == q['key_party'] or ans['key_party'] == "*":
		party_applies = True
	
	answer_applies = intent_applies and topic_applies and impact_applies and party_applies
	
	if answer_applies == True:
		return ans
	return None

def generate_weasel_answer_html(ans):
	written = ""
	written_lines = ans['answer']['written'].splitlines()
	for wl in written_lines:
		written += "<p>" + wl + "</p>"
	html_snippet = "<div class='weasel_answer_reply'>" \
		+ "<div><strong>Helpful Link:</strong></div><div><a href='" + ans['answer']['hyperlink'] +"'>"+ ans['answer']['hyperlink'] +"</a></div>" \
		+ "<div class='weasel_written'><strong>Weasel Thinks:</strong></div><div>" + written + "</div>" \
		+ "<div class='weasel_media'><strong>Helpful Video:</strong></div><div>" + ans['answer']['media'] + "</div>" \
		+ "<ul>" \
			+ "<li>" + ans['intent'] + "</li>" \
			+ "<li>" + ans['topic_interest'] + "</li>" \
			+ "<li>" + ans['impact_on'] + "</li>" \
			+ "<li>" + ans['key_party'] + "</li>" \
			+ "<li>" + ans['answer']['type'] + "</li>" \
		+ "</ul>" \
		+ "</div>"
	return html_snippet

def handle_weasel_message(response):
	entities = response['entities']
	
	raw_json = json.dumps(response, indent=4, sort_keys=True)
	raw_answer_json = json.dumps(weasel_answers, indent=4, sort_keys=True)
	
	q = {}

	q['intent'] = first_entity_value_rs(entities, 'intent')
	q['topic_interest'] = first_entity_value_rs(entities, 'topic_interest')
	q['impact_on'] = first_entity_value_rs(entities, 'impact_on')
	q['key_party'] = first_entity_value(entities, 'key_party')

	# look for valid answer
	valid_answer = None
	for ans in weasel_answers['answers']:
		valid_answer = check_answer(ans,q) 
		if not valid_answer:
			continue 
		result = valid_answer
		break

	# weasel is sorry, find the sorry answer and use it
	if not valid_answer:
		for ans in weasel_answers['answers']:
			valid_answer = check_answer(ans,weasel_miss_signature)
			if not valid_answer:
				continue
			result = valid_answer
			break

	raw_weasel_answer_json = json.dumps(valid_answer, indent=4, sort_keys=True)
	
	html_weasel_answer = Markup( generate_weasel_answer_html(valid_answer) )	

	return render_template('weasel/index.html', q=response['_text'] ,weaselanswer=html_weasel_answer, rawweaselanswer=raw_weasel_answer_json, rawjson=raw_json, rawanswerjson=raw_answer_json)

# proc the message we got from wit
def handle_message(response):
	entities = response['entities']
	intent = first_entity_value(entities, 'intent')

	raw_json = json.dumps(response, indent=4, sort_keys=True)
	status = "Weasel Found Something"
	result = ""

	if intent == "why is":
		topic = first_entity_value_rs(entities, 'topic_interest')
		impacts = first_entity_value_rs(entities, 'impact_on')
		party = first_entity_value_rs(entities, 'key_party')
		result = "["+intent+"]["+topic+"]["+impacts+"]["+party+"]"
	else:
		status = "Weasel didn't quite get it"
		result = "Weasel doesn't know that... yet!"

	return render_template('weasel/index.html', myout = result, mystatus=status, rawjson=raw_json)

