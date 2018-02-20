from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
from flask import Flask, request
import click, os, sys
import json, datetime

# import an environment variable as an app config option
# throws KeyError
def import_env_var(app, env_var):
  app.config[env_var] = os.environ[env_var]


app = Flask(__name__)

try:
  import_env_var(app, "SLACK_BOT_TOKEN")
  import_env_var(app, "SLACK_VERIFICATION_TOKEN")
except KeyError:
  click.echo("Could not load environment variables")
  sys.exit()

slack_client = SlackClient(app.config["SLACK_BOT_TOKEN"])
slack_events_adapter = SlackEventAdapter(app.config["SLACK_VERIFICATION_TOKEN"], endpoint="/slack/events", server=app)

# requires 'message' scope
@slack_events_adapter.on("message")
def handle_message(event_data):
  click.echo("Received a message")
  click.echo(event_data)
  message = event_data["event"]
  if message.get("subtype") is None and "hello" in message.get('text'):
    channel = message["channel"]
    msg = "Hi <@%s>! :simple_smile:" % message["user"]
    click.echo('Attempting to post:' + msg)
    send_message(channel, text=msg)

# send a message to channel
# uses keyword args to expand message
# for simple messages, use send_message(channel, text="simple message")
# for dict/formatted messages, use send_message(channel, **msg)
def send_message(channel, **msg):
  slack_client.api_call("chat.postMessage", channel=channel, msg)

# fetches a restaurant from Yelp based on its id
def fetch_restaurant(id):
  return {}

# takes in a response from the Yelp API, nicely formats a restaurant with relevant info
# TODO: use the stars that Yelp requires 
def get_restaurant(res):  
  name = res["name"]
  link = res["url"]
  price = res["price"]
  image = res["image_url"]
  rating = "\u2605" * int(res["rating"]) + "\u2606" * (5 - int(res["rating"]))

  weekday = datetime.datetime.today().weekday()
  endtime = res["hours"]["open"][weekday]["end"]
  time = (int(endtime[:2]) % 12) + ":" + endtime[2:]

  desc = ""
  review = ""
  address = ""
  nav_link = ""