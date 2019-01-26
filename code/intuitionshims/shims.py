# over importing during quick dev, todo: clean imports to just the basics
from flask import (Blueprint, render_template, render_template_string, request, redirect, Markup, jsonify)
from wit import Wit
from bs4 import BeautifulSoup
import json
import urllib
import requests

app_set_debug_mode = 0 # 0 = off, 1 on, 2 in/out. 3 all

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
    out = ['search','Search','course','courses','catalog','catalogue','lucky','Lucky','into', 'will', "won't ", 'who', 'what', 'when', 'where', 'why', 'how', \
        'is', 'the', 'we', 'my', 'your', 'a', 'an', 'and', \
        #'of', \
        'that', 'this', \
        'these', 'those', 'can', 'could', 'should', 'may', 'might', 'must', 'for', 'I', "'s" \
    ]
    for knock in out:
        utterance = utterance.replace(' '+knock+' ',' ')
    return utterance

def shim_intuit_intent_visualize(raw_text_query):
    #debug
    if app_set_debug_mode >= 1:
        print(f"-- wsl -- > shim_intuit_intent_visualize > enter_method > {raw_text_query}")

    # note the space, brittle shim
    if 'visualize ' in raw_text_query:
        return "visualize"
    return None

def shim_intuit_intent_learnskill(raw_text_query):
    #debug
    if app_set_debug_mode >= 1:
        print(f"-- wsl -- > shim_intuit_intent_learnskill > enter_method > {raw_text_query}")

    utterance = raw_text_query.lower().strip()
    utterance = ' '+utterance+' '
    if app_set_debug_mode >= 1:
        print(f"-- wsl -- > shim_intuit_intent_learnskill > check > {utterance}")

    if 'learn' in utterance:
        out = ['learn', 'how', 'do', 'i', 'in', 'with', 'want','to','program','code','develop','build','a' \
        ]
        for knock in out:
            utterance = utterance.replace(' '+knock+' ',' ')
        utterance = utterance.strip()
        if(utterance == ""):
            utterance = "how to learn" # ugly shim, but this is all temporary as the model figured it out
    else:
        utterance = None
    #debug
    if app_set_debug_mode >= 2:
        print(f"-- wsl -- > shim_intuit_intent_learnskill > exit_method > '{utterance}'")

    return utterance

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
    if 'courses' in raw_text_query or 'catalog' in raw_text_query:
        search_provider = "catalogue.da-an.ca"
    #debug
    if app_set_debug_mode >= 2:
        print(f"-- wsl -- > shim_intuit_search_provider > exit_method > {search_provider}")

    return search_provider

def shim_weasel_translate_request(utterance):
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
        assist_hints['knock-common-words'] = True

    if assist_hints.get('knock-gov-speak', "") == "":
        assist_hints['knock-gov-speak'] = True

    # use them

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
    
    # shim for AI learning "search geds blah blah" or "contact blah blah"
    # AI seems to be learning to exclude items from the return
    # we should consider changing the entity to a custom one, or wit/search_query
    # the intent of our message subject here is in essence a query string we 
    # fire at the search provider.
    if ' geds ' in utterance or ' ' in utterance:
        assist_hints['knock-first-word'] = False
    

    # gov speak knockouts
    if assist_hints.get('knock-gov-speak') == True:
        out = ['contact','geds','GEDS','cra','CRA','canada.ca','busrides.ca','catalogue.da-an.ca']
        utterance = ' ' + utterance 
        for knock in out:
            utterance = utterance.replace(' '+knock+' ',' ')    
    #    assist_hints['knock-first-word'] = True        
    # knockouts
    if assist_hints.get('knock-first-word') == True:
        utterance = ' '.join(utterance.split()[1:])

    utterance = utterance.strip()

    # WARN: deep magic. burn deck. Remove when you've got a better AI model
    utterance = utterance.replace('T4','T4 Statement of Remuneration Paid (slip)')

    # diff search providers want different food
    if assist_hints.get('knock-space-with-dash') == True:
        utterance = utterance.replace(' ','-')

    if assist_hints.get('knock-pct20-with-dash') == True: 
        utterance = utterance.replace('%20','-') 

    #debug
    if app_set_debug_mode >= 2:
        print(f"-- wsl -- > shim_assist_weasel_comprehension > exit_method > {utterance} {assist_hints}")


    return utterance

def run_intuition_shims(q,response,run_check=True):
    if run_check == True:
        intuition_check = shim_intuit_search_provider( response['_text'] )
        if intuition_check is not None:
            q['topic_interest'] = intuition_check

        intuition_check = shim_intuit_intent_visualize( response['_text'] )
        if intuition_check is not None:
            q['intent'] = 'visualize'

        intuition_check = shim_intuit_intent_learnskill( response['_text'] )
        if intuition_check is not None:
            q['topic_interest'] = intuition_check.lower()

        if q['topic_interest'] == "busrides.ca":
            q['intent'] = 'search site' 
    return q
