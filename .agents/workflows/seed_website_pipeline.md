---
description: Seed a New Website using the Ingestion & Scraper Pipeline
---
# Seed a New Website via Scrapers

This workflow outlines how to execute the site builder pipeline to automatically generate a brand new website from external data sources.

The pipeline is capable of ingesting data from **Yelp**, **Instagram**, and the **Food Truck League**, extracting brand colors from logos, identifying missing content gaps compared to the target template, using an LLM to synthesize copy (hero text, features, about us, FAQ, and menu items), and seamlessly constructing the final `Website` and `Page` records in the database!

### Prerequisites
- The target template (e.g., `food-truck-v2`, `cairns-v1`, `mambo-v1`) must already exist in the database (usually defined in `SiteTemplate`).
- You must find the correct URLs for the business across the platforms you intend to scrape.

---

### Option A: Direct CLI Ingestion (Data Extraction Only)
If you simply want to fire off the scrapers and save the structured profile output without generating a full Django website or triggering the LLM, you can use the built-in single-line command:

// turbo
```bash
python manage.py ingest_profile --urls https://www.yelp.com/biz/mybiz https://www.instagram.com/mybiz --name "My Business" --output "my_business_profile.json"
```

---

### Option B: Full Pipeline Orchestration (End-to-End Site Build)
If you want to ingest the data *and* seamlessly construct the `Website`, `Page`, and LLM-synthesized `BlockInstance` records inside the database, you must utilize an orchestrator script.

#### Step 1: Duplicate an Orchestration Script
```bash
cp hugo/management/commands/orchestrate_strippin.py hugo/management/commands/orchestrate_my_business.py
```

#### Step 2: Configure the Data Sources
Open your newly created orchestrator (`orchestrate_my_business.py`) and modify the **Inputs** section at the very top of the `handle()` function.

1. **Set the business URLs**:
```python
yelp_url = "https://www.yelp.com/biz/my-cool-business"
insta_url = "https://www.instagram.com/mycoolbusiness/"
ftl_url = "https://foodtruckleague.com/Utah/trucks/12345"
```

2. **Define the Business Name and Output Target**:
```python
profile_path = "my_business_profile.json"
# ... inside the `else:` block
profile = BusinessProfile(name="My Cool Business")
```

#### Step 3: Configure Template and Slug
Further down the script, update the `SiteTemplate` slug you wish to map the data against, and the `slug` the final generated `Website` will use in the database.

1. **Set the Template Extraction Target**:
```python
template = SiteTemplate.objects.get(slug='food-truck-v2')
```
2. **Set the Ingestion Site Slug**:
```python
site_slug = "my-cool-business-v1"
```

#### Step 4: Execute the Pipeline

Run your custom management command:

// turbo
```bash
python manage.py orchestrate_my_business
```

**What happens during execution:**
1. **Scraping**: Invokes the auto-detected scrapers.
2. **Color Extraction**: Uses `extract_colors_from_url` to derive a CSS theme from the logo.
3. **Gap Analysis**: Compares the scraped profile against the requested `SiteTemplate`'s required blocks.
4. **LLM Synthesis**: Passes the profile and missing parameters to `generate_site_copy()`.
5. **Database Ingestion**: Downloads media assets locally and saves the `BlockInstances` and `Website` final records to the DB.
