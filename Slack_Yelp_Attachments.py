
# coding: utf-8

from YELP_API import Yelp_API
from slackclient import SlackClient
from datetime import datetime, time


# In[4]:

def get_rating_stars(rating=1.5):
    return "\u2605"*int(rating) + "\u2606"*(0 if rating % 1 == 0 else 1)


# In[5]:

def get_attachment(title="Empty", title_link="", fallback="Couldn't fetch info.", color="#E01010", pretext="", author_name="\u2605\u2605", author_icon="", text="", img_url="", thumb_url="", price_range="$$$$", open_status="Currently Open", open_hours=""):
    attachments_json = {
            "title": title,
            "title_link": title_link,
            "fallback": fallback,
            "color": color,
            "pretext": pretext,
            "author_name": author_name,
            "author_icon": author_icon,
            "text": text,
            "fields": [
                    {
                        "title": price_range
                    },
                        {
                            "title": open_status,
                            "value": open_hours
                        }
                ],
            "image_url": img_url,
            "thumb_url": thumb_url,
            "footer": "Yelp API",
            "footer_icon": "http://icons.iconarchive.com/icons/sicons/basic-round-social/512/yelp-icon.png",
        }
    
    return attachments_json


# In[6]:

def get_best_review(reviews):
    current_rating = -1
    best_review = ""
    for r in reviews['reviews']:
        if int(r['rating']) > current_rating:
            current_rating = int(r['rating'])
            best_review = r['text']
    return best_review


# In[7]:

def get_expensiveness(price):
    count = len(price)
    if count == 1:
        return """I heard it's cheap."""
    elif count == 2:
        return """I think it's inexpensive."""
    elif count == 3:
        return """It's not going to be cheap."""
    else:
        return """It's expensive for sure."""


# In[8]:

def get_open_status(business, ts=0):
    if 'hours' not in business and 'is_open_now' not in business:
        # some businesses don't provide business hours
        return 'Not provided.', 'Not provided.', False, """Unsure if it's opened or not."""
    elif 'hours' not in business:
        return 'Not provided.', 'Not provided.', False, bool(business['is_open_now'])
    
    hours = business['hours'][0]['open']
    todays_day = datetime.today().weekday() # like monday, tuesday, wednesday ...
    time_now = datetime.now().time()
    
    hours_of_day = ''
    opened_until = 'Not provided.'
    is_overnight = False
    is_opened = bool(business['hours'][0]['is_open_now'])
    
    for h in hours:
        if h['day'] == todays_day:
            start_time = time(int(h['start'][:2]), int(h['start'][2:]))
            close_time = time(int(h['end'][:2]), int(h['end'][2:]))
            is_overnight = bool(h['is_overnight'])
            hours_of_day += ('\n{0}-{1}\n'.format(start_time.strftime("%H:%M"), close_time.strftime("%H:%M")))
            opened_until = close_time             
            
    return hours_of_day, opened_until.strftime("%H:%M"), is_overnight, is_opened


# In[9]:

def get_attachments_with_yelp(yelp_api_key, term="lunch", location="pittsburgh, pa", limit=1, ts=0):
    _ya = Yelp_API(yelp_api_key)
    response = _ya.search(term=term, location=location, search_limit=limit)
    businesses = response.get('businesses')
    
    att = []
    business_names = []
    for business in businesses:
        b_id = business['id']
        name = business['name']
        business_names.append(name)
        full_address = ', '.join(business['location']['display_address'])
        phone = business['display_phone']
        img = business['image_url']
        
        if 'price' in business:
            price = "Expensiveness: " + get_expensiveness(business['price'])
        else:
            price = 'Expensiveness: Not provided.'
        
        reviews = _ya.get_reviews(b_id)
        review = get_best_review(reviews)
        
        b_info = _ya.get_business(b_id)
        hours_of_day, opened_until, is_overnight, is_opened = get_open_status(b_info, ts=0)
        
        status = ('Currently Closed.' if not is_opened else 'Opened until: ' + opened_until) 
        #print(bool(business['is_closed']))
        
        a = get_attachment(name, title_link=business['url'], author_name=get_rating_stars(business['rating']), 
                           text="{0}\n {1}\n\n{2}".format(full_address, phone, review), 
                           thumb_url=img, price_range=price, open_status=status, 
                           open_hours="Today's hours: " + hours_of_day
                        )
        att.append(a)
        
    return att, business_names


# In[10]:

def get_button_attachment(business_names):
    actions = []
    for b in business_names:
        actions.append({
            "name": b,
            "text": b,
            "value": b,
            "type": 'button'            
        })
    
    button_att = {
            "title": 'VOTE',
            "callback_id": 'vote_failed',
            "actions": actions
    }
    return button_att


# In[11]:

def send_results_to_slack(yelp_key, slack_token, channel='#general', term="lunch", location="Pittsburgh, PA", limit=1, ts=0):
    attachments, business_names = get_attachments_with_yelp(yelp_key, term=term, location=location, limit=limit)
    sc = SlackClient(slack_token)
    
    buttons = [get_button_attachment(business_names)]
    
    recom = "Recommendation"
    sc.api_call("chat.postMessage", channel=channel, 
                text="{0} {1} {2}:".format(str(limit), term.title(), recom if limit==1 else recom+'s'),
                attachments=str(attachments)
               )
    sc.api_call("chat.postMessage", channel=channel, 
                text="Cast your votes!",
                attachments=str(buttons)
               )



