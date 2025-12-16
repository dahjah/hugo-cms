+++
title = "Home"
date = ""
draft = false
type = "home"
[[header_blocks]]
  type = "row"
  gap = "4"
  justify = "space-between"
  align = "center"
  [[header_blocks.blocks]]
    type = "brand_logo"
    logo_url = ""
    brand_name = "Strippin Dippin Chicken"
    tagline = ""
    link_url = "/"
    logo_image = "/media/uploads/e3187daf-c430-4279-a31a-737a0b2f87e0.jpg"
  [[header_blocks.blocks]]
    type = "menu"
    style = "pills"
    responsive = true
    hamburgerDirection = "dropdown"
    items = [{label = "Home", url = "/", type = "link"}, {label = "Menu", url = "/menu", type = "link"}, {label = "Catering", url = "/catering", type = "link"}, {label = "Contact", url = "/contact", type = "link"}]

[[main_blocks]]
  type = "section"
  style = "welcome"
  id = "hero"
  [[main_blocks.blocks]]
    type = "hero"
    title = "Delicious Strippin Dippin Chicken"
    subtitle = "Fresh Chicken strips, Handcut French fries and \"Awesome\" hand-made dipping sauces."
    bgImage = "/media/uploads/ecf05118-0ecc-4a2f-bbcd-a74c45b8549a.jpg"
    cta_text = "View Menu"
    cta_url = "/menu"

[[main_blocks]]
  type = "section"
  style = "default"
  id = "highlights"
  [[main_blocks.blocks]]
    type = "text"
    content = "<h2 class=\"text-center\">Highlights</h2>"
  [[main_blocks.blocks]]
    type = "features_grid"
    columns = "3"
    features = [{icon = "leaf", title = "Fresh & Made to Order", description = "Experience the taste of fresh, never frozen Chicken Shop, prepared right when you order."}, {icon = "truck", title = "Fast & Friendly", description = "We bring the flavor to you! Perfect for quick lunches, events, and catering needs."}, {icon = "map-pin", title = "Local Favorite", description = "A staple of the local food scene, serving up delicious bites for everyone to enjoy."}]

[[main_blocks]]
  type = "section"
  style = "alt"
  id = "menu"
  [[main_blocks.blocks]]
    type = "text"
    content = "<h2>Menu</h2>"
  [[main_blocks.blocks]]
    type = "markdown"
    content = "At Strippin Dippin Chicken, we are passionate about bringing the best street food to you. Fresh Chicken strips, Handcut French fries and \"Awesome\" hand-made dipping sauces. Whether you're grabbing a quick lunch or planning an event, we're here to serve you."
  [[main_blocks.blocks]]
    type = "menu_grid"
    columns = "3"
    show_images = true
    items = [{name = "Famous Chicken Strips", image = "/media/uploads/3279c6b6-6931-4883-a551-3e36e2099e6a.jpg", description = "Crispy, golden-brown chicken tenders served with our signature house sauce. ($12.99)"}, {name = "Hand-Cut Fries", image = "/media/uploads/480b990d-0982-4be6-aa33-2c6e8bd7392f.jpg", description = "Freshly cut potatoes, twice-fried for extra crispiness. ($5.99)"}, {name = "Combo Meal", image = "/media/uploads/c6cd5097-cf1b-421c-8230-fc0b01d96282.jpg", description = "3 strips, fries, and a drink. ($16.99)"}, {name = "Spicy Dippin Sauce", image = "/media/uploads/4f170473-f379-4ebc-8641-4fb95d65d3f9.jpg", description = "Our secret blend of spices and creaminess. ($0.50)"}]
  [[main_blocks.blocks]]
    type = "row"
    justify = "center"
    gap = "3"
    [[main_blocks.blocks.blocks]]
      type = "button"
      text = "See Full Menu"
      url = "/menu"
      style = "primary"


[[main_blocks]]
  type = "section"
  style = "default"
  id = "locations"
  [[main_blocks.blocks]]
    type = "text"
    content = "<h2>Locations</h2>"

[[main_blocks]]
  type = "section"
  style = "alt"
  id = "catering"
  [[main_blocks.blocks]]
    type = "row"
    flex_mode = true
    gap = "2"
    [[main_blocks.blocks.blocks]]
      type = "column"
      width_percent = "50"
      [[main_blocks.blocks.blocks.blocks]]
        type = "column"
        [[main_blocks.blocks.blocks.blocks.blocks]]
          type = "text"
          content = "<h2>Catering</h2>"
        [[main_blocks.blocks.blocks.blocks.blocks]]
          type = "markdown"
          content = "At Strippin Dippin Chicken, we are passionate about bringing the best street food to you. Fresh Chicken strips, Handcut French fries and \"Awesome\" hand-made dipping sauces. Whether you're grabbing a quick lunch or planning an event, we're here to serve you."
        [[main_blocks.blocks.blocks.blocks.blocks]]
          type = "button"
          text = "Get Catering Info"
          url = "/catering"
          style = "primary"

      [[main_blocks.blocks.blocks.blocks]]
        type = "column"
        [[main_blocks.blocks.blocks.blocks.blocks]]
          type = "accordion"
          items = [{title = "Do you travel for private events?", content = "Yes! We love bringing our truck to weddings, parties, and corporate events."}, {title = "What is the minimum spend?", content = "Our minimums vary by location and date. Please contact us for a custom quote."}, {title = "Do I need to provide power?", content = "We are fully self-sufficient with our own generator."}, {title = "How far in advance should I book?", content = "We recommend booking at least 2-3 months in advance."}]

    [[main_blocks.blocks.blocks]]
      type = "column"
      width_percent = "50"

[[main_blocks]]
  type = "section"
  style = "light"
  id = "about"
  [[main_blocks.blocks]]
    type = "row"
    flex_mode = true
    gap = "2"
    [[main_blocks.blocks.blocks]]
      type = "column"
      width_percent = "55"
      [[main_blocks.blocks.blocks.blocks]]
        type = "column"
        [[main_blocks.blocks.blocks.blocks.blocks]]
          type = "text"
          content = "<h2>About</h2>"
        [[main_blocks.blocks.blocks.blocks.blocks]]
          type = "markdown"
          content = "At Strippin Dippin Chicken, we are passionate about bringing the best street food to you. Fresh Chicken strips, Handcut French fries and \"Awesome\" hand-made dipping sauces. Whether you're grabbing a quick lunch or planning an event, we're here to serve you."
        [[main_blocks.blocks.blocks.blocks.blocks]]
          type = "quote"
          text = ""
          author = ""
          title = ""

      [[main_blocks.blocks.blocks.blocks]]
        type = "column"
        [[main_blocks.blocks.blocks.blocks.blocks]]
          type = "image"
          src = ""
          alt = ""

    [[main_blocks.blocks.blocks]]
      type = "column"
      width_percent = "45"

[[main_blocks]]
  type = "section"
  style = "alt"
  id = "reviews"
  [[main_blocks.blocks]]
    type = "text"
    content = "<h2 class=\"text-center\">Reviews</h2>"
  [[main_blocks.blocks]]
    type = "carousel"
    auto_advance = true
    interval_seconds = "6"
    show_dots = true
    show_arrows = true
    [[main_blocks.blocks.blocks]]
      type = "image"
      src = "https://s3-media0.fl.yelpcdn.com/bphoto/q9XshFAkMaQLOlRKlS7RwQ/l.jpg"
      alt = "Gallery Image"
    [[main_blocks.blocks.blocks]]
      type = "image"
      src = "https://s3-media0.fl.yelpcdn.com/bphoto/c5ugvGu6ShLBLPPwvNPWdQ/l.jpg"
      alt = "Gallery Image"
    [[main_blocks.blocks.blocks]]
      type = "image"
      src = "https://s3-media0.fl.yelpcdn.com/bphoto/2NRRmCOMrk8WYpvYeUzPIQ/l.jpg"
      alt = "Gallery Image"
    [[main_blocks.blocks.blocks]]
      type = "image"
      src = "https://s3-media0.fl.yelpcdn.com/bphoto/Zd-C4aaz8oKoTaB0KPuUew/l.jpg"
      alt = "Gallery Image"
    [[main_blocks.blocks.blocks]]
      type = "image"
      src = "https://s3-media0.fl.yelpcdn.com/bphoto/SGLgHKRKqPF27Sj5aciZdw/l.jpg"
      alt = "Gallery Image"
  [[main_blocks.blocks]]
    type = "google_reviews"
    columns = "3"
    show_rating = true
    reviews = [{name = "James O.", rating = "5", text = "Great food!! Great price, Awesome value!!\nWill even cater for your events.\nNo better chicken!!", date = "", image = ""}, {name = "Oscar Z.", rating = "5", text = "These guys came to my office and indulged me with a great lunch meal. It was my first time so I went with the two piece combo, but trust me, I was regretting not having ordered the three piece meal at least by the end. Still, the amount of hand cut potatoes and the size of the strips left me fully satisfied. The person taking my order and payment was helpful and friendly, and the quality of the food talked for the care with which it was cooked. I hope they come back soon or I can find a post of where they would be going in the upcoming weeks.", date = "", image = ""}, {name = "John C.", rating = "5", text = "This food truck was amazing! They make everything from scratch per order they actually cut the potatoes right in front of you they actually dip the chicken in the batter and fry it right in front of you. \n\nThis puts the food truck for chicken at a new level. \n\nThey go North, South, East, and West and have to check their Instagram, and facebook. \n\nCan't wait to go back.", date = "", image = ""}, {name = "Luna D.", rating = "5", text = "I had the chicken salad and my daughter had the 2 piece strips. The fries were perfectly salted, the chicken was crispy, and the sauces were amazing. The bbq and peppercorn ranch mix on the chicken salad was amazing, and the lettuce was very fresh. The person running the truck was very friendly and the food was ready quickly. Would definitely eat here again!", date = "", image = ""}, {name = "Justin R.", rating = "1", text = "Food truck was at my office today. Very nice staff. However the food was not good, sadly. Chicken itself was bland at best. Breading was soft like a chicken nugget... didn't taste fried. Chicken was under cooked. The French fries had a coating, but were 100% undercooked. Soggy, cold, slimy on the inside... fries were limp. \n\nI tried the honey mustard sauce, which was a very standard sauce. Nothing new or amazing about it. Their spicy bam bam sauce (whatever it was called) was creamy and bland. No flavor. \n\nI was highly disappointed, as I love to support food trucks. However, this one needs some major internal love before I'll ever consider eating again.", date = "", image = ""}, {name = "Keisha F.", rating = "4", text = "First things first, the ranch is amazing. It's a black peppercorn ranch and just phenomenal. \n\nFries are great too, they are the hand-cut fries that are personally my favorite! \n\nThey literally prepare all the food as your order - so nothing is frozen or cooked beforehand. Which to me, means it's made with love. \n\nOnto the chicken, the flavor is 100% on point. It's delicious, you can tell the chicken is of quality and it's a good tender. I do find the breading interesting as it's extremely thin and not necessarily crispy. So I would say the breading is more like a coating and it reminds me of grilled chicken tenders with a bit of extra texture. \n\nAll in all, the flavors are on point and and aren't your usual chicken tender flavor - plus the fact that it's all made to order is really awesome! \n\nLooking forward to trying this place again.", date = "", image = ""}]

[[main_blocks]]
  type = "section"
  style = "cta"
  [[main_blocks.blocks]]
    type = "stats_counter"
    animate = true
    stats = [{value = "3.3", suffix = "", label = "Rating"}, {value = "14", suffix = "", label = "Review_count"}, {value = "465", suffix = "", label = "Followers"}, {value = "299", suffix = "", label = "Following"}, {value = "746", suffix = "", label = "Posts"}, {value = "14", suffix = "+", label = "Reviews"}]

[[main_blocks]]
  type = "section"
  style = "cta"
  id = "contact"
  [[main_blocks.blocks]]
    type = "text"
    content = "<h2 class=\"text-center\">Contact</h2>"
  [[main_blocks.blocks]]
    type = "row"
    justify = "center"
    gap = "4"
    [[main_blocks.blocks.blocks]]
      type = "button"
      text = "Order Now"
      url = "/menu"
      style = "primary"
    [[main_blocks.blocks.blocks]]
      type = "button"
      text = "Contact Us"
      url = "/contact"
      style = "secondary"


[[footer_blocks]]
  type = "social_links"
  links = [{platform = "yelp", url = "https://www.yelp.com/biz/strippin-dippin-chicken-west-jordan"}, {platform = "instagram", url = "https://www.instagram.com/strippindippinchicken/"}, {platform = "website", url = "https://foodtruckleague.com/Utah/trucks/677ec632f7fd49c21152b236"}]
[[footer_blocks]]
  type = "text"
  content = "<p class=\"text-center\"></p>"
[[footer_blocks]]
  type = "text"
  content = "<p class=\"text-center\"></p>"
+++
