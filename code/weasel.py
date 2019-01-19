from flask import (Blueprint, render_template, render_template_string, request, redirect, Markup, jsonify)
from wit import Wit
from bs4 import BeautifulSoup
import json
import urllib
import requests

######################################################################
#  Application routing and web end
######################################################################

bp = Blueprint('weasel', __name__, url_prefix = '/weasel')

# configs, setup, get the weasel ready
def wake_the_weasel(request):
	text = request.args.get('weasel_ask', False)
	if not text:
		text = "Weasel is waiting for your input"
	# wit client access token (note, client token is fine, but dont
	# expose the server token. You can find this info on the wit dashboard and docs
	# See wit dash https://wit.ai/mightyweasel/
	client = Wit("OTUZQQXJ4DTVBPRLWAXJMSZXSOROZ4PZ")
	resp = client.message( str(text) )	
	return resp


# route/render the home page
@bp.route('/weasel-index', methods = ('GET', 'POST'))
def render_index():
	if request.method == 'GET':
		return render_template('weasel/index.html',q="Weasel Ready!", weaselanswer=Markup("<p><strong>Weasel Ready</strong></p>"), rawweaselanswer="", rawjson="", rawanswerjson="")

# api requests, returns json
@bp.route('/api', methods = ('GET', 'POST'))
def serve_api_request():
	if request.method == 'GET':
		return jsonify( api_handle_weasel_message( wake_the_weasel( request ) ) )
	
# api requests, returns json
@bp.route('/action-api', methods = ('GET', 'POST'))
def serve_action_api_request():
	if request.method == 'GET':
		return action_api_handle_weasel_message( wake_the_weasel( request ) )

# route and render the results (we're subbing back to the index with extra data)
# might want to consider changing this to a template on its own down the road
@bp.route('/weasel-answer', methods = ('GET', 'POST'))
def render_answer():
	if request.method == 'GET':
		return handle_weasel_message( wake_the_weasel( request ) )

######################################################################
#  Setup weasel and define helper function
######################################################################

weasel_miss_signature_json = '{"intent":"!","topic_interest":"!","impact_on":"!","key_party":"!"}'
weasel_miss_signature = json.loads(weasel_miss_signature_json)
weasel_all_selector = "*"
weasel_data_folder = "static/data/can-live/"

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
	with open(weasel_data_folder+answerfile+'.json') as f:
		data = json.load(f)
		return data

# setup some weasel answers
weasel_answers = get_weasel_answers_json('weasel-answers-en');

# check the data point for fitness
def check_applicability(ans,q,datapoint):
	datapoint_applies = False
	try:
		if ans[datapoint] == q[datapoint] or ans[datapoint] == weasel_all_selector:
			datapoint_applies = True
	except:
		pass
	return datapoint_applies

# check the answer for applicability
def check_answer(ans,q):
	answer_applies = False

	intent_applies = check_applicability(ans,q,'intent')
	topic_applies = check_applicability(ans,q,'topic_interest')
	impact_applies = check_applicability(ans,q,'impact_on')
	party_applies = check_applicability(ans,q,'key_party')
	
	answer_applies = intent_applies and topic_applies and impact_applies and party_applies
	
	if answer_applies == True:
		return ans
	return None

# make the html fragment (consider a better solution, template string) something
# like html_snippet = render_template_string('hello {{ what }}', what='world')
def generate_weasel_answer_html(ans):
	written = ""
	written_lines = ans['answer']['written'].splitlines()
	for wl in written_lines:
		written += "<p>" + wl + "</p>"
	
	html_snippet = "" \
		+ "<div class='weasel_answer_reply'>" \
			+ "<div id='weasel_spoken'>"+ans['answer']['spoken']+"</div>" \
			+ "<div><strong><span class='mif-link'></span> Helpful Link:</strong></div><div><a href='" + ans['answer']['hyperlink'] +"'>"+ ans['answer']['hyperlink'] +"</a></div>" \
			+ "<div class='weasel_written'><strong><span class='mif-bubble'></span> Weasel Thinks:</strong></div><div>" + written + "</div>" \
			+ "<div class='weasel_media'><strong><span class='mif-video'></span> Helpful Media:</strong></div><div><div class='video-container'>" + ans['answer']['media'] + "</div></div>" \
			+ "<div class='weasel_message_signature'>" \
				+ "<strong><span class='mif-cogs'></span> Weasel Message Signature:</strong>" \
				+ "" + ans['intent'] + "" \
				+ " | " + ans['topic_interest'] + "" \
				+ " | " + ans['impact_on'] + "" \
				+ " | " + ans['key_party'] + "" \
				+ " | " + ans['answer']['type'] + "" \
			+ "</div>" \
		+ "</div>"
	return html_snippet

# helper for the handlers
def intuit_valid_answer(response):
	entities = response['entities']
	q = {}

	q['intent'] = first_entity_value_rs(entities, 'intent')
	q['topic_interest'] = first_entity_value_rs(entities, 'topic_interest')
	q['impact_on'] = first_entity_value_rs(entities, 'impact_on')
	q['key_party'] = first_entity_value_rs(entities, 'key_party')

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
	return valid_answer

# do a weasel war dance
def do_weasel_action(valid_answer,response):
	action = valid_answer['answer']['action']
	if action == "access":
		return redirect( valid_answer['answer']['hyperlink'] )
	if action == "weasel-search-lucky":
		entities = response['entities']
		extracted_q = first_entity_value_rs(entities, 'message_subject')
		search_q = extracted_q.replace(' ','+') 
		search_target = valid_answer['answer']['hyperlink'].replace('{ws}', search_q)
		# weasel the page down 
		page = requests.get( search_target )
		if page.status_code == requests.codes.ok:
			page_text = page.text
		else:
			page_text = ""
		# were using bs4 here to chew through the tags and give us workable data
		soup = BeautifulSoup(page_text, 'lxml')
		datapoints = soup.find_all('article')
		for dp in datapoints:
			anchors = dp.find_all('a')
			for a in anchors:
				search_target = a.attrs['href']
				break
			break
		return redirect( search_target )
	if action == "weasel-search":
		entities = response['entities']
		extracted_q = first_entity_value_rs(entities, 'message_subject')
		
		#python 3
		#search_q = quote(extracted_q,safe='')
		#python 2
		#search_q = pathname2url(extracted_q,safe='')
		#aaaaand the super hacky fix that resolved the 502 at 1am.
		#remember kids. Just because it works locally and you're sure the server was on Python3
		#its not always the case. question everything. question this comment.
		#question the question itself
		#just dont question me on this hack. I wanna fix it. and I will.
		search_q = extracted_q.replace(' ','+') 
		
		search_target = valid_answer['answer']['hyperlink'].replace('{ws}', search_q)
		return redirect( search_target )
	return None

# the api return as json response, this can be used for whatever application you like
def api_handle_weasel_message(response):
	valid_answer = intuit_valid_answer(response)
	return valid_answer

# the action api, executes weasel war dances (actions like redirection), returns json for everything else
def action_api_handle_weasel_message(response):
	valid_answer = intuit_valid_answer(response)
	action = do_weasel_action(valid_answer,response)
	if action is None:
		return jsonify(valid_answer)
	return action

# regular response, returns html to the render
def handle_weasel_message(response):
	valid_answer = intuit_valid_answer(response)
	action = do_weasel_action(valid_answer,response)
	if action is None:
		raw_json = json.dumps(response, indent=4, sort_keys=True)
		raw_answer_json = json.dumps(weasel_answers, indent=4, sort_keys=True)
		raw_weasel_answer_json = json.dumps(valid_answer, indent=4, sort_keys=True)	
		html_weasel_answer = Markup( generate_weasel_answer_html(valid_answer) )	
		return render_template('weasel/index.html', q=response['_text'], weaselanswer=html_weasel_answer, rawweaselanswer=raw_weasel_answer_json, rawjson=raw_json, rawanswerjson=raw_answer_json)
	return action
