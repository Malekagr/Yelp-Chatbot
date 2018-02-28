import datetime, urllib.parse

sidebar_color = "#D01010"
footer = "YelpBot"
footer_icon = "https://www.yelp.com/favicon.ico"
placeholder_image = "https://s3-media3.fl.yelpcdn.com/assets/srv0/yelp_styleguide/fe8c0c8725d3/assets/img/default_avatars/business_90_square.png"
maps_api = "https://www.google.com/maps/search/?api=1&"

def build_vote_message(restaurant_arr, reviews_arr):
  msg = {"text": "I found these options:", "attachments": []}
  for i in range(len(restaurant_arr)):
    msg["attachments"].append(format_with_vote_button(
      restaurant_arr[i], reviews_arr[i]))
  return msg

# formats the given restaurant and review message
# uses format_restaurant
# adds necessary voting bits
def format_with_vote_button(restaurant, reviews):
  formatted = format_restaurant(restaurant, reviews)
  formatted["callback_id"] = "vote"
  formatted["actions"] = [{
    "name": "vote",
    "text": "Vote!",
    "value": restaurant["name"],
    "type": "button"
  }]
  formatted["fields"].append({"title": "Votes:", "value": 0})
  return formatted

# takes in the result of 2 Yelp API calls
# nicely formats a restaurant as an attachment
# TODO: use the stars that Yelp requires
# TODO: address/nav-link
def format_restaurant(restaurant, reviews):
  # we need a name and URL no matter what
  if not ("name" in restaurant and "url" in restaurant):
    return {"text": "Could not format"}
  name = restaurant["name"]
  link = restaurant["url"]

  rating = get_rating(restaurant)
  snippet = get_review_snippet(reviews)
  image = get_image(restaurant)
  price = get_price(restaurant)

  time = "Currently closed."
  if is_open(restaurant):
    time = "Open until {}".format(get_closing_time)

  restaurant_attachment = {}
  restaurant_attachment["fallback"] = name
  restaurant_attachment["color"] = sidebar_color
  restaurant_attachment["author_name"] = rating
  restaurant_attachment["author_link"] = link
  restaurant_attachment["title"] = name
  restaurant_attachment["title_link"] = link
  restaurant_attachment["text"] = snippet
  restaurant_attachment["thumb_url"] = image
  restaurant_attachment["footer"] = footer
  restaurant_attachment["footer_icon"] = footer_icon
  restaurant_attachment["fields"] = [
    {"title": time, "short": "true"},
    {"title": price, "short": "true"}
  ]

  return restaurant_attachment

# get price with fallback
def get_price(restaurant):
  if "price" in restaurant:
    return restaurant["price"]
  return None

# get image with fallback
def get_image(restaurant):
  if "image_url" in restaurant:
    return restaurant["image_url"]
  return placeholder_image

# get star rating with fallback
# TODO: Yelp requires us to use specific star icons
def get_rating(restaurant):
  if "rating" in restaurant:
    return "\u2605" * int(restaurant["rating"]) + "\u2606" * (5 - int(restaurant["rating"]))
  return "\u2606" * 5

# get current open status
def is_open(restaurant):
  if "hours" in restaurant and "is_open_now" in restaurant["hours"][0]:
    return restaurant["hours"][0]["is_open_now"]
  return False

# get today's closing time with fallback
def get_closing_time(restaurant):
  if "hours" in restaurant:
    weekday = datetime.datetime.today().weekday()
    endtime = restaurant["hours"][0]["open"][weekday]["end"]
    return endtime[:2] + ":" + endtime[2:]
  return None

# get categories
def get_categories(restaurant):
  if "categories" in restaurant and len(restaurant["categories"]) > 0:
    return "/".join(map((lambda cat: cat["title"]), restaurant["categories"]))
  return None

# get review snippet
def get_review_snippet(reviews):
  current_rating = -1
  best_review = None

  if "reviews" in reviews:
    for r in reviews["reviews"]:
      if "rating" in r and "text" in r:
        if int(r["rating"]) > current_rating:
          current_rating = int(r["rating"])
          best_review = r["text"]
  return best_review

# get address
def get_address(restaurant):
  if "location" in restaurant and "display_address" in restaurant["location"]:
    return ", ".join(restaurant["location"]["display_address"])
  return None

# get a link for navigation
def get_nav_link(restaurant):
  address = get_address(restaurant)
  if address:
    return maps_api + urllib.parse.urlencode({"query": address})
  return None
