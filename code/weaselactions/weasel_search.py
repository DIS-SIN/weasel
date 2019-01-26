# over importing during quick dev, todo: clean imports to just the basics
from flask import (render_template, render_template_string, request, redirect, Markup, jsonify)
from bs4 import BeautifulSoup
import json
import urllib
from code.intuitionshims import shims
from code.weasellib import wlib

app_set_debug_mode = 0 # 0 = off, 1 on, 2 in/out. 3 all

def weasel_act(valid_answer,response,runquery=True):
    # Ca-na-da-dot-see-eh is hard for the ai to grok, help it out
    try:
        search_q = response['entities']['message_subject'][0]['value']
        assert len( response['entities']['message_subject'] ) == 1
        search_q = shims.shim_assist_weasel_comprehension( \
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
            shims.shim_assist_weasel_comprehension( \
                shims.shim_siht_message_subject( response ), \
                {"knock-first-word":True, "knock-common-words": True, "knock-common-urls": True} \
                ), safe=''\
        )
        #debug
        if app_set_debug_mode >= 1: 
            print(f"-- wsl -- > do_weasel_action > search lucky > AssertionError > {search_q}")                
    except:
        search_q = urllib.parse.quote( \
            shims.shim_assist_weasel_comprehension( \
                shims.shim_siht_message_subject( response ), \
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
