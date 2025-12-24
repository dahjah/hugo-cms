---
{
  "title": "Our Menu",
  "description": "Explore our delicious menu offerings",
  "layout": "single",
  "header_blocks": [
    {
      "gap": "4",
      "justify": "space-between",
      "align": "center",
      "id": "55179596-31bd-4f63-8498-14de13f6c6a6",
      "block_type": "row",
      "blocks": [
        {
          "brand_name": "Mad Taco AZ",
          "logo_image": "/media/uploads/mad-taco-az/618c53e7-3eb6-4c4e-887b-2680d5559056.png",
          "tagline": "",
          "link_url": "/",
          "id": "7e7f99a7-9e98-4e04-900f-8304233374b2",
          "block_type": "brand_logo"
        },
        {
          "items": [
            {
              "label": "Home",
              "url": "/",
              "type": "link"
            },
            {
              "label": "Menu",
              "url": "/menu",
              "type": "link"
            },
            {
              "label": "Packages",
              "url": "/packages",
              "type": "link"
            },
            {
              "label": "About",
              "url": "/about",
              "type": "link"
            },
            {
              "label": "Contact",
              "url": "#contact",
              "type": "link"
            }
          ],
          "style": "pills",
          "responsive": true,
          "hamburgerDirection": "dropdown",
          "id": "27a0e058-75bc-43ae-825e-e957c6a7b738",
          "block_type": "menu"
        }
      ]
    }
  ],
  "main_blocks": [
    {
      "content": "<h1>Our Menu</h1><p>{{ menu_intro }}</p>",
      "id": "7f2a0b6c-cd48-4630-8866-d024aa0c1eda",
      "block_type": "text"
    },
    {
      "title": "Menu Favorites",
      "items": [
        {
          "name": "{{ menu_item_1_name }}",
          "image": "{{ menu_item_1_image }}",
          "description": "{{ menu_item_1_desc }}"
        },
        {
          "name": "{{ menu_item_2_name }}",
          "image": "{{ menu_item_2_image }}",
          "description": "{{ menu_item_2_desc }}"
        },
        {
          "name": "{{ menu_item_3_name }}",
          "image": "{{ menu_item_3_image }}",
          "description": "{{ menu_item_3_desc }}"
        },
        {
          "name": "{{ menu_item_4_name }}",
          "image": "{{ menu_item_4_image }}",
          "description": "{{ menu_item_4_desc }}"
        }
      ],
      "id": "5188b6a9-ec19-4bb5-89f5-2c8924fd32da",
      "block_type": "menu_grid"
    },
    {
      "content": "<h2>Ready to Book?</h2><p>Check out our catering packages for your next event.</p>",
      "id": "ccf2987a-b37e-429f-afd9-a5cb20550d69",
      "block_type": "text"
    },
    {
      "gap": "4",
      "justify": "center",
      "align": "center",
      "id": "4bcf2443-2657-4217-bf7c-c578d827363e",
      "block_type": "row",
      "blocks": [
        {
          "text": "View Packages",
          "url": "/packages",
          "style": "primary",
          "id": "bbbd1810-5e6f-4897-9ac3-4f4dc238f4e6",
          "block_type": "button"
        },
        {
          "text": "Contact Us",
          "url": "#contact",
          "style": "secondary",
          "id": "5efb6c95-652e-464f-bf0a-91494af85967",
          "block_type": "button"
        }
      ]
    }
  ],
  "footer_blocks": [
    {
      "content": "<p>{{ address }}</p><p>{{ phone }}</p>",
      "id": "40fd692f-96cd-4c2c-9fd9-e1b6f216d1db",
      "block_type": "text"
    },
    {
      "links": [
        {
          "platform": "facebook",
          "url": "{{ facebook_url }}"
        },
        {
          "platform": "instagram",
          "url": "{{ instagram_url }}"
        }
      ],
      "id": "d30b4992-e037-41b1-832b-a719e7fab6e1",
      "block_type": "social_links"
    },
    {
      "content": "<p>\u00a9 2025 {{ business_name }}. All Rights Reserved.</p>",
      "id": "8115f871-36b3-45e2-8ebc-8388ca5f46c0",
      "block_type": "text"
    }
  ]
}
---
