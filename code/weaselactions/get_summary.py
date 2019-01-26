# over importing during quick dev, todo: clean imports to just the basics
from flask import (render_template, render_template_string, Markup, jsonify)
import json
from code.weasellib import wlib

app_set_debug_mode = 0 # 0 = off, 1 on, 2 in/out. 3 all

def weasel_act(valid_answer,response,runquery=True):
    json_ds = wlib.weasel_http_request( valid_answer['answer']['hyperlink'] )
    raw_json = Markup(json_ds)
    return render_template('weasel/weasel-summary.html', q=response['_text'], jsonds=raw_json )
