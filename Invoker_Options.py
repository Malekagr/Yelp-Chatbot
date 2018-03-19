invoker_options={
    "title": 'Choose an option for this voting session:',
    "callback_id": 'invoker_controls',
    "actions": [{
            "name": 'Reroll',
            "text": 'Reroll',
            "value": 'reroll',
            "type": 'button',
            "confirm": {
                "title": "Are you sure?",
                "text": "Are you sure you want to reroll the options?",
                "ok_text": "Yes",
                "dismiss_text": "No"
            }   
        },{
            "name": 'Finalize',
            "text": 'Finalize',
            "value": 'finalize',
            "type": 'button',
            "confirm": {
                "title": "Are you sure?",
                "text": "Are you sure you want to finalize the session?",
                "ok_text": "Yes",
                "dismiss_text": "No"
            }   
        },{
            "name": 'Cancel',
            "text": 'Cancel',
            "value": 'cancel',
            "type": 'button',
            "confirm": {
                "title": "Are you sure?",
                "text": "Are you sure you want to cancel the session?",
                "ok_text": "Yes",
                "dismiss_text": "No"
            }            
        }
    ]
}

def send_invoker_options(user, channel, slack_client):
    return slack_client.api_call("chat.postEphemeral", channel=channel, user=user, text="Invoker Perks", attachments=str([invoker_options]))
