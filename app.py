from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
from flask import Flask, make_response, Response, request
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

# handles button press events
@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    # Parse the request payload
    form_json = json.loads(request.form["payload"])

    # Check to see what the user's selection was and update the message
    selection = form_json["actions"][0]["value"]

    message_text = '<@{0}> selected {1}'.format(form_json["user"]["id"], selection)
    
    slack_client.api_call(
      "chat.postMessage",
      channel=form_json["channel"]["id"],
      text=message_text
    )

    return make_response("", 200)

# requires 'message' scope
@slack_events_adapter.on("message")
def handle_message(event_data):
  message = event_data["event"]
  if message.get("subtype") is None:
    channel = message["channel"]
    user = message["user"]

    if "hello" in message.get('text'):
      send_message(channel, text="Hi <@%s>! :simple_smile:" % user)

# send a message to channel
# uses keyword args to expand message
# for simple messages, use send_message(channel, text="simple message")
# for dict/formatted messages, use send_message(channel, **msg)
def send_message(channel, **msg):
  slack_client.api_call("chat.postMessage", channel=channel, **msg)