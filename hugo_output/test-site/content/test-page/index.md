---
{
  "title": "Test Page",
  "layout": "list",
  "main_blocks": [
    {
      "content": "<p><strong>Lorem ipsum </strong>dolor <em>sit amet, consecte</em>tur <u>adipiscing elit.</u></p><ul><li><u>helo</u></li></ul><ol><li><u>s</u><a href=\"https://testing.com\" target=\"_blank\"><u>dfsdfsdf</u></a></li><li><u><span class=\"ql-cursor\">\ufeff</span></u></li></ol>",
      "type": "text"
    },
    {
      "type": "row",
      "flex_mode": true,
      "gap": "2",
      "blocks": [
        {
          "type": "column",
          "width_percent": "50.0",
          "blocks": [
            {
              "md": "## Hello World\nThis is **markdown** content.",
              "type": "markdown"
            }
          ]
        },
        {
          "type": "column",
          "width_percent": "50.0",
          "blocks": [
            {
              "md": "## Hello World\nThis is **markdown** content.",
              "type": "markdown"
            }
          ]
        }
      ]
    },
    {
      "message": "This is an important alert message.",
      "alert_type": "warning",
      "type": "alert"
    }
  ]
}
---
