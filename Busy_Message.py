busy_message={
    "title": 'Revoke the session?',
    "callback_id": 'busy_message',
    "actions": [{
            "name": 'Revoke',
            "text": 'Revoke',
            "value": 'revoke',
            "type": 'button',
            "confirm": {
                "title": "Are you sure?",
                "text": "Are you sure you want to revoke the current voting session?",
                "ok_text": "Yes",
                "dismiss_text": "No"
            }   
        }
    ]
}

def send_busy_message(channel, slack_client):
    im_busy = "Sorry, there seems to be an ongoing voting session, please close it or use the revoke button to revoke the session."
    return slack_client.api_call("chat.postMessage", channel=channel, text=im_busy, attachments=str([busy_message]))
