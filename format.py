import datetime, urllib.parse

sidebar_color = "#D01010"
footer = "YelpBot"
footer_icon = "https://www.yelp.com/favicon.ico"
placeholder_image = "https://s3-media3.fl.yelpcdn.com/assets/srv0/yelp_styleguide/fe8c0c8725d3/assets/img/default_avatars/business_90_square.png"
maps_api = "https://www.google.com/maps/search/?api=1&"

# takes in the result of 2 Yelp API calls
# nicely formats a restaurant with relevant info
# TODO: use the stars that Yelp requires
def format_restaurant(restaurant, reviews):
  # we need a name and URL no matter what
  if not ("name" in restaurant and "url" in restaurant):
    return {"text": "Could not format"}
  name = restaurant["name"]
  link = restaurant["url"]

  formatted = {}
  formatted["text"] = "I found {}! ({})".format(name, get_categories(restaurant))
  restaurant = {}
  attachments = [restaurant]
  formatted["attachments"] = attachments
  restaurant["fallback"] = name
  restaurant["color"] = sidebar_color
  restaurant["author_name"] = get_rating(restaurant)
  restaurant["author_link"] = link
  restaurant["title"] = name
  restaurant["title_link"] = link
  restaurant["text"] = get_review_snipet(reviews)
  restaurant["thumb_url"] = get_image(restaurant)
  restaurant["footer"] = footer
  restaurant["footer_icon"] = footer_icon
  restaurant["fields"] = [{"title": "Open today until {} / {}".format(get_time(restaurant), get_price(restaurant))}]

  return formatted

# get price with fallback
def get_price(restaurant):
  if "price" in restaurant:
    return restaurant["price"]
  return "Unknown Price"

# get image with fallback
def get_image(restaurant):
  if "image" in restaurant:
    return restaurant["image_url"]
  return placeholder_image

# get star rating with fallback
# TODO: Yelp requires us to use specific star icons
def get_rating(restaurant):
  if "rating" in restaurant:
    return "\u2605" * int(restaurant["rating"]) + "\u2606" * (5 - int(restaurant["rating"]))
  return "\u2606" * 5

# get today's closing time
def get_time(restaurant):
  if "time" in restaurant:
    weekday = datetime.datetime.today().weekday()
    endtime = restaurant["hours"][0]["open"][weekday]["end"]
    return endtime[:2] + ":" + endtime[2:]
  return "Unknown Closing Time"

# get categories
def get_categories(restaurant):
  if "categories" in restaurant and len(restaurant["categories"]) > 0:
    return "/".join(map((lambda cat: cat["title"]), restaurant["categories"]))
  return "Unknown Categories"


# get review snippet
def get_review_snipet(reviews):
  if "reviews" in reviews and len(reviews["reviews"]) > 0:
    return reviews["reviews"][0]["text"]
  return ""

# get address
def get_address(restaurant):
  if "location" in restaurant and "display_address" in restaurant["location"]:
    return ", ".join(restaurant["location"]["display_address"])
  return "Unknown address"

# get a link for navigation
def get_nav_link(address):
  return maps_api + urllib.parse.urlencode({"query": address})