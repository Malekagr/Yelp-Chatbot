from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
from flask import Flask

app = Flask(__name__)

# found in OAuth and Permission section
SLACK_BOT_TOKEN = 'xoxb-313903713426-UJKPHKX598yn8PbrLV4i9Yue'

# Part of App Credentials
SLACK_VERIFICATION_TOKEN = 'zuBu6ghkakwlQhUWWI3RLBFy'

slack_client = SlackClient(SLACK_BOT_TOKEN)
slack_events_adapter = SlackEventAdapter(SLACK_VERIFICATION_TOKEN, endpoint="/slack/events", server=app)


@slack_events_adapter.on("message")
# requires 'message' scope
def handle_message(event_data):
    print(event_data)
    message = event_data["event"]
    if message.get("subtype") is None:
        channel = message["channel"]
        msg = "<@%s> just typed: " % message["user"] + message["text"] + " :simple_smile:"
        print('Attempting to post:', msg)
        slack_client.api_call("chat.postMessage", channel=channel, text=msg, as_user=True)
        
@slack_events_adapter.on("reaction_added")
# requires 'reaction_added' scope
def reaction_added(event_data):
    event = event_data["event"]
    emoji = event["reaction"]
    channel = event["item"]["channel"]
    text = ":%s:" % emoji
    slack_client.api_call("chat.postMessage", channel=channel, text=text, as_user=True)
