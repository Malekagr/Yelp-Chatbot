
# coding: utf-8

# In[2]:

from slackclient import SlackClient

class Slack(object):
    def __init__(self, user_bot_token, verfication_token=None):
        self.bot_token = user_bot_token
        self.verf_token = verfication_token
        self.slack_client = SlackClient(self.bot_token)
        
    def send_message(self, message='hello world!', channel='#general'):
        self.slack_client.api_call('chat.postMessage', channel=channel, text=message)

