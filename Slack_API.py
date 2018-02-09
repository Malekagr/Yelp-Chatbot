
# coding: utf-8

# In[2]:

from slackclient import SlackClient

class Slack(object):
    def __init__(self, user_bot_token, verfication_token=None):
        self.bot_token = user_bot_token
        self.verf_token = verfication_token
        self.slack_client = SlackClient(self.bot_token)
        
    def send_message(self, message='hello world!', channel_name='#general'):
        ret = self.slack_client.api_call('chat.postMessage', channel=channel_name, text=message)
        return ret
        
    def reply_message(self, message='I replied!', channel_name='#general', timestamp=0):
        ret = self.slack_client.api_call('chat.postMessage', channel=channel_name, text=message, ts=timestamp)
        return ret

