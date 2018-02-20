import json, datetime, urllib.parse

sidebar_color = "#D01010"
footer = "YelpBot"
footer_icon = "https://www.yelp.com/favicon.ico"

def format_restaurant(id):
  res = json.load(open("testres.json")) # get from Yelp
  reviews = json.load(open("testreviews.json")) # get from Yelp

  # get name, url, price, an image
  name = res["name"]
  link = res["url"]
  price = res["price"]
  image = res["image_url"]

  # get star rating
  # TODO: Yelp requires us to use specific star icons
  rating = "\u2605" * int(res["rating"]) + "\u2606" * (5 - int(res["rating"]))

  # get today's closing time
  weekday = datetime.datetime.today().weekday()
  endtime = res["hours"][0]["open"][weekday]["end"]
  time = endtime[:2] + ":" + endtime[2:]

  # get categories
  desc = "result"
  if "categories" in res and len(res["categories"]) > 0:
    desc = "/".join(map((lambda cat: cat["title"]), res["categories"]))

  # get review snippet
  snippet = ""
  if "reviews" in reviews and len(reviews["reviews"]) > 0:
    snippet = reviews["reviews"][0]["text"]

  # get address
  address = ", ".join(res["location"]["display_address"])

  # get a link for navigation
  maps_api = "https://www.google.com/maps/search/?api=1&"
  nav_link = maps_api + urllib.parse.urlencode({"query": address})

  # now we BUILD!
  formatted = {}
  formatted["text"] = "I found {}! ({})".format(name, desc)
  restaurant = {}
  attachments = [restaurant]
  formatted["attachments"] = attachments
  restaurant["fallback"] = name
  restaurant["color"] = sidebar_color
  restaurant["author_name"] = rating
  restaurant["author_link"] = link
  restaurant["title"] = name
  restaurant["title_link"] = link
  restaurant["text"] = snippet
  restaurant["thumb_url"] = image
  restaurant["footer"] = footer
  restaurant["footer_icon"] = footer_icon
  restaurant["fields"] = [{"title": "Open today until {} / {}".format(time, price)}]

  print(formatted)

format_restaurant(123)