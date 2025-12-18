import json
import os
import re
from django.core.management.base import BaseCommand
from hugo.pipeline.orchestrator import orchestrate

class Command(BaseCommand):
    help = 'Ingest business profile from URLs and save to JSON file.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--urls', 
            nargs='+', 
            required=True, 
            help='List of URLs or handles to scrape (e.g., https://yelp.com/biz/..., @tiktok_user)'
        )
        parser.add_argument(
            '--name', 
            type=str, 
            help='Override/Set business name manually'
        )
        parser.add_argument(
            '--output', 
            type=str, 
            help='Path to save the JSON profile (default: {slug}_profile.json)'
        )

    def handle(self, *args, **options):
        urls = options['urls']
        manual_name = options.get('name')
        custom_output = options.get('output')

        self.stdout.write(self.style.MIGRATE_HEADING("--- Starting Ingestion ---"))
        self.stdout.write(f"Sources: {urls}")

        # Orchestra!
        try:
            profile = orchestrate(urls)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Orchestration Failed: {e}"))
            return

        # Manual overrides
        if manual_name:
            self.stdout.write(f"Overriding name to: {manual_name}")
            profile.name = manual_name
            # Regenerate slug if needed
            if not profile.slug:
                 profile.slug = re.sub(r'[^a-z0-9]+', '-', profile.name.lower()).strip('-')

        # Validation
        if not profile.name:
            self.stdout.write(self.style.ERROR("Failed to determine business name. Use --name to specify manually."))
            return

        # Determine Output Path
        if custom_output:
            output_path = custom_output
        else:
            slug = profile.slug or "unknown_business"
            output_path = f"{slug}_profile.json"

        # Save
        self.stdout.write(f"Saving profile to {output_path}...")
        try:
            data = profile.to_dict()
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.stdout.write(self.style.SUCCESS(f"✓ Profile successfully saved to {output_path}"))
            
            # Summary
            self.stdout.write("\nSummary:")
            self.stdout.write(f" - Name: {profile.name}")
            self.stdout.write(f" - Reviews: {len(profile.reviews)}")
            self.stdout.write(f" - Menu Items: {len(profile.menu_items)}")
            self.stdout.write(f" - Images: {len(profile.gallery_images)}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to save file: {e}"))
