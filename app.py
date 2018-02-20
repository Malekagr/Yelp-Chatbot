from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
from flask import Flask, request
import click, os, sys
import json, datetime, urllib.parse

sidebar_color = "#D01010"
footer = "YelpBot"
footer_icon = "https://www.yelp.com/favicon.ico"

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

# takes in a Yelp ID, nicely formats a restaurant with relevant info
# TODO: use the stars that Yelp requires 
def format_restaurant(id):
  res = json.load(open("testres.json")) # get from Yelp
  reviews = json.load(open("testreviews.json")) # get from Yelp

  # get name, url, price, an image
  name = res["name"]
  link = res["url"]
  price = res["price"]
  image = res["image_url"]

  # get star rating
  # TODO: Yelp requires us to use specific star icons
  rating = "\u2605" * int(res["rating"]) + "\u2606" * (5 - int(res["rating"]))

  # get today's closing time
  weekday = datetime.datetime.today().weekday()
  endtime = res["hours"][0]["open"][weekday]["end"]
  time = endtime[:2] + ":" + endtime[2:]

  # get categories
  desc = "result"
  if "categories" in res and len(res["categories"]) > 0:
    desc = "/".join(map((lambda cat: cat["title"]), res["categories"]))

  # get review snippet
  snippet = ""
  if "reviews" in reviews and len(reviews["reviews"]) > 0:
    snippet = reviews["reviews"][0]["text"]

  # get address
  address = ", ".join(res["location"]["display_address"])

  # get a link for navigation
  maps_api = "https://www.google.com/maps/search/?api=1&"
  nav_link = maps_api + urllib.parse.urlencode({"query": address})

  # now we BUILD!
  formatted = {}
  formatted["text"] = "I found {}! ({})".format(name, desc)
  restaurant = {}
  attachments = [restaurant]
  formatted["attachments"] = attachments
  restaurant["fallback"] = name
  restaurant["color"] = sidebar_color
  restaurant["author_name"] = rating
  restaurant["author_link"] = link
  restaurant["title"] = name
  restaurant["title_link"] = link
  restaurant["text"] = snippet
  restaurant["thumb_url"] = image
  restaurant["footer"] = footer
  restaurant["footer_icon"] = footer_icon
  restaurant["fields"] = [{"title": "Open today until {} / {}".format(time, price)}]

  print(formatted)