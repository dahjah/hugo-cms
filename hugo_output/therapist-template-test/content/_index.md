+++
title = "Home"
date = ""
draft = false
type = "single"
description = "A safe space to find healing, transformation, and growth"
[[header_blocks]]
  type = "brand_logo"
  brand_name = "{{ business_name }}"
  logo_image = ""
  tagline = "{{ tagline_short }}"
  link_url = "/"
[[header_blocks]]
  type = "menu"
  style = "default"
  responsive = true
  hamburgerDirection = "dropdown"
  items = [{label = "Home", url = "/", type = "link"}, {label = "Services", url = "/counseling", type = "link"}, {label = "About", url = "/about", type = "link"}, {label = "Contact", url = "#contact", type = "link"}]
[[main_blocks]]
  type = "hero"
  title = "{{ business_name }}"
  subtitle = "{{ tagline }}"
  bgImage = ""
  cta_text = "Schedule a Consultation"
  cta_url = "#contact"
  tagline = "Healing • Transformation • Growth"
[[main_blocks]]
  type = "text"
  content = "<h2>My Approach to Healing</h2><p>{{ about_approach }}</p>"
[[main_blocks]]
  type = "features_grid"
  columns = "2"
  items = [{icon = "heart", title = "Safe Space", description = "A nurturing environment where you can process your most difficult struggles"}, {icon = "users", title = "Collaborative Partnership", description = "Work together to discover your strengths and goals"}, {icon = "target", title = "Root Cause Healing", description = "Go beyond symptom management to lasting transformation"}, {icon = "compass", title = "Inner Wisdom", description = "Guiding you to your own insights for lasting change"}]
[[main_blocks]]
  type = "text"
  content = "<h3>Why Work With Me?</h3>\n<p>I combine deep empathy, clinical expertise, and evidence-based practices to support your healing journey. My approach is collaborative, compassionate, and tailored to your unique needs.</p>\n<ul>\n<li>Safe, nurturing space where you can process your most difficult struggles</li>\n<li>Collaborative partnership to discover your strengths and goals</li>\n<li>Root cause healing that goes beyond symptom management</li>\n<li>Guiding you to your inner wisdom for lasting transformation</li>\n</ul>"
[[main_blocks]]
  type = "flip_cards"
  title = "My Treatment Philosophy"
  subtitle = "Guiding your transformation"
[[main_blocks]]
  type = "row"
  gap = "6"
  justify = "center"
  align = "stretch"
  [[main_blocks.blocks]]
    type = "column"
    width = "33%"
    [[main_blocks.blocks.blocks]]
      type = "text"
      content = "<h3>Healing</h3><p>Creating a safe space to process trauma, grief, and difficult emotions</p>"

  [[main_blocks.blocks]]
    type = "column"
    width = "33%"
    [[main_blocks.blocks.blocks]]
      type = "text"
      content = "<h3>Transformation</h3><p>Discovering your inner wisdom and resolving root causes</p>"

  [[main_blocks.blocks]]
    type = "column"
    width = "33%"
    [[main_blocks.blocks.blocks]]
      type = "text"
      content = "<h3>Growth</h3><p>Building new skills and confidence for lasting change</p>"


[[main_blocks]]
  type = "text"
  content = "<h2 class=\"text-3xl font-bold text-center mb-4\" style=\"font-family: var(--font-heading);\">What Our Clients Say</h2>"
[[main_blocks]]
  type = "carousel"
  [[main_blocks.blocks]]
    type = "testimonial"
    quote = "Karen provided a safe space for me to process my trauma. Her compassionate approach helped me find healing I never thought possible."
    author = "Former Client"
    image = ""
  [[main_blocks.blocks]]
    type = "testimonial"
    quote = "Working with Karen transformed my life. She helped me discover my inner strength and navigate through my darkest moments."
    author = "Former Client"
    image = ""
  [[main_blocks.blocks]]
    type = "testimonial"
    quote = "I finally feel like myself again. Her expertise in trauma therapy made all the difference in my healing journey."
    author = "Former Client"
    image = ""
[[main_blocks]]
  type = "text"
  content = "<p style=\"text-align: center; color: #666;\">© 2025 Cairn's Counseling Center</p>"
[[main_blocks]]
  type = "row"
  gap = "4"
  justify = "center"
  align = "center"
  [[main_blocks.blocks]]
    type = "button"
    text = "View Services"
    url = "/counseling"
    style = "primary"
  [[main_blocks.blocks]]
    type = "button"
    text = "Free 15-min Consult"
    url = "tel:(801) 528-1329"
    style = "secondary"
  [[main_blocks.blocks]]
    type = "button"
    text = "Client Portal Login"
    url = "https://karenritchie.clientsecure.me"
    style = "outline"
    size = "medium"
    new_tab = true

[[footer_blocks]]
  type = "social_links"
  links = [{platform = "facebook", url = "{{ facebook_url }}"}, {platform = "instagram", url = "{{ instagram_url }}"}]
[[footer_blocks]]
  type = "text"
  content = "<p>© 2025 {{ business_name }}</p>"
+++
