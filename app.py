import os
from flask import Flask, request, abort, make_response
import configparser

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

from linebot.models import *
from Access_Database import Access_Leaders

import requests
import json

app = Flask(__name__)
config = configparser.ConfigParser()
config.read("config.ini")

line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
handler = WebhookHandler(config['line_bot']['Channel_Secret'])

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(event)
    # line_bot_api.reply_message(event.reply_token, TextSendMessage(text=event.message.text))
    msg = event.message.text
    if msg[0] != "!":
        return make_response("", 200)
    if event.source.type == "room":
        r_token = event.source.room_id # should've named room id, which is unique
    else:
        r_token = event.source.user_id
    al_con = Access_Leaders(r_token)
    al_con.create_leaders_list()
    tokens = msg.split(" ")
    reply_msg = ""
    if len(tokens) >= 2 and tokens[0].lower() == "!add":
        leader_name = ' '.join(tokens[1:])
        al_con.add_leader(leader_name)
        reply_msg = "{}'s leader now has been caught {} time(s)".format(leader_name, al_con.get_leader_lost_count(leader_name))
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_msg))
        
    elif len(tokens) >= 2 and tokens[0].lower() == "!sub":
        leader_name = ' '.join(tokens[1:])
        al_con.sub_leader(leader_name)
        reply_msg = "{}'s leader now has been caught {} time(s)".format(leader_name, al_con.get_leader_lost_count(leader_name))
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_msg))
        
    elif len(tokens) >= 2 and tokens[0].lower() == "!get":
        leader_name = ' '.join(tokens[1:])
        reply_msg = "{}'s leader has been caught {} time(s)".format(leader_name, al_con.get_leader_lost_count(leader_name))
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_msg))
        
    elif msg.rstrip().lower() == "!getall":
        d = al_con.get_leader_dict()
        reply_msg = ""
        for k,v in d.items():
            reply_msg += "{}'s leader has been caught {} time(s)\n".format(k, v)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_msg))
        
    elif len(tokens) >= 2 and tokens[0].lower() == "!delete":
        leader_name = ' '.join(tokens[1:])
        al_con.delete_leader(leader_name)
        reply_msg = "Removed {} from the list".format(leader_name)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_msg))
        
    elif len(tokens) >= 2 and tokens[0].lower() == "!set":
        leader_name = ' '.join(tokens[1:-1])
        try:
            count = int(tokens[-1])
            al_con.set_leader_count(leader_name, count)
            reply_msg = "{}'s leader now has been caught {} time(s)".format(leader_name, al_con.get_leader_lost_count(leader_name))
        except:            
            reply_msg = "Invalid number"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_msg))
        
    elif msg.rstrip().lower() == "!help":
        reply_msg = get_help_message()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_msg))
    return make_response("", 200)

def get_help_message():
    help_msg = '''
    HELP MENU
    !add <name> : adds 1 leader caught count under the <name>
    !sub <name> : subtracts 1 leader caught count under the <name>
    !delete <name> : removes <name> from the list
    !set <name> <count> : directly sets caught count to <count>
    !get <name> : gets the caught count of <name>
    !getall : lists out everyone's count
    !help : to bring up this menu
    '''
    return help_msg

if __name__ == "__main__":
    app.run()
