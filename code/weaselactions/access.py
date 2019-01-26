# over importing during quick dev, todo: clean imports to just the basics
from flask import (redirect)

app_set_debug_mode = 0 # 0 = off, 1 on, 2 in/out. 3 all

def weasel_act(valid_answer,response,runquery=True):
    return redirect( valid_answer['answer']['hyperlink'] )