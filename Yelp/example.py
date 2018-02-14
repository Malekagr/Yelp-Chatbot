import Yelp_API

# get an api key by registering an yelp account
API_KEY= ''
    
# make an instance of the class Yelp_API, remember to pass in the api key
ya = Yelp_API(API_KEY)
    
# searching for results of 'pizza place' in 'Pittsburgh, PA', and list out at most 5 results
# you could mess around with the arguments, like changing the location to a zipcode
ya.lookup(term='pizza place', location='Pittsburgh, PA', search_limit=5)
