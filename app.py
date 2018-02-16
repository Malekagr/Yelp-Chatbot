from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
from flask import Flask
import click

app = Flask(__name__)
app.config.from_json("credentials.json")
slack_client = SlackClient(app.config["SLACK_BOT_TOKEN"])
slack_events_adapter = SlackEventAdapter(app.config["SLACK_VERIFICATION_TOKEN"], endpoint="/slack/events", server=app)

@slack_events_adapter.on("message")
# requires 'message' scope
def handle_message(event_data):
    click.echo(event_data)
    message = event_data["event"]
    if message.get("subtype") is None and "hello world" in message.get('text'):
        channel = message["channel"]
        msg = "<@%s> just typed: " % message["user"] + message["text"] + " :simple_smile:"
        click.echo('Attempting to post:', msg)
        slack_client.api_call("chat.postMessage", channel=channel, text=msg)

@slack_events_adapter.on("reaction_added")
# requires 'reaction_added' scope
def reaction_added(event_data):
    event = event_data["event"]
    emoji = event["reaction"]
    channel = event["item"]["channel"]
    text = ":%s:" % emoji
    slack_client.api_call("chat.postMessage", channel=channel, text=text)