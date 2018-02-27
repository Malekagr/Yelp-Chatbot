import requests
from urllib.parse import quote

class YelpAPI(object):
    # code modified from https://github.com/Yelp/yelp-fusion/blob/master/fusion/python/sample.py
    def __init__(self, api_key):
        self.key = api_key
        self.API_HOST = 'https://api.yelp.com'
        self.SEARCH_PATH = '/v3/businesses/search'
        self.BUSINESS_PATH = '/v3/businesses/'

    def request(self, host, path, api_key, url_params={}):
        url_params = url_params or {}
        url = '{0}{1}'.format(host, quote(path.encode('utf8')))
        headers = {
            'Authorization': 'Bearer %s' % api_key,
        }
        response = requests.request('GET', url, headers=headers, params=url_params)
        return response.json()

    def get_business(self, business_id):
        """Query the Business API by a business ID.
        Args:
            business_id (str): The ID of the business to query.
        Returns:
            dict: The JSON response from the request.
        """
        business_path = self.BUSINESS_PATH + business_id
        return self.request(self.API_HOST, business_path, self.key )

    def get_reviews(self, business_id):
        reviews_path = self.BUSINESS_PATH + business_id + '/reviews'
        return self.request(self.API_HOST, reviews_path, self.key )

    def search(self, term, location, search_limit):
        url_params = {
            'term': term.replace(' ', '+'),
            'location': location.replace(' ', '+'),
            'limit': search_limit
        }
        return self.request(self.API_HOST, self.SEARCH_PATH, self.key, url_params=url_params)
