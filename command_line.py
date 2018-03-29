def send_help(channel_id, slack_client, bot_name="yelp_chatbot"):
    bot_id = get_bot_id(slack_client, bot_name)
    displayed_bot_name = "@{}".format(bot_name) if bot_id is None else "<@{}>".format(bot_id)
    msg = '''
    Hi! I'm the {0}. I can be used to search for local restaurants and help your group decide where to get food.
        •`{0} location city/zip-code/address` *sets the location* for a channel.
        •`{0} help` will display this *help message.*
        •`{0} poll [search terms, optional]` will *start a poll.*
    '''.format(displayed_bot_name)
    slack_client.api_call("chat.postMessage", channel=channel_id, text=msg)

def get_bot_id(slack_client, bot_name="yelp_chatbot"):
    ret=slack_client.api_call("users.list")
    try:
        bot_id = list(r for r in ret["members"] if r["name"] == bot_name)[0]["id"]
        return bot_id
    except:
        return None

def parse_command(msg=""):
    tokens = msg.split()
    ret = {"type":"none"}
    if len(tokens) < 2:
        return ret
    if tokens[1] == "location" and len(tokens) > 2:
        ret["type"] = "location"
        ret["location"] = ' '.join(tokens[2:]) if len(tokens) > 2 else "pittsburgh, pa"
        ret["bot"] = tokens[0]
    elif tokens[1] == "poll":
        ret["type"] = "poll"
        ret["terms"] = ' '.join(tokens[2:]) if len(tokens) > 2 else ""
        ret["bot"] = tokens[0]
    else:
        ret["type"] = "help"
        ret["text"] = ""
        ret["bot"] = tokens[0]
    return ret
