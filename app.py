from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
from flask import Flask, request
import click, os


def main():
    app = Flask(__name__)

    success = True

    success = success and import_env_var(app, "SLACK_BOT_TOKEN")
    success = success and import_env_var(app, "SLACK_VERIFICATION_TOKEN")

    if not success:
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    slack_client = SlackClient(app.config["SLACK_BOT_TOKEN"])
    slack_events_adapter = SlackEventAdapter(app.config["SLACK_VERIFICATION_TOKEN"], endpoint="/slack/events", server=app)

# requires 'message' scope
@slack_events_adapter.on("message")
def handle_message(event_data):
    click.echo(event_data)
    message = event_data["event"]
    if message.get("subtype") is None and "hello world" in message.get('text'):
        channel = message["channel"]
        msg = "<@%s> just typed: " % message["user"] + message["text"] + " :simple_smile:"
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

# import an environment variable as an app config option
def import_env_var(app, env_var):
    try:
        app.config[env_var] = os.environ[env_var]
        return True
    except KeyError:
        return False

if __name__ == "__main__":
    main()