import click, os, sys, json
import slack_format
from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
from flask import Flask, make_response, Response, request
from yelp import YelpAPI
from flask_caching import Cache
from poll import Poll

##### SETUP
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# import an environment variable as an app config option
# throws KeyError
def import_env_var(app, env_var):
  app.config[env_var] = os.environ[env_var]

try:
  import_env_var(app, "SLACK_BOT_TOKEN")
  import_env_var(app, "SLACK_VERIFICATION_TOKEN")
  import_env_var(app, "YELP_API_KEY")
except KeyError:
  click.echo("Could not load environment variables")
  sys.exit()

slack_client = SlackClient(app.config["SLACK_BOT_TOKEN"])
slack_events_adapter = SlackEventAdapter(app.config["SLACK_VERIFICATION_TOKEN"], endpoint="/slack/events", server=app)
yelp_api = YelpAPI(app.config["YELP_API_KEY"])

@app.route("/", methods=["POST", "GET"])
def hello():
    return 'OK'

##### EVENT HANDLERS

# handles button press events
@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
  # Parse the request payload
  form_json = json.loads(request.form["payload"])
  #print(form_json)

  # Check to see what the user's selection was and update the message
  selection = form_json["actions"][0]["value"]
  
  cache_votes(form_json["user"]["id"], selection)
  poll = Poll(get_msg_attachments(), get_cached_votes())
  update_message(form_json["channel"]["id"], ts=get_votes_ts(), **poll.get_updated_attachments())
  
  message_text = "<@{0}> selected {1}".format(form_json["user"]["id"], selection)
  print(message_text)
  return make_response("", 200)

# requires 'message' scope
@slack_events_adapter.on("message")
def handle_message(event_data):
  message = event_data["event"]
  if message.get("subtype") is None and not message.get("text") is None:
    #ts = get_ts()
    text = message["text"]
    channel = message["channel"]
    user = message["user"]
    #cache_ts(message["ts"])

    print(event_data)
    if "hello" in text:
      send_message(channel, text="Hi <@%s>! :simple_smile:" % user)
  return make_response("", 200)

# handles when bots name is mentioned
@slack_events_adapter.on("app_mention")
def bot_inovked(event_data):
    message = event_data["event"]
    if not validate_timestamp(message["ts"]):
    # the received message either has old timestamp or the same value as the current cached one
        print("Received message too old!")
        return make_response("", 200)
    cache_ts(message["ts"])
    
    if message.get("subtype") is None and not message.get("text") is None:
        text = message["text"]
        channel = message["channel"]
        user = message["user"]
        if "botsearch" in text:
            search(channel)
        else:
            send_message(channel, text="What's up @<{0}>! :simple_smile:".format(user))
    return make_response("", 200)

# timestamp caching function
def cache_ts(ts):
    #cache.update([('timestamp', ts)])
    cache.set(key='timestamp',value=ts)
    print("Cached:", ts)
    return ts
  
def get_ts():
    ts = cache.get('timestamp')
    if ts is None or ts is str(None):
        return 0
    return float(ts) # returns as an integer
  
def validate_timestamp(cur_ts):
    cur_ts = float(cur_ts)
    past = get_ts()
    print('PAST:', past,'CURRENT:',cur_ts)
    if cur_ts <= past:
        return False
    return True

def cache_votes(user_id, vote):    
    votes = get_cached_votes()
    votes[user_id] = vote
    cache.set(key='votes',value=votes)
    
def get_cached_votes():
    if not cache.get("votes"):
        # if votes hasn't been initialized
        cache.set(key="votes",value={})
    return cache.get("votes")
  
def cache_votes_ts(ts):
    cache.set(key='votes_timestamp',value=ts)
def get_votes_ts():
    if not cache.get("votes_timestamp"):
        cache.set(key="votes_timestamp",value=0)
    return cache.get("votes_timestamp")
def cache_msg_attachments(msg_attachments):
    cache.set(key='msg_attachments',value=msg_attachments)
def get_msg_attachments():
    if not cache.get("msg_attachments"):
        cache.set(key="msg_attachments",value={})
    return cache.get("msg_attachments")
##### HELPERS

# send a message to channel
# uses keyword args to expand message
# for simple messages, use send_message(channel, text="simple message")
# for dict/formatted messages, use send_message(channel, **msg)
def send_message(channel, **msg):
  return slack_client.api_call("chat.postMessage", channel=channel, **msg)
def update_message(channel, ts, **msg):
  print("Trying to update at ts=", ts)
  return slack_client.api_call("chat.update", channel=channel, ts=ts, **msg)
def search(channel):
  search_results = yelp_api.search("lunch", "pittsburgh, pa", 3)

  restaurants_arr = []
  reviews_arr = []
  for res in search_results["businesses"]:
    restaurant_id = res["id"]
    restaurants_arr.append(yelp_api.get_business(restaurant_id))
    reviews_arr.append(yelp_api.get_reviews(restaurant_id))
  msg = slack_format.build_vote_message(restaurants_arr, reviews_arr)
  cache_msg_attachments(msg)
  ret = send_message(channel, **msg)
  cache_votes_ts(ret["ts"])
