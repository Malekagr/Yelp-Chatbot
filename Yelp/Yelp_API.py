import json
import requests

from urllib.parse import quote

class Yelp_API(object):
    # code modified from https://github.com/Yelp/yelp-fusion/blob/master/fusion/python/sample.py
    def __init__(self, api_key):
        self.key = api_key

        self.API_HOST = 'https://api.yelp.com'
        self.SEARCH_PATH = '/v3/businesses/search'
        self.BUSINESS_PATH = '/v3/businesses/'
    
    def request(self, host, path, api_key, url_params=None):
        url_params = url_params or {}
        url = '{0}{1}'.format(host, quote(path.encode('utf8')))
        headers = {
            'Authorization': 'Bearer %s' % api_key,
        }
        
        response = requests.request('GET', url, headers=headers, params=url_params)
        return response.json()
    
    def search(self, api_key, term, location, search_limit):
        url_params = {
            'term': term.replace(' ', '+'),
            'location': location.replace(' ', '+'),
            'limit': search_limit
        }
    
        return self.request(self.API_HOST, self.SEARCH_PATH, api_key, url_params=url_params)
    
    def parse_info(self, business):
        # parse the json data received from the api
        # 'business' passed in as a dict
        rating = business['rating']
        name = business['name']
        address = business['location']['display_address'][0] + ' ' + business['location']['display_address'][1]
        phone = business['display_phone']
        url = business['url']
        status = 'Currently Open'
        if bool(business['is_closed']):
            status = 'Currently Closed'
        
        # message text
        message = 'Rating: ' + str(rating) + '\n' + str(name) + '\n' + str(address) + '\n' + str(phone) + '\n' + status + '\n\n' + str(url)
    
        return message
    
    def print_all_info(self, businesses):
        s = ''
        for b in businesses:
            s += self.parse_info(b) + '\n'
        print(s)
        return s
    
    def lookup(self, term='food', location='Pittsburgh, PA', search_limit=3):
        response = self.search(self.key, term, location, search_limit)
        businesses = response.get('businesses')
        if not businesses:
            return u'No results for {0} in {1}'.format(term, location)
    
        return self.print_all_info(businesses)
