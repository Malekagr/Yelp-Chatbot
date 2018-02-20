from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
from flask import Flask, request
import click, os, sys


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
        click.echo('Attempting to post:', msg)
        slack_client.api_call("chat.postMessage", channel=channel, text=msg)

# requires 'reaction_added' scope
@slack_events_adapter.on("reaction_added")
def reaction_added(event_data):
    event = event_data["event"]
    emoji = event["reaction"]
    channel = event["item"]["channel"]
    text = ":%s:" % emoji
    slack_client.api_call("chat.postMessage", channel=channel, text=text)
