import click, os, sys, json
import slack_format
from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
from flask import Flask, make_response, Response, request
from yelp import YelpAPI
from flask_caching import Cache
from poll import Poll, Finalize, ReRoll
from Invoker_Options import send_invoker_options

##### SETUP
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple','CACHE_DEFAULT_TIMEOUT': 0}) # I heard 0 is the value for infinite
cache.set("invoked_ts", -1)
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
    #request.headers['X-Slack-No-Retry'] = 1
    return 'OK'

##### EVENT HANDLERS

# handles button press events, where only the votes will be handled
# and there can only exist one ongoing voting session (for now)
@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
  # Parse the request payload
  form_json = json.loads(request.form["payload"])
   # Check to see what the user's selection was and update the message
  user_id = form_json["user"]["id"]
  channel_id = form_json["channel"]["id"]
  callback_id = form_json["callback_id"]
  selection = form_json["actions"][0]["value"] 
  message_ts = form_json["message_ts"]
  votes_ts, votes_channel_id = get_votes_info()
  invoker_id, invoked_channel, invoked_ts = get_invoker_info()
  
  if callback_id == "vote" and message_ts == votes_ts:
    # this part handles vote buttons
    cache_votes(user_id, selection)
    
    poll = Poll(get_msg_attachments(), get_cached_votes())
    update_message(votes_channel_id, ts=votes_ts, **poll.get_updated_attachments())
  
  elif callback_id == "invoker_controls":
    if user_id != invoker_id:
      #slack_client.api_call("chat.postEphemeral", channel=channel_id, text="Only the poll creator can make changes to the poll.", user=user_id)
      print("Invoker:", invoker_id, "user:", user_id)
      return make_response("", 200)
    if selection == "finalize":
      # finalize votes
      cache_invoker_info(str(None), str(None), -1) # reset invoker info
      conclusion = Finalize.conclude(get_cached_votes())
      slack_client.api_call("chat.delete", channel=str(votes_channel_id), ts=votes_ts)
      slack_client.api_call("chat.postMessage", channel=str(invoked_channel), text=conclusion)
    elif selection == "reroll":
      # reroll votes
      pass
    elif selection == "cancel":
      # cancel votes
      cache_invoker_info(str(None), str(None), -1)
      cancel = Cancel.conclude(get_cached_votes())
      slack_client.api_call("chat.postMessage", channel=str(invoked_channel), text=cancel)
      
    
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
    print(event_data)
  return make_response("", 200)

# handles when bots name is mentioned
@slack_events_adapter.on("app_mention")
def bot_invoked(event_data):
    #print("Cached ts:", cache.get('timestamp'))
    print("called")
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
        search(channel)
        
        ret = send_invoker_options(user, channel, slack_client)
        cache_invoker_info(user, channel, ret["message_ts"])        

    return make_response("", 200)

def cache_ts(ts):
    cache.set(key='timestamp',value=ts)
    #print("Cached:", ts)
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

def cache_votes_info(ts, channel):
    cache.set("votes_timestamp", ts)
    cache.set("votes_channel", channel)

def get_votes_info():
    if not cache.get("votes_timestamp"):
        cache.set(key="votes_timestamp",value=0)
    return cache.get("votes_timestamp"), cache.get("votes_channel")
  
def cache_msg_attachments(msg_attachments):
    cache.delete("msg_attachments")
    cache.set("msg_attachments", msg_attachments)

def get_msg_attachments():
    if not cache.get("msg_attachments"):
        cache.set(key="msg_attachments",value={})
    return cache.get("msg_attachments")
  
def cache_invoker_info(invoker_id, invoked_channel, invoked_ts):
    cache.set("invoker_id", invoker_id)
    cache.set("invoked_channel", invoked_channel)
    cache.set("invoked_ts", invoked_ts)
    print("Cached Invoker id:",cache.get("invoker_id"),"channel:",cache.get("invoked_channel"),"ts:",cache.get("invoked_ts"))
def get_invoker_info():
    print("Getting Invoker id:",cache.get("invoker_id"),"channel:",cache.get("invoked_channel"),"ts:",cache.get("invoked_ts"))
    return cache.get("invoker_id"), cache.get("invoked_channel"), cache.get("invoked_ts")
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

def search(channel, term="lunch", location="pittsburgh, pa", limit=3):
  search_results = yelp_api.search(term, location, limit)

  restaurants_arr = []
  reviews_arr = []
  for res in search_results["businesses"]:
    restaurant_id = res["id"]
    restaurants_arr.append(yelp_api.get_business(restaurant_id))
    reviews_arr.append(yelp_api.get_reviews(restaurant_id))
  msg = slack_format.build_vote_message(restaurants_arr, reviews_arr)
  
  votes_ts, votes_channel_id = get_votes_info()  
  invoker_id, invoked_channel, invoked_ts = get_invoker_info()
  cache_msg_attachments(msg)  
  slack_client.api_call("chat.delete", channel=str(votes_channel_id), ts=votes_ts)
  # ephemeral messages cannot be deleted (by the bot at least) will use the invoker id to check when someone
  # wants to finalize/reroll/cancel the voting session
  # print(slack_client.api_call("chat.delete", channel=str(invoked_channel), ts=invoked_ts)) 

  ret = send_message(channel, **msg)
  cache_votes_info(ret["ts"], ret["channel"])