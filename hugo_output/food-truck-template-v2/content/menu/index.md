+++
title = "Our Menu"
date = ""
draft = false
layout = "single"
description = "Explore our delicious menu offerings"
[[header_blocks]]
  type = "row"
  gap = "4"
  justify = "space-between"
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
    responsive = true
    hamburgerDirection = "dropdown"
    items = [{label = "Home", url = "/", type = "link"}, {label = "Menu", url = "/menu", type = "link"}, {label = "Packages", url = "/packages", type = "link"}, {label = "About", url = "/about", type = "link"}, {label = "Contact", url = "#contact", type = "link"}]

[[main_blocks]]
  type = "text"
  content = "<h1>Our Menu</h1><p>{{ menu_intro }}</p>"
[[main_blocks]]
  type = "menu_grid"
  title = "Menu Favorites"
  items = [{name = "{{ menu_item_1_name }}", image = "{{ menu_item_1_image }}", description = "{{ menu_item_1_desc }}"}, {name = "{{ menu_item_2_name }}", image = "{{ menu_item_2_image }}", description = "{{ menu_item_2_desc }}"}, {name = "{{ menu_item_3_name }}", image = "{{ menu_item_3_image }}", description = "{{ menu_item_3_desc }}"}, {name = "{{ menu_item_4_name }}", image = "{{ menu_item_4_image }}", description = "{{ menu_item_4_desc }}"}]
[[main_blocks]]
  type = "text"
  content = "<h2>Ready to Book?</h2><p>Check out our catering packages for your next event.</p>"
[[main_blocks]]
  type = "row"
  gap = "4"
  justify = "center"
  align = "center"
  [[main_blocks.blocks]]
    type = "button"
    text = "View Packages"
    url = "/packages"
    style = "primary"
  [[main_blocks.blocks]]
    type = "button"
    text = "Contact Us"
    url = "#contact"
    style = "secondary"

[[footer_blocks]]
  type = "text"
  content = "<p>{{ address }}</p><p>{{ phone }}</p>"
[[footer_blocks]]
  type = "social_links"
  links = [{platform = "facebook", url = "{{ facebook_url }}"}, {platform = "instagram", url = "{{ instagram_url }}"}]
[[footer_blocks]]
  type = "text"
  content = "<p>© 2025 {{ business_name }}. All Rights Reserved.</p>"
+++
