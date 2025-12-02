+++
title = "Default Home"
date = "2025-11-26"
draft = false
layout = "home"
description = "Default description."
tags = ["default"]
[[header_blocks]]
  type = "menu"
  orientation = "horizontal"
  alignment = "left"
  style = "pills"
  responsive = "true"
  hamburgerDirection = "sidebar"
  sticky = "true"
  sidebarSide = "left"
  position = "normal"
  items = [{label = "Home", url = "/", type = "page"}, {label = "About", url = "/kennysmom", type = "page"}, {label = "Contact", url = "/over9000", type = "page"}]
  sidebarFooterBlocks = [{type = "markdown", md = "## Hello World\nThis is **markdown** content."}]

[[header_blocks]]
  type = "hero"
  title = "Welcome Home"
  subtitle = "Start your journey here"
  bgImage = "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=1200&q=80"

[[main_blocks]]
  type = "hero"
  title = "Welcome Home"
  subtitle = "Start your journey here"
  bgImage = "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=1200&q=80"

[[main_blocks]]
  type = "text"
  content = "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p><p><br></p><ul><li>helo</li></ul><ol><li><u>underline</u></li></ol><p><a href=\"https://hugo.cloud.djg.dev/\" target=\"_blank\">hyperlink</a></p>"
  css_classes = ""

[[main_blocks]]
  type = "youtube"
  videoId = "dQw4w9WgXcQ"
  title = "My Video"
  width = "91.3%"

[[main_blocks]]
  type = "flex_columns"
  col_widths = "50.0, 50.0"
  [[main_blocks.col_0]]
    type = "image"
    src = "http://hugo.cloud.djg.dev/media/uploads/default/151a432c-3673-45f3-a5e5-3c623c51f68d.png"
    caption = "A beautiful view"
    width = "100%"
    height = "auto"

  [[main_blocks.col_1]]
    type = "image"
    src = "http://hugo.cloud.djg.dev/media/uploads/default/151a432c-3673-45f3-a5e5-3c623c51f68d.png"
    caption = "A beautiful view"
    width = "100%"
    height = "auto"


[[main_blocks]]
  type = "html"
  html = "<div class=\"p-4\">\n  <h3>Custom HTML</h3>\n  <p>Add your HTML here.</p>\n</div>"

[[sidebar_blocks]]
  type = "image"
  src = "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=800&q=80"
  caption = "A beautiful view"
  css_classes = "missing"

[[sidebar_blocks]]
  type = "image"
  src = "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=800&q=80"
  caption = "A beautiful view"
  width = "100%"
  height = "auto"

+++
