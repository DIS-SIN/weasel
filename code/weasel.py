from flask import (Blueprint, render_template, render_template_string, request, redirect, Markup, jsonify)
from wit import Wit
from bs4 import BeautifulSoup
import json
import urllib
import requests
# Python 2/3 imports changed, the dot is required it seems
from .weasellib import wlib
from .intuitionshims import shims
from .weaselactions import (access, display, get_summary, weasel_search, weasel_search_lucky)

######################################################################
#  System Config. Consider moving to env vars.
######################################################################

#debug enable for logging
# 0=none,1=entry,2=entry/exit,3=all
app_set_debug_mode = 0
# True, use package weasel_intuition - False, dont (test AI without help)
app_set_use_intuition_shims = True 

######################################################################
#  Application routing and web end
######################################################################

bp = Blueprint('weasel', __name__, url_prefix = '/weasel')


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
        return jsonify( api_handle_weasel_message( wlib.wake_the_weasel( request ) ) )
    
# api requests, returns json
@bp.route('/action-api', methods = ('GET', 'POST'))
def serve_action_api_request():
    if request.method == 'GET':
        return action_api_handle_weasel_message( wlib.wake_the_weasel( request ) )

# route and render the results (we're subbing back to the index with extra data)
# might want to consider changing this to a template on its own down the road
@bp.route('/weasel-answer', methods = ('GET', 'POST'))
def render_answer():
    if request.method == 'GET':
        return handle_weasel_message( wlib.wake_the_weasel( request ) )

@bp.route('/ermine-answer', methods = ('GET', 'POST'))
def render_ermine_answer():
    if request.method == 'GET':
        return handle_ermine_message( wlib.wake_the_weasel( request ) )

######################################################################
#  Setup weasel and define helper function
######################################################################

weasel_miss_signature_json = '{"intent":"!","topic_interest":"!","impact_on":"!","key_party":"!"}'
weasel_miss_signature = json.loads(weasel_miss_signature_json)


# setup some weasel answers
weasel_answers = wlib.get_weasel_answers_json('weasel-answers-en');

# Intuition
def intuit_valid_answer(response):
    #debug
    if app_set_debug_mode >= 1:
        print(f"-- wsl -- > intuit_valid_answer > enter_method > {response}")
    
    entities = response['entities']
    q = {}

    q['intent'] = wlib.first_entity_value_rs(entities, 'intent')
    q['topic_interest'] = wlib.first_entity_value_rs(entities, 'topic_interest')
    q['impact_on'] = wlib.first_entity_value_rs(entities, 'impact_on')
    q['key_party'] = wlib.first_entity_value_rs(entities, 'key_party')

    ##################################################################
    # SHIMS - hacks for reducing complexity of what we send to wit
    # definitely want to revisit this, because we both know this isn't
    # how we should do things long terms. This is spaghetti waiting to
    # happen. But my model wont finish re-training until 9:33PM 
    # (or 2am as is the case now as im fixing spelling ), 
    # and it is only 3:49pm. I'm impatient. That's way too long to wait to make
    # progress. So forgive me dear reader. Trust that this pains me 
    ##################################################################

    # ideally the AI would always give us the message JSON with the same params
    # each time we ask it something, but thats a good million training datapoints
    # away at least. While it's learning it can be very confident of something
    # thats just not correct. Kinda like humans. We should aim to have strong opinions
    # that are loosely held and subject to discussion without ego interrupting growth
    # So lets cut our AI a break and give it some intuitions, you know the stuff you
    # know you should know even if you didn't understand it. Kind of like if you
    # were visiting a country where you didnt speak the language. You could still find 
    # something to eat with hand signals alone, or if you got lucky (and nowadays more
    # often than not you get lucky) some kind human will understand your interface and
    # provide an adapater for you. Do good things people.

    # Aaaanyways. These functions will try some hacky, but useful things.
    # Also, in time they should be wrapped to only fire if the AI really did get confused
    # never forget, the two state 3d button in Windows 3.0 was just two lines of pixels
    # just with different shades. And the first 3D was red/blue lenses with two sets of lines
    # painted. Things have an amazing ability to evolve.

    q = shims.run_intuition_shims(q, response, app_set_use_intuition_shims) # from weaselintuition.shims

    # look for valid answer
    valid_answer = None
    for ans in weasel_answers['answers']:
        valid_answer = wlib.check_answer(ans,q) 
        if not valid_answer:
            continue 
        result = valid_answer
        break

    # weasel is sorry, find the sorry answer and use it
    if not valid_answer:
        for ans in weasel_answers['answers']:
            valid_answer = wlib.check_answer(ans,weasel_miss_signature)
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
        return access.weasel_act(valid_answer,response,runquery)
    if action == "get-summary":
        return get_summary.weasel_act(valid_answer,response,runquery)
    if action == "weasel-search-lucky":    
        return weasel_search_lucky.weasel_act(valid_answer,response,runquery)
    if action == "weasel-search":
        return weasel_search.weasel_act(valid_answer,response,runquery)
    if action == "display":
        return display.weasel_act(valid_answer,response,runquery)
    #debug
    if app_set_debug_mode >= 2: 
        print(f"-- wsl -- > do_weasel_action > end_method > {action}")

    return None


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
        html_weasel_answer = Markup( wlib.generate_weasel_answer_html(valid_answer) )    
        
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
