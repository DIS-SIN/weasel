from flask import (Blueprint, render_template, render_template_string, request, redirect, Markup, jsonify)
from wit import Wit
from bs4 import BeautifulSoup
import json
import urllib
import requests


#debug enable for logging
app_set_debug_mode = 0 # 0=none,1=entry,2=entry/exit,3=all

######################################################################
#  Application routing and web end
######################################################################

bp = Blueprint('weasel', __name__, url_prefix = '/weasel')

def weasel_translate_request(utterance):
	# this is a temporary shim to test if translation services would be beneficial to us
	# warning: replace this asap with gcloud translation api or microsoft azure cognitive
	# this is only a proof of concept. Do not use as actual solution.
	translation_service = "https://translate.google.com/#view=home&op=translate&sl=es&tl=fr&text={ws}"
	search_target = translation_service.replace('{ws}', utterance.replace(' ','%20'))
	page = requests.get( search_target )
	if page.status_code == requests.codes.ok:
		page_text = page.text
	else:
		return utterance		
	soup = BeautifulSoup(page_text, 'lxml')
	datapoints = soup.find_all('span', class_='tlid-translation translation')
	for a in datapoints:
		search_target = a.attrs['text']
		break
	return search_target	

# configs, setup, get the weasel ready
def wake_the_weasel(request):
	text = request.args.get('weasel_ask', False)
	lang = request.args.get('recognition_language', False)
	tlx = request.args.get('recognition_lang_tlxd', False)
	if not text:
		text = "Weasel is waiting for your input"
	if not lang:
		lang = "en-US"
	if not tlx:
		tlx = "disabled"
	
	if lang == "fr-CA":
		if tlx == "enabled":
			pass 
			# note: dont call the google page on prod.
			# they have a cloud api exactly for this
			# find a good cloud solution and replace this with that
			#text = weasel_translate_request(text)
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

# route/render the home page
@bp.route('/ermine', methods = ('GET', 'POST'))
def render_ermine():
	if request.method == 'GET':
		return render_template('weasel/gc-ermine.html',q="Weasel Ready!", weaselanswer=Markup("<p><strong>Weasel Ready</strong></p>"), rawweaselanswer="", rawjson="", rawanswerjson="")

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

@bp.route('/ermine-answer', methods = ('GET', 'POST'))
def render_ermine_answer():
	if request.method == 'GET':
		return handle_ermine_message( wake_the_weasel( request ) )

######################################################################
#  Setup weasel and define helper function
######################################################################

weasel_miss_signature_json = '{"intent":"!","topic_interest":"!","impact_on":"!","key_party":"!"}'
weasel_miss_signature = json.loads(weasel_miss_signature_json)
weasel_all_selector = "*"
weasel_core_authority_selector = "core"
weasel_data_folder = "static/data/can-live/"

# extract the intuition flags for our shims
def get_intuition_flags(entities, entity):
	if not entities[entity]:
		return None
	return entities[entity]

# returns None on key miss, returns the array of matched items
def get_matched_entity_list(entities, entity):
	if entity not in entities:
		return None
	elist = entities[entity]
	if not elist:
		return None
	return elist

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

def check_authority(ans,q):
	authority_applies = False
	if ans['answer']['authority'] == weasel_core_authority_selector:
		authority_applies = True
	try:
		if ans['answer']['authority'] == q['authority']:
			authority_applies = True
	except:
		pass
	return authority_applies

# check the answer for applicability
def check_answer(ans,q):
	answer_applies = False

	intent_applies = check_applicability(ans,q,'intent')
	topic_applies = check_applicability(ans,q,'topic_interest')
	impact_applies = check_applicability(ans,q,'impact_on')
	party_applies = check_applicability(ans,q,'key_party')
	
	# check data sourced from authority (core, government, community)
	authority_applies = check_authority(ans,q)

	answer_applies = intent_applies and topic_applies and impact_applies and party_applies and authority_applies
	
	if answer_applies == True:
		return ans
	return None

# helpers	

def extract_link_from_return(valid_answer,page_text,search_target):
	soup = BeautifulSoup(page_text, 'lxml')
	if valid_answer['topic_interest'] == "CPAC":
		datapoints = soup.find_all('a', class_='vidlist-main__titlelink')
		for a in datapoints:
			search_target = a.attrs['href']
			break
	else:
		datapoints = soup.find_all('article')
		for dp in datapoints:
			anchors = dp.find_all('a')
			for a in anchors:
				search_target = a.attrs['href']
				break
			break
	return search_target

def weasel_http_request(search_target):
	page = requests.get( search_target )
	if page.status_code == requests.codes.ok:
		page_text = page.text
	else:
		page_text = ""		
	return page_text

##################################################################
# SHIMS - hacks for reducing complexity of what we send to wit
# definitely want to revisit this, because we both know this isn't
# how we should do things long terms. This is spaghetti waiting to
# happen. But my model wont finish re-training until 9:33PM 
# (or 2am as is the case now as im fixing spelling ), 
# and it is only 3:49pm. I'm impatient. That's way too long to wait to make
# progress. So forgive me dear reader. Trust that this pains me 
##################################################################

# sometimes we get arrays of content back from weasel
# for now, let's just smash them together
def shim_implode_message_subject(response):
	utterance = ""
	entities = response['entities']
	mse = get_matched_entity_list(entities, 'message_subject')		
	if not mse:
		return utterance
	for ms in mse:
		if not ms['value']:
			utterance += ""
		utterance += ms['value'] + " "
	return utterance

# string inference, hardcode transliteration
# aka siht aka this.backwards() aka this is not an example of long term code
# The message passes us back the raw text before it gives us confidence values
# we're going to use the raw and just snip out the unhelpful parts of the query
# (side note, we're straight up ignoring confidence for now, but we could
# easily use those as proper replacements for these shims. anything less than .79
# we can assume is a miss. But we can probably improve our chances by removing
# known safe keyword phrases from the input. Downside there is languification.
# so if you're in a bilingual environment that hack wont cut it (well it could)
# but the effort you'd invest into a bad solution could have been spent doing it right)
def shim_siht_message_subject(response):
	utterance = ""
	siht = response['_text']
	if not siht:
		return utterance
	utterance = siht			
	return utterance

# more hacks to send good queries to canada.ca search
def shim_knock_en_common_words(utterance):
	out = ['search','Search','lucky','Lucky','into', 'will', "won't ", 'who', 'what', 'when', 'where', 'why', 'how', \
		'is', 'the', 'we', 'my', 'your', 'a', 'an', 'and', \
		#'of', \
		'that', 'this', \
		'these', 'those', 'can', 'could', 'should', 'may', 'might', 'must', 'for', 'I', "'s" \
	]
	for knock in out:
		utterance = utterance.replace(' '+knock+' ',' ')
	return utterance

def shim_intuit_intent_visualize(raw_text_query):
	if 'visualize ' in raw_text_query:
		return "visualize"
	return None

def shim_intuit_search_provider(raw_text_query):
	#debug
	if app_set_debug_mode >= 1:
		print(f"-- wsl -- > shim_intuit_search_provider > enter_method > {raw_text_query}")

	raw_text_query = raw_text_query.replace('lucky ','')
	search_provider = None
	if 'search GEDS ' in raw_text_query or 'search geds ' in raw_text_query or 'contact ' in raw_text_query:
		search_provider = "GEDS"
	if 'search CRA ' in raw_text_query or 'search cra ' in raw_text_query:
		search_provider = "CRA"
	if 'search CPAC ' in raw_text_query or 'search cpac ' in raw_text_query:
		search_provider = "CPAC"
	if 'busrides' in raw_text_query or 'bus rides' in raw_text_query:
		search_provider = "busrides.ca"

	#debug
	if app_set_debug_mode >= 2:
		print(f"-- wsl -- > shim_intuit_search_provider > exit_method > {search_provider}")

	return search_provider

 
# help out the baby weasel get better food to eat
def shim_assist_weasel_comprehension(utterance,assist_hints=""):
	# wit/message_subject seems to be a bit greedy in it's matching. Reduce the problem domain a bit
	# Ca-na-da-dot-see-eh is hard for the ai to grok, help it out

	#debug
	if app_set_debug_mode >= 1:
		print(f"-- wsl -- > shim_assist_weasel_comprehension > enter_method > {utterance} {assist_hints}")

	# set up default assist flags
	if assist_hints == "":
		assist_hints = {}

	if assist_hints.get('knock-first-word', "") == "":
		assist_hints['knock-first-word'] = False

	if assist_hints.get('knock-space-with-dash', "") == "":
		assist_hints['knock-space-with-dash'] = False

	if assist_hints.get('knock-pct20-with-dash', "") == "":
		assist_hints['knock-space-with-dash'] = False

	if assist_hints.get('knock-common-urls', "") == "":
		assist_hints['knock-common-urls'] = True

	if assist_hints.get('knock-common-words', "") == "":
		assist_hints['knock-common-urls'] = True

	if assist_hints.get('knock-common-words') == True:
		utterance = shim_knock_en_common_words( ' ' + utterance )
	
	if assist_hints.get('knock-common-urls') == True:
		utterance = utterance.replace('Canada. CA','canada.ca') 
		utterance = utterance.replace('Canada .CA','canada.ca') 
		utterance = utterance.replace('canada. CA','canada.ca') 
		utterance = utterance.replace('canada .CA','canada.ca') 
		utterance = utterance.replace('bus rides','busrides') 
		utterance = utterance.replace('busrides','busrides.ca') 
		utterance = utterance.replace('busrides .CA','busrides.ca') 
		
	if 'busrides.ca' in utterance:
		assist_hints['knock-space-with-dash'] = True
		assist_hints['knock-first-word'] = True		
	# knockouts
	if assist_hints.get('knock-first-word') == True:
		utterance = ' '.join(utterance.split()[1:])

	utterance = utterance.strip()


	# diff search providers want different food
	if assist_hints.get('knock-space-with-dash') == True:
		utterance = utterance.replace(' ','-')

	if assist_hints.get('knock-pct20-with-dash') == True: 
		utterance = utterance.replace('%20','-') 

	#debug
	if app_set_debug_mode >= 2:
		print(f"-- wsl -- > shim_assist_weasel_comprehension > exit_method > {utterance} {assist_hints}")


	return utterance

# Intuition
def intuit_valid_answer(response):
	#debug
	if app_set_debug_mode >= 1:
		print(f"-- wsl -- > intuit_valid_answer > enter_method > {response}")
	
	entities = response['entities']
	q = {}

	q['intent'] = first_entity_value_rs(entities, 'intent')
	q['topic_interest'] = first_entity_value_rs(entities, 'topic_interest')
	q['impact_on'] = first_entity_value_rs(entities, 'impact_on')
	q['key_party'] = first_entity_value_rs(entities, 'key_party')

	intuit_topic_interest = shim_intuit_search_provider( response['_text'] )
	if intuit_topic_interest is not None:
		q['topic_interest'] = intuit_topic_interest

	#shim
	if q['topic_interest'] == "busrides.ca":
		q['intent'] = 'search site' 

	intuit_intent_visualize = shim_intuit_intent_visualize( response['_text'] )
	if intuit_intent_visualize is not None:
		q['intent'] = 'visualize'


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

	#debug
	if app_set_debug_mode >= 2:
		print(f"-- wsl -- > intuit_valid_answer > exit_method > {valid_answer} {response}")

	return valid_answer
	
# do a weasel war dance
def do_weasel_action(valid_answer,response,runquery=True):
	#debug
	if app_set_debug_mode >= 1:
		runquery = False 
		print(f"-- wsl -- > do_weasel_action > enter_method > {valid_answer} {response} {runquery}")
	action = valid_answer['answer']['action']
	if action == "access":
		return redirect( valid_answer['answer']['hyperlink'] )
	if action == "get-summary":
		json_ds = weasel_http_request( valid_answer['answer']['hyperlink'] )
		raw_json=Markup(json_ds)
		return render_template('weasel/weasel-summary.html', q=response['_text'], jsonds=raw_json )
	if action == "weasel-search-lucky":	
		try:
			search_q = response['entities']['message_subject'][0]['value']
			assert len( response['entities']['message_subject'] ) == 1
			search_q = shim_assist_weasel_comprehension( \
				search_q, \
				{"knock-first-word":False} \
			)
			search_q = urllib.parse.quote(search_q, safe='') # python 3 warning, doesnt work in 2
			#debug
			if app_set_debug_mode >= 3: 
				print(f"-- wsl -- > do_weasel_action > search lucky > try > {search_q}")
		except AssertionError:
			if app_set_debug_mode >= 1: 
				print(f"-- wsl -- > EXCEPTION > AI Confused > {search_q}")
			search_q = urllib.parse.quote( \
				shim_assist_weasel_comprehension( \
					shim_siht_message_subject( response ), \
					{"knock-first-word":True, "knock-common-words": True, "knock-common-urls": True} \
					), safe=''\
			)
			#debug
			if app_set_debug_mode >= 1: 
				print(f"-- wsl -- > do_weasel_action > search lucky > AssertionError > {search_q}")							
		except:
			search_q = urllib.parse.quote( \
				shim_assist_weasel_comprehension( \
					shim_siht_message_subject( response ), \
					{"knock-first-word":False, "knock-common-words": True, "knock-common-urls": True} \
					), safe=''\
			)  # could also use shim_implode
			#debug
			if app_set_debug_mode >= 3: 
				print(f"-- wsl -- > do_weasel_action > search lucky > except > {search_q}")
		search_target = valid_answer['answer']['hyperlink'].replace('{ws}', search_q)
		# weasel the page down 
		if runquery == True: 
			page_text = weasel_http_request(search_target)
			# were using bs4 here to chew through the tags and give us workable data
			search_target = extract_link_from_return(valid_answer,page_text,search_target)	
			#debug
			if app_set_debug_mode >= 3:
				print(f"-- wsl -- > do_weasel_action > done search lucky > redirect > {search_target} {response}")
			return redirect( search_target )
		#debug
		if app_set_debug_mode >= 3:
			print(f"-- wsl -- > do_weasel_action > done search lucky > {search_target} {response}")
	if action == "weasel-search":
		# Ca-na-da-dot-see-eh is hard for the ai to grok, help it out
		try:
			search_q = response['entities']['message_subject'][0]['value']
			assert len( response['entities']['message_subject'] ) == 1
			search_q = shim_assist_weasel_comprehension( \
				search_q, \
				{"knock-first-word":False }\
			)
			search_q = urllib.parse.quote(search_q,safe='') # python 3 warning, doesnt work in 2
			#debug
			if app_set_debug_mode >= 3: 
				print(f"-- wsl -- > do_weasel_action > search > try > {search_q}")
		except AssertionError:
			if app_set_debug_mode >= 1: 
				print(f"-- wsl -- > EXCEPTION > AI Confused > {search_q}")
			search_q = urllib.parse.quote( \
				shim_assist_weasel_comprehension( \
					shim_siht_message_subject( response ), \
					{"knock-first-word":True, "knock-common-words": True, "knock-common-urls": True} \
					), safe=''\
			)
			#debug
			if app_set_debug_mode >= 1: 
				print(f"-- wsl -- > do_weasel_action > search lucky > AssertionError > {search_q}")				
		except:
			search_q = urllib.parse.quote( \
				shim_assist_weasel_comprehension( \
					shim_siht_message_subject( response ), \
					{"knock-first-word":False, "knock-common-words": True, "knock-common-urls": True} \
				), safe=''\
			)  # could also use shim_implode
			if app_set_debug_mode >= 3: 
				print(f"-- wsl -- > do_weasel_action > search > except > {search_q}")
		search_target = valid_answer['answer']['hyperlink'].replace('{ws}', search_q)
		# weasel the page down 
		if runquery == True: 
			#debug
			if app_set_debug_mode >= 3:
				print(f"-- wsl -- > do_weasel_action > done search > redirect > {search_target} {response}")
			return redirect( search_target )
	#debug
	if app_set_debug_mode >= 2: 
		print(f"-- wsl -- > do_weasel_action > end_method > {action}")

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

# the api return as json response, this can be used for whatever application you like
def api_handle_weasel_message(response):
	valid_answer = intuit_valid_answer(response)
	va = {"valid_answer": valid_answer, "wit_reply": response}
	return va

# the action api, executes weasel war dances (actions like redirection), returns json for everything else
def action_api_handle_weasel_message(response):
	valid_answer = intuit_valid_answer(response)
	action = do_weasel_action(valid_answer,response,True)
	if action is None:
		va = {"valid_answer": valid_answer, "wit_reply": response}
		return jsonify(va)
	return action

# regular response, returns html to the render
def handle_weasel_message(response,render_template_target):
	valid_answer = intuit_valid_answer(response)
	if render_template_target is None:
		render_template_target = 'weasel/index.html'

	#debug
	if app_set_debug_mode >= 1: 
		print(f"-- wsl -- > handle_weasel_message > enter > {valid_answer} {response}")


	action = do_weasel_action(valid_answer,response,True)
	if action is None:
		raw_json = json.dumps(response, indent=4, sort_keys=True)
		raw_answer_json = json.dumps(weasel_answers, indent=4, sort_keys=True)
		raw_weasel_answer_json = json.dumps(valid_answer, indent=4, sort_keys=True)	
		html_weasel_answer = Markup( generate_weasel_answer_html(valid_answer) )	
		
		#debug
		if app_set_debug_mode >= 2: 
			print(f"-- wsl -- > handle_weasel_message > no action > {raw_json} {valid_answer}")

		return render_template(render_template_target, q=response['_text'], weaselanswer=html_weasel_answer, rawweaselanswer=raw_weasel_answer_json, rawjson=raw_json, rawanswerjson=raw_answer_json)

	#debug
	if app_set_debug_mode >= 2: 
		print(f"-- wsl -- > handle_weasel_message > action > {action}")

	return action

# ermine dashboard style render
def handle_ermine_message(response):
	return handle_weasel_message(response,'weasel/gc-ermine.html')
