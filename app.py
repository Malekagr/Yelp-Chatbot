import click, os, sys, json
from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
from flask import Flask, make_response, Response, request
import psycopg2

import slack_format
from yelp import YelpAPI
from poll import Poll, Finalize, ReRoll
from Invoker_Options import send_invoker_options
from Access_Database import Access_Votes, Access_Invoker, Access_Business_IDs, Access_General

##### SETUP
app = Flask(__name__)

# import an environment variable as an app config option
# throws KeyError
def import_env_var(app, env_var):
    app.config[env_var] = os.environ[env_var]

try:
    import_env_var(app, "SLACK_BOT_TOKEN")
    import_env_var(app, "SLACK_VERIFICATION_TOKEN")
    import_env_var(app, "YELP_API_KEY")
    import_env_var(app, "DATABASE_URL")
except KeyError:
    print("Could not load environment variables")
    sys.exit()

slack_client = SlackClient(app.config["SLACK_BOT_TOKEN"])
slack_events_adapter = SlackEventAdapter(app.config["SLACK_VERIFICATION_TOKEN"], endpoint="/slack/events", server=app)
yelp_api = YelpAPI(app.config["YELP_API_KEY"])
db_conn = psycopg2.connect(app.config["DATABASE_URL"])

@app.route("/", methods=["POST", "GET"])
def hello():
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
    
    vote_con = Access_Votes(channel_id)
    invoker_con = Access_Invoker(channel_id)
    bid_con = Access_Business_IDs(channel_id)
    general_con = Access_General(channel_id)
  
    if callback_id == "vote" and float(message_ts) == float(vote_con.get_votes_ts()):
        # this part handles vote buttons
        #print("Updating votes")
        vote_con.set_user_votes(user_id, selection)
        print("updated votes:", vote_con.get_user_votes())
        poll = Poll(vote_con.get_msg_attachments(), vote_con.get_user_votes())
        print(update_message(channel_id, ts=vote_con.get_votes_ts(), **poll.get_updated_attachments()))
  
    elif callback_id == "invoker_controls":
        if user_id != invoker_con.get_invoker_id():
            print("Invoker:", invoker_con.get_invoker_id(), "user:", user_id)
            return make_response("", 200)
    
        if selection == "finalize":
          # finalize votes
            conclusion = Finalize.conclude(vote_con.get_user_votes())
            print("user_votes=", vote_con.get_user_votes())
      
            print(slack_client.api_call("chat.delete", channel=str(channel_id), ts=vote_con.get_votes_ts()))
            slack_client.api_call("chat.postMessage", channel=channel_id, text=conclusion)
            invoker_con.delete()
            vote_con.delete()
            bid_con.delete()

        elif selection == "reroll":
          # reroll votes
            business_ids = bid_con.get_business_ids()
            if len(business_ids) < 3 and len(business_ids) > 0:
                list_of_ids = business_ids
                bid_con.set_business_ids([])
            elif len(business_ids) <= 0:
                print("out of ids")
                # don't make any modification to the current poll
                return make_response("", 200)
            else:
                # when there are more than 3 ids left
                list_of_ids, business_ids = ReRoll(business_ids).reroll()  
                bid_con.set_business_ids(business_ids)
        
            restaurants_arr = []
            reviews_arr = []
            for restaurant_id in list_of_ids:
                restaurants_arr.append(yelp_api.get_business(restaurant_id))
                reviews_arr.append(yelp_api.get_reviews(restaurant_id))
            msg = slack_format.build_vote_message(restaurants_arr, reviews_arr) 
  
            vote_con.set_msg_attachments(msg)
            ret = update_message(channel_id, vote_con.get_votes_ts(), **msg)
        
        elif selection == "cancel":
            # cancel voting session
            print("user_votes=", vote_con.get_user_votes())
            slack_client.api_call("chat.postMessage", channel=str(channel_id), text="Voting session canceled")
            print("Attempting to delete message at", vote_con.get_votes_ts(), "in", channel_id)
            slack_client.api_call("chat.delete", channel=str(channel_id), ts=vote_con.get_votes_ts())
            invoker_con.delete()
            vote_con.delete()
            bid_con.delete()
    return make_response("", 200)

# requires 'message' scope
@slack_events_adapter.on("message")
def handle_message(event_data):
    message = event_data["event"]
    if message.get("subtype") is None and not message.get("text") is None:
        #ts = get_ts()
        text = message["text"]
        channel_id = message["channel"]
        user = message["user"]
        #general_con = Access_General(channel_id)
        #general_con.set_ts(message["ts"])
        print(event_data)
    return make_response("", 200)

# handles when bots name is mentioned
@slack_events_adapter.on("app_mention")
def bot_invoked(event_data):
    message = event_data["event"]

    if message.get("subtype") is None and not message.get("text") is None:        
        text = message["text"]
        channel_id = message["channel"]
        user = message["user"]
        search(channel_id)
    
        vote_con = Access_Votes(channel_id)
        invoker_con = Access_Invoker(channel_id)
        bid_con = Access_Business_IDs(channel_id)
        general_con = Access_General(channel_id)
    
        invoker_id = invoker_con.get_invoker_id()
        invoked_channel = channel_id
        invoked_ts = invoker_con.get_invoker_ts()
    
        if invoked_ts != None and float(invoked_ts) > 0:
            pass
            #print("There is an ongoing poll")
            #slack_client.api_call("chat.postMessage", channel=str(invoked_channel), text="I'm busy right now, call me once the current poll is finished.")
            #return make_response("", 200)
    
        if not general_con.validate_timestamp(message["ts"]):
            # the received message either has old timestamp or the same value as the current cached one
            print("Received message too old!")
            return make_response("", 200)
    
        general_con.create_general_info(message["ts"])
        ret = send_invoker_options(user, channel_id, slack_client)
        invoker_con.create_invoker_info(user, ret["message_ts"]) 

    return make_response("", 200)

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

def search(channel, term="lunch", location="pittsburgh, pa"):
    vote_con = Access_Votes(channel)
    invoker_con = Access_Invoker(channel)
    bid_con = Access_Business_IDs(channel)
    general_con = Access_General(channel)
        
    business_ids = bid_con.get_business_ids()
    if not business_ids:
        limit = 50      # 50 is the maximum we can request for
        search_results = yelp_api.search(term, location, limit)
        business_ids = [res["id"] for res in search_results["businesses"]]
    
    partial_ids, business_ids = ReRoll(business_ids).reroll()  
    bid_con.create_business_ids(business_ids)
    
    restaurants_arr = []
    reviews_arr = []
    for restaurant_id in partial_ids:
        restaurants_arr.append(yelp_api.get_business(restaurant_id))
        reviews_arr.append(yelp_api.get_reviews(restaurant_id))
    msg = slack_format.build_vote_message(restaurants_arr, reviews_arr)  
    
    ret = send_message(channel, **msg)
    vote_con.create_votes_info(str(ret["ts"]), msg)
