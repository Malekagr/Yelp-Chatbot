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
  message = event_data["event"]
  if message.get("subtype") is None:
    channel = message["channel"]
    user = message["user"]

    if "hello" in message.get('text'):
      send_message(channel, text="Hi <@%s>! :simple_smile:" % user)

    if "idsearch" in message.get('text'):
      idterm = message.get('text').split()[-1]
      restaurant = get_restaurant(idterm)
      reviews = get_reviews(idterm)

      send_message(channel, format_restaurant(restaurant, reviws))

# send a message to channel
# uses keyword args to expand message
# for simple messages, use send_message(channel, text="simple message")
# for dict/formatted messages, use send_message(channel, **msg)
def send_message(channel, **msg):
  slack_client.api_call("chat.postMessage", channel=channel, msg)

# uses the Yelp API to search for a restaurant based on ID
def get_restaurant(id):
  return {}

# uses the Yelp API to search for reviews based on ID
def get_reviews(id):
  return {}

# takes in the result of 2 Yelp API calls
# nicely formats a restaurant with relevant info
# TODO: use the stars that Yelp requires
def format_restaurant(restaurant, reviews):
  # we need a name and URL no matter what
  if not ("name" in restaurant and "url" in restaurant):
    return {"text": "Could not format"}
  name = restaurant["name"]
  link = restaurant["url"]

  # price with fallback
  price = "Unknown Price"
  if "price" in restaurant:
    price = restaurant["price"]

  # image with fallback
  image = ""
  if "image" in restaurant:
    image = restaurant["image_url"]

  # get star rating
  # TODO: Yelp requires us to use specific star icons
  rating = "Unknown Rating"
  if "rating" in restaurant:
    rating = "\u2605" * int(restaurant["rating"]) + "\u2606" * (5 - int(restaurant["rating"]))

  # get today's closing time
  time = "Unknown Time"
  if "time" in restaurant:
    weekday = datetime.datetime.today().weekday()
    endtime = restaurant["hours"][0]["open"][weekday]["end"]
    time = endtime[:2] + ":" + endtime[2:]

  # get categories
  desc = "result"
  if "categories" in restaurant and len(restaurant["categories"]) > 0:
    desc = "/".join(map((lambda cat: cat["title"]), restaurant["categories"]))

  # get review snippet
  snippet = ""
  if "reviews" in reviews and len(reviews["reviews"]) > 0:
    snippet = reviews["reviews"][0]["text"]

  # get address
  address = "Unknown Address"
  if "location" in restaurant and "display_address" in restaurant["location"]:
    address = ", ".join(restaurant["location"]["display_address"])

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

  return formatted