+++
title = "Test Page 3"
date = ""
draft = false
layout = "list"
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
  type = "text"
  content = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."

[[sidebar_blocks]]
  type = "image"
  src = "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=800&q=80"
  caption = "A beautiful view"

+++
