# You would need to download slackclient first
# In command line: pip install slackclient
# https://pypi.python.org/pypi/slackclient

# This shows an example of sending a message to Slack

from slackclient import SlackClient
import json
import datetime

SLACK_BOT_TOKEN = 'xoxb-313903713426-UJKPHKX598yn8PbrLV4i9Yue'

slack_client = SlackClient(SLACK_BOT_TOKEN)
msg = json.load(open("message.json"))

# This will post the message to the general channel of our Yelp group
# under the name of the bot
# you can change the channel parameter to any other existing channel names,
# for example '#random'
send_message(channel, message)

def send_message(msg, channel):
	slack_client.api_call("chat.postMessage", channel=channel, **msg)

def get_restaurant(id):

	res = {} # get json from yelp
	
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