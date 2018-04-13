import datetime, urllib.parse, json

sidebar_color = "#D01010"
footer = "YelpBot"
footer_icon = "https://www.yelp.com/favicon.ico"
placeholder_image = "https://s3-media3.fl.yelpcdn.com/assets/srv0/yelp_styleguide/fe8c0c8725d3/assets/img/default_avatars/business_90_square.png"
maps_api = "https://www.google.com/maps/search/?api=1&"
categories_map = {}

def build_vote_message(restaurant_arr):
  msg = {"text": "I found these options:", "attachments": []}
  for r in restaurant_arr:
    msg["attachments"].append(format_with_vote_button(r))
  return msg

def build_normal_message(restaurant_arr, text=""):
  msg = {"text": text, "attachments": []}
  for r in restaurant_arr:
    msg["attachments"].append(format_restaurant(r))
  return msg

# formats the given restaurant and review message
# uses format_restaurant
# adds necessary voting bits
def format_with_vote_button(restaurant):
  formatted = format_restaurant(restaurant)
  formatted["callback_id"] = "vote"
  formatted["actions"] = [{
    "name": restaurant["name"],
    "text": "Vote!",
    "value": restaurant["id"],
    "type": "button"
  }]
  formatted["fields"].append({"title": "Votes: 0"})
  return formatted

# takes in the result of 2 Yelp API calls
# nicely formats a restaurant as an attachment
# TODO: use the stars that Yelp requires
# TODO: address/nav-link
def format_restaurant(restaurant):
  # we need a name and URL no matter what
  if not ("name" in restaurant and "url" in restaurant):
    return {"text": "Could not format"}
  name = restaurant["name"]
  link = restaurant["url"]

  rating = get_rating(restaurant)
  categories = get_categories(restaurant)
  image = get_image(restaurant)
  price = get_price(restaurant)

  time = "Currently closed."
  if is_open(restaurant):
    time = "Open until {}".format(get_closing_time(restaurant))

  restaurant_attachment = {}
  restaurant_attachment["fallback"] = name
  restaurant_attachment["color"] = sidebar_color
  restaurant_attachment["author_name"] = rating
  restaurant_attachment["author_link"] = link
  restaurant_attachment["title"] = name
  restaurant_attachment["title_link"] = link
  restaurant_attachment["text"] = categories
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
    try:
      endtime = [h['end'] for h in restaurant['hours'][0]['open'] if h['day'] == weekday].pop(0)
      return endtime[:2] + ":" + endtime[2:]
    except (IndexError, KeyError) as e:
      return "Unsure"
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

# get a slack emoji name from a Yelp category name
def category_to_emoji(cat_name):
  global categories_map
  cat_name = cat_name.lower()

  if len(categories_map) == 0:
    categories_map = json.load(open("categories.json"))

  if cat_name in categories_map:
    return ":" + categories_map[cat_name] + ":"
  return None
