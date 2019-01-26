from wit import Wit
import json
import requests
# Python 2/3 imports changed, the dot is required it seems

weasel_all_selector = "*"
weasel_core_authority_selector = "core"
weasel_data_folder = "static/data/can-live/"


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


# make the html fragment (consider a better solution, template string) something
# like html_snippet = render_template_string('hello {{ what }}', what='world')
def generate_weasel_linktile_html(hyperlink):
    #html_tile_snippet = "" \
    #    +"<a href='|h|' data-size='|s|' data-role='tile' class='bg-|c| ani-hover-bounce'>" \
    #        +"<span class='mif-|i| icon'></span> " \
    #        +"<span class='badge-top'>(|v|)</span>" \
    #        +"<span class='branding-bar'>|n|</span>" \
    #    +"</a>"
    html_tile_snippet = "" \
        +"<p><a href='|h|' style='background-color:#cccccc;'>" \
            +"<span class='mif-|i| icon'></span> " \
            +"<span>|n|</span> " \
            +"<span class='badge-top'>(|v|)</span> " \
        +"</a></p>"

    html_tile_snippet = html_tile_snippet.replace("|n|",hyperlink.replace("/","/ ").replace("-"," ").replace("_"," "))
    html_tile_snippet = html_tile_snippet.replace("|h|",hyperlink)
    html_tile_snippet = html_tile_snippet.replace("|i|","link")
    html_tile_snippet = html_tile_snippet.replace("|c|","red")
    html_tile_snippet = html_tile_snippet.replace("|s|","small")
    html_tile_snippet = html_tile_snippet.replace("|v|","Human Curated")
    return html_tile_snippet


def generate_weasel_answer_html(ans):
    written = ""
    written_lines = ans['answer']['written'].splitlines()
    for wl in written_lines:
        written += "<p>" + wl + "</p>"

    links = ans['answer']['hyperlink']
    if isinstance(links,list):
        html_link_tiles_snippet = ""
        for link in ans['answer']['hyperlink']:
            html_link_tiles_snippet += generate_weasel_linktile_html( link['hyperlink'] )
        links = html_link_tiles_snippet
    
    html_snippet = "" \
        + "<div class='container weasel_answer_reply'>" \
            + "<div id='weasel_spoken'>"+ans['answer']['spoken']+"</div>" \
            + "<div class='weasel_written'><strong><span class='mif-bubble'></span> In short:</strong></div>"\
            + "<p>" + written + "</p>" \
            + "<div><strong><span class='mif-link'></span>Actually Helpful Link(s):</strong></div>" \
            + links \
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
