+++
title = "Test Page"
date = ""
draft = false
layout = "list"
[[header_blocks]]
  type = "menu"
  orientation = "horizontal"
  alignment = "left"
  style = "default"
  responsive = "true"
  hamburgerDirection = "dropdown"
  sidebarSide = "left"
  position = "normal"
  items = [{label = "Home", url = "/", type = "page"}, {label = "About", url = "/test-page", type = "page"}, {label = "Contact", url = "https://youtu.be/dQw4w9WgXcQ", type = "external"}]

[[header_blocks]]
  type = "image"
  src = "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=800&q=80"
  caption = "A beautiful view"
  width = "100%"
  height = "auto"

[[main_blocks]]
  type = "text"
  content = "<p><strong>Lorem ipsum </strong>dolor <em>sit amet, consecte</em>tur <u>adipiscing elit.</u></p><ul><li><u>helo</u></li></ul><ol><li><u>s</u><a href=\"https://testing.com\" target=\"_blank\"><u>dfsdfsdf</u></a></li><li><u><span class=\"ql-cursor\">﻿</span></u></li></ol>"

[[main_blocks]]
  type = "flex_columns"
  col_widths = "50.0, 50.0"
  [[main_blocks.col_0]]
    type = "markdown"
    md = "## Hello World\nThis is **markdown** content."

  [[main_blocks.col_1]]
    type = "markdown"
    md = "## Hello World\nThis is **markdown** content."


[[main_blocks]]
  type = "alert"
  message = "This is an important alert message."
  alert_type = "warning"

[[sidebar_blocks]]
  type = "quote"
  text = "Design is intelligence made visible."
  author = "Alina Wheeler"

+++
