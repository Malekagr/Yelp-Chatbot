from Slack_API import Slack
from slackeventsapi import SlackEventAdapter
from flask import Flask

SLACK_BOT_TOKEN = 'xoxb-309384138949-wInzZ71weN1LpnRMHZWNfjWh'
bot = Slack(SLACK_BOT_TOKEN)
slack_events_adapter = SlackEventAdapter(SLACK_VERIFICATION_TOKEN, endpoint="/slack/events", server=app)

@slack_events_adapter.on("message")
# requires 'message' scope (Event API)
def handle_message(event_data):
    message = event_data["event"]
    if message.get("subtype") is None:
        channel = message["channel"]
        message = "<@%s>! You typed: " % message["user"] + message["text"] + " :simple_smile:"
        bot.send_message(channel=channel, text=message)
        
@slack_events_adapter.on("reaction_added")
# requires 'reaction_added' scope (Event API)
def reaction_added(event_data):
    event = event_data["event"]
    emoji = event["reaction"]
    channel = event["item"]["channel"]
    text = ":%s:" % emoji
    bot.send_message(channel=channel, text=message)
