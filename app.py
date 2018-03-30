import click, os, sys, json, ast
import psycopg2
import slack_format, static_messages
import slackclient, slackeventsapi, yelp
from flask import Flask, make_response, Response, request
from poll import Poll, Finalize, ReRoll
from database import AccessVotes, AccessInvoker, AccessBusinessIDs, AccessGeneral, AccessPoll
from functools import wraps
from command_line import parse_command, send_help


##### SETUP
app = Flask(__name__)
env_vars = ["SLACK_BOT_TOKEN", "SLACK_VERIFICATION_TOKEN", "YELP_API_KEY", "DATABASE_URL"]

for var in env_vars:
    try:
        app.config[var] = os.environ[var]
    except KeyError:
        print("Could not load environment variable {}".format(var))
        sys.exit()

slack_client = slackclient.SlackClient(app.config["SLACK_BOT_TOKEN"])
slack_events_adapter = slackeventsapi.SlackEventAdapter(app.config["SLACK_VERIFICATION_TOKEN"], endpoint="/slack/events", server=app)
yelp_api = yelp.YelpAPI(app.config["YELP_API_KEY"])
db_conn = psycopg2.connect(app.config["DATABASE_URL"])

# wrapper to filter out retries
def reject_repeats(f1):
    @wraps(f1)
    def f2(*args, **kwargs):
        if "X-Slack-Retry-Num" in request.headers and int(request.headers["X-Slack-Retry-Num"]) > 1:
            print("Caught and blocked a retry - retry reason ({})".format(request.headers["X-Slack-Retry-Reason"]))
            return okay()
        return f1(*args, **kwargs)
    return f2

# builds okay response with no-retry header
def okay():
    res = make_response("", 200)
    res.headers["X-Slack-No-Retry"] = 1
    return res


##### EVENT HANDLERS

# handles button press events, where only the votes will be handled
# and there can only exist one ongoing voting session (for now)
@app.route("/slack/message_actions", methods=["POST"])
@reject_repeats
def message_actions():
    # Parse the request payload
    form_json = json.loads(request.form["payload"])
    # Check to see what the user's selection was and update the message
    user_id = form_json["user"]["id"]
    channel_id = form_json["channel"]["id"]
    callback_id = form_json["callback_id"]
    selection = form_json["actions"][0]["value"]
    message_ts = form_json["message_ts"]

    vote_con = AccessVotes(channel_id, db_conn)
    invoker_con = AccessInvoker(channel_id, db_conn)
    bid_con = AccessBusinessIDs(channel_id, db_conn)
    general_con = AccessGeneral(channel_id, db_conn)

    print("callback_id=", callback_id)

    if callback_id == "vote" and float(message_ts) == float(vote_con.get_votes_ts()):
        # this part handles vote buttons
        #print("Updating votes")
        vote_con.set_user_votes(user_id, selection)
        #print("updated votes:", vote_con.get_user_votes())
        poll = Poll(vote_con.get_msg_attachments(), vote_con.get_user_votes())
        update_message(channel_id, ts=vote_con.get_votes_ts(), **poll.get_updated_attachments())

    elif callback_id == "busy_message":
        if float(invoker_con.get_invoker_ts()) > 0:
            # if there are values to delete (if there exists an ongoing poll)
            slack_client.api_call("chat.postMessage", channel=str(channel_id), text="Voting session revoked.")
            slack_client.api_call("chat.delete", channel=str(channel_id), ts=vote_con.get_votes_ts())
            invoker_con.delete()
            vote_con.delete()
            bid_con.delete()

    elif callback_id == "invoker_controls":
        if user_id != invoker_con.get_invoker_id():
            print("Invoker:", invoker_con.get_invoker_id(), "user:", user_id)
            return okay()

        if selection == "finalize":
            # finalize votes
            all_restaurants_dict = extract_restaurants_from_attachments(vote_con.get_msg_attachments())
            conclusion, winner = Finalize.conclude(vote_con.get_user_votes(), all_restaurants_dict)
            slack_client.api_call("chat.delete", channel=channel_id, ts=vote_con.get_votes_ts())
            slack_client.api_call("chat.postMessage", channel=channel_id, text=conclusion)
            if winner:
                #slack_client.api_call("chat.postMessage", channel=channel_id, text="The chosen winner is: {}".format(winner))
                print_winner(channel_id, winner)
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
                slack_client("chat.postMessage", channel=channel_id, text="There are no more restaurants to reroll.")
                # don't make any modification to the current poll
                return okay()
            else:
                # when there are more than 3 ids left
                list_of_ids, business_ids = ReRoll(business_ids).reroll()
                bid_con.set_business_ids(business_ids)
            # wipes out all votes
            vote_con.reset_user_votes()

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
            slack_client.api_call("chat.postMessage", channel=str(channel_id), text="Voting session canceled")
            slack_client.api_call("chat.delete", channel=str(channel_id), ts=vote_con.get_votes_ts())
            invoker_con.delete()
            vote_con.delete()
            bid_con.delete()

    return okay()


# handles when bots name is mentioned
@slack_events_adapter.on("app_mention")
@reject_repeats
def bot_invoked(event_data):
    message = event_data["event"]

    if message.get("subtype") is None and not message.get("text") is None:
        text = message["text"]
        channel_id = message["channel"]
        user = message["user"]

        vote_con = AccessVotes(channel_id, db_conn)
        invoker_con = AccessInvoker(channel_id, db_conn)
        bid_con = AccessBusinessIDs(channel_id, db_conn)
        general_con = AccessGeneral(channel_id, db_conn)

        invoker_id = invoker_con.get_invoker_id()
        invoked_channel = channel_id
        invoked_ts = invoker_con.get_invoker_ts()

        if not general_con.validate_timestamp(message["ts"]):
            # the received message either has old timestamp or the same value as the current stored one
            print("Received message too old!")
            return okay()

        command_info = parse_command(text)
        ap_con = AccessPoll(channel_id, db_conn)

        if command_info["type"] == "location":
            slack_client.api_call("chat.postMessage", channel=channel_id, text="Location has been set to {}".format(command_info["location"]))
            ap_con.create_poll_info(locations=command_info["location"])

        elif command_info["type"] == "poll":
            # don't proceed if there's an ongoing poll
            if invoked_ts != None and float(invoked_ts) > 0:
                print("There is an ongoing poll")
                static_messages.send_busy_message(invoked_channel, slack_client)
                return okay()
            # renew the terms value if any
            ap_con.create_poll_info(terms=command_info["terms"])
            terms = ap_con.get_terms()
            location = ap_con.get_locations()
            # send the searching indication message
            slack_client.api_call("chat.postMessage", channel=channel_id, text="Searching for {} in {}...".format(terms, location))
            # send the actual search with options and buttons
            search(channel_id, term=terms, location=location)
            # set the message timestamp value
            general_con.create_general_info(message["ts"])
            ret = static_messages.send_invoker_options(user, channel_id, slack_client)
            invoker_con.create_invoker_info(user, ret["message_ts"])
        else:
            send_help(channel_id=channel_id, slack_client=slack_client)

    return okay()

##### HELPERS

# send a message to channel
# uses keyword args to expand message
# for simple messages, use send_message(channel, text="simple message")
# for dict/formatted messages, use send_message(channel, **msg)
def send_message(channel, **msg):
    return slack_client.api_call("chat.postMessage", channel=channel, **msg)

def update_message(channel, ts, **msg):
    return slack_client.api_call("chat.update", channel=channel, ts=ts, **msg)

def search(channel, term="lunch", location="pittsburgh, pa"):
    vote_con = AccessVotes(channel, db_conn)
    invoker_con = AccessInvoker(channel, db_conn)
    bid_con = AccessBusinessIDs(channel, db_conn)
    general_con = AccessGeneral(channel, db_conn)

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

def print_winner(channel, winner_id):
    #arrays used to pass into the format_restaurant method
    winner_arr = []
    winner_review = []

    #winner_id used for identifying which resturant to display
    #build the arrays to pass into printing the new message
    winner_arr.append(yelp_api.get_business(winner_id))
    winner_review.append(yelp_api.get_reviews(winner_id))

    #print the new message
    msg = slack_format.build_normal_message(winner_arr, winner_review)
    return send_message(channel, **msg)
    
def extract_restaurants_from_attachments(att=""):
    try:
        ret = ast.literal_eval(str(att))
        names = list(r['actions'][0]['name'] for r in ret['attachments'])
        ids = list(r['actions'][0]['value'] for r in ret['attachments'])
        return {k:v for k,v in zip(ids, names)}
    except:
        print("failed to extract")
