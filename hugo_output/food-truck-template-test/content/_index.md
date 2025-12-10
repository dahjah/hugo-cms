+++
title = "Home"
date = ""
draft = false
type = "single"
description = "Food truck catering for events everyone will remember"
[[header_blocks]]
  type = "row"
  gap = "4"
  justify = "between"
  align = "center"
  [[header_blocks.blocks]]
    type = "brand_logo"
    brand_name = "{{ business_name }}"
    logo_image = ""
    tagline = ""
    link_url = "/"
  [[header_blocks.blocks]]
    type = "menu"
    style = "pills"
    responsive = "false"
    hamburgerDirection = "dropdown"
    alignment = "center"
    items = [{label = "Home", url = "/", type = "link"}, {label = "Menu", url = "/menu", type = "link"}, {label = "Packages", url = "/packages", type = "link"}, {label = "About", url = "/about", type = "link"}, {label = "Contact", url = "#contact", type = "link"}]

[[main_blocks]]
  type = "hero"
  title = "{{ headline }}"
  subtitle = "{{ subheadline }}"
  bgImage = ""
  cta_text = "Book the Truck"
  cta_url = "/packages"
[[main_blocks]]
  type = "features_grid"
  columns = "3"
  items = [{icon = "clock", title = "Reliable Service", description = "Dependable scheduling and clear communication ensure your catering is one less thing to worry about."}, {icon = "truck", title = "Interactive Experience", description = "The food truck itself is a fun, engaging centerpiece for your event, adding personality and flair."}, {icon = "dollar-sign", title = "Transparent Pricing", description = "Clear, upfront pricing eliminates unexpected costs and ensures you can plan confidently within your budget."}]
[[main_blocks]]
  type = "text"
  content = "<h2>{{ pain_point_headline }}</h2><p>{{ pain_point_description }}</p>"
[[main_blocks]]
  type = "process_steps"
  layout = "horizontal"
  steps = [{title = "1. Book Your Experience", description = "Pick your ideal package or request a custom option, confirm your date, and provide us with the event details."}, {title = "2. Stay Connected", description = "Our team keeps you updated with seamless communication as your event day gets closer."}, {title = "3. Savor the Celebration", description = "When the day arrives, our truck rolls in to serve your guests with vibrant cuisine."}]
[[main_blocks]]
  type = "text"
  content = "<h2>What Customers Are Saying</h2>"
[[main_blocks]]
  type = "carousel"
  auto_advance = true
  interval_seconds = "6"
  show_dots = true
  show_arrows = true
  [[main_blocks.blocks]]
    type = "testimonial"
    quote = "{{ testimonial_1_quote }}"
    author = "{{ testimonial_1_author }}"
    image = ""
  [[main_blocks.blocks]]
    type = "testimonial"
    quote = "{{ testimonial_2_quote }}"
    author = "{{ testimonial_2_author }}"
    image = ""

[[main_blocks]]
  type = "accordion"
  allow_multiple = false
  items = [{title = "Will the food be good enough for my guests?", content = "Absolutely! Our menu is crafted with bold, fresh flavors designed to impress even the pickiest eaters."}, {title = "Will the food truck arrive on time?", content = "Yes! Punctuality is our priority. We coordinate logistics well in advance and stay in communication with you."}, {title = "What if the catering costs exceed my budget?", content = "We offer customizable packages to fit a variety of budgets without compromising on quality."}, {title = "Can you accommodate dietary restrictions?", content = "Yes! We offer vegetarian, vegan, and gluten-free options to ensure all your guests can enjoy our food."}, {title = "Is a food truck appropriate for formal events?", content = "Definitely! Our vibrant food truck adds a unique and memorable touch to any event, formal or casual."}]
[[main_blocks]]
  type = "text"
  content = "<h2>Not Quite Ready?</h2><p>Contact us to explore your options or ask questions.</p>"
[[main_blocks]]
  type = "button"
  text = "Book the Truck"
  url = "/packages"
  style = "primary"
[[footer_blocks]]
  type = "text"
  content = "<p>{{ address }}</p><p>{{ phone }}</p>"
[[footer_blocks]]
  type = "social_links"
  links = [{platform = "facebook", url = "{{ facebook_url }}"}, {platform = "instagram", url = "{{ instagram_url }}"}, {platform = "twitter", url = "{{ twitter_url }}"}]
[[footer_blocks]]
  type = "text"
  content = "<p>© 2025 {{ business_name }}. All Rights Reserved.</p>"
+++
