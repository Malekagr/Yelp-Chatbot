import click, os, sys, json
import slack_format
from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
from flask import Flask, make_response, Response, request
from yelp import YelpAPI


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
except KeyError:
  click.echo("Could not load environment variables")
  sys.exit()

slack_client = SlackClient(app.config["SLACK_BOT_TOKEN"])
slack_events_adapter = SlackEventAdapter(app.config["SLACK_VERIFICATION_TOKEN"], endpoint="/slack/events", server=app)
yelp_api = YelpAPI(app.config["YELP_API_KEY"])


##### EVENT HANDLERS

# handles button press events
@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
  # Parse the request payload
  form_json = json.loads(request.form["payload"])

  # Check to see what the user's selection was and update the message
  selection = form_json["actions"][0]["value"]
  message_text = "<@{0}> selected {1}".format(form_json["user"]["id"], selection)

  send_message(channel=form_json["channel"]["id"], text=message_text)
  return make_response("", 200)

# requires 'message' scope
@slack_events_adapter.on("message")
def handle_message(event_data):
  message = event_data["event"]
  if message.get("subtype") is None and not message.get("text") is None:
    text = message["text"]
    channel = message["channel"]
    user = message["user"]

    #click.echo("Received message '{}' from '{}' in '{}'".format(text, user, channel))
    print(event_data) # will change this back if click.echo wasn't the problem
    if "hello" in text:
      send_message(channel, text="Hi <@%s>! :simple_smile:" % user)

    if "botsearch" in text:
      search(channel)

  return make_response("", 200)

##### HELPERS

# send a message to channel
# uses keyword args to expand message
# for simple messages, use send_message(channel, text="simple message")
# for dict/formatted messages, use send_message(channel, **msg)
def send_message(channel, **msg):
  slack_client.api_call("chat.postMessage", channel=channel, **msg)

def search(channel):
  search_results = yelp_api.search("lunch", "pittsburgh, pa", 3)

  restaurants_arr = []
  reviews_arr = []
  for res in search_results["businesses"]:
    restaurant_id = res["id"]
    restaurants_arr.append(yelp_api.get_business(restaurant_id))
    reviews_arr.append(yelp_api.get_reviews(restaurant_id))

  send_message(channel, **slack_format.build_vote_message(restaurants_arr, reviews_arr))
