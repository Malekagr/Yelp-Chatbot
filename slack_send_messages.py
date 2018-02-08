# You would need to download slackclient first
# In command line: pip install slackclient
# https://pypi.python.org/pypi/slackclient

# This shows an example of sending a message to Slack

from slackclient import SlackClient

SLACK_BOT_TOKEN = 'xoxb-311305854327-QXJDo079SwxZUFhYMsFWmbmq'

slack_client = SlackClient(SLACK_BOT_TOKEN)
msg = 'PUT YOUR MESSAGE HERE'

# This will post the message to the general channel of our Yelp group
# under the name of the bot
# you can change the channel parameter to any other existing channel names,
# for example '#random'
slack_client.api_call("chat.postMessage", channel="#general", text=msg)
