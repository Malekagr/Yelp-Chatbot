from Slack_Yelp_Attachments import send_results_to_slack

SLACK_TOKEN = 'xoxb-313903713426-UJKPHKX598yn8PbrLV4i9Yue'
YELP_KEY = 'hUxX4T7WpWwbbfTNnPIQ0Z1YvMxjyKsaVljDe2g1K1-KpTbrRUuGLkpbMNaXDnbHrIIgc5dQL9TRTfuOSDkLxNo-f5HzdOJbUbWz7dxS2fu10cLa5WBHv8XJsC6HWnYx'

TERM = "food"
CHANNEL = "#bot-testing"
LIMIT = 3
LOCATION = "Pittsburgh, PA, 15260"

send_results_to_slack(yelp_key=YELP_KEY, slack_token=SLACK_TOKEN, channel=CHANNEL, term=TERM, limit=LIMIT, 
                      location=LOCATION)
