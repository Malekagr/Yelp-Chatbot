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

@slack_events_adapter.on("message")
# requires 'message' scope
def handle_message(event_data):
    print(event_data)
    message = event_data["event"]
    if message.get("subtype") is None and "hello world" in message.get('text'):
        channel = message["channel"]
        msg = "<@%s> just typed: " % message["user"] + message["text"] + " :simple_smile:"
        print('Attempting to post:', msg)
        slack_client.api_call("chat.postMessage", channel=channel, text=msg)
        
@slack_events_adapter.on("reaction_added")
# requires 'reaction_added' scope
def reaction_added(event_data):
    event = event_data["event"]
    emoji = event["reaction"]
    channel = event["item"]["channel"]
    text = ":%s:" % emoji
    slack_client.api_call("chat.postMessage", channel=channel, text=text)
