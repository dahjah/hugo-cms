"""
Management command to import an external Hugo site into Hugo CMS.

Usage:
    python manage.py import_hugo_site /path/to/hugo/site "Website Name" website-slug

Example (cairnscounseling):
    python manage.py import_hugo_site ~/projects/cairnscounseling "Therapy Practice" therapy-demo
"""
from django.core.management.base import BaseCommand
from hugo.hugo_importer import import_hugo_site
from hugo.template_service import export_website_to_template


class Command(BaseCommand):
    help = 'Import an external Hugo site into Hugo CMS'

    def add_arguments(self, parser):
        parser.add_argument('hugo_path', type=str, help='Path to the Hugo site root directory')
        parser.add_argument('website_name', type=str, help='Name for the new CMS website')
        parser.add_argument('website_slug', type=str, help='URL slug for the new website')
        parser.add_argument(
            '--create-template',
            type=str,
            default=None,
            help='Create a template from the imported site with the given template ID'
        )
        parser.add_argument(
            '--template-name',
            type=str,
            default=None,
            help='Display name for the template (defaults to website name)'
        )
        parser.add_argument(
            '--template-category',
            type=str,
            default=None,
            help='Category slug for the template'
        )

    def handle(self, *args, **options):
        hugo_path = options['hugo_path']
        website_name = options['website_name']
        website_slug = options['website_slug']
        
        self.stdout.write(f'Importing Hugo site from: {hugo_path}')
        self.stdout.write(f'Creating website: {website_name} ({website_slug})')
        
        try:
            # Import the Hugo site
            website = import_hugo_site(hugo_path, website_name, website_slug)
            
            self.stdout.write(self.style.SUCCESS(
                f'✓ Successfully imported Hugo site as: {website.name}'
            ))
            
            # Show imported pages
            from hugo.models import Page, BlockInstance
            pages = Page.objects.filter(website=website)
            for page in pages:
                block_count = BlockInstance.objects.filter(page=page).count()
                self.stdout.write(f'  - {page.title} ({page.slug}): {block_count} blocks')
            
            # Create template if requested
            if options['create_template']:
                template_id = options['create_template']
                template_name = options['template_name'] or website_name
                template_category = options['template_category']
                
                self.stdout.write(f'\nCreating template: {template_id}')
                
                template = export_website_to_template(
                    website_id=website.id,
                    template_id=template_id,
                    name=template_name,
                    description=f'Imported from {hugo_path}',
                    category_slug=template_category
                )
                
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Created template: {template.name} ({template.id})'
                ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing Hugo site: {e}'))
            raise
