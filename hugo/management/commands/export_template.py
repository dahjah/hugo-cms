"""
Export a website to a reusable SiteTemplate.

Usage:
    python manage.py export_template <website_slug> <template_slug> --name="Template Name" --tags=therapist,healthcare

Example:
    python manage.py export_template cairns-counseling therapist-modern --name="Modern Therapist" --tags=therapist,healthcare,counseling
"""
from django.core.management.base import BaseCommand, CommandError
from hugo.models import Website, SiteTemplate
from hugo.template_service import export_website_to_template


class Command(BaseCommand):
    help = 'Export a website to a reusable SiteTemplate'

    def add_arguments(self, parser):
        parser.add_argument(
            'website_slug',
            type=str,
            help='Slug of the website to export'
        )
        parser.add_argument(
            'template_slug',
            type=str,
            help='URL-friendly slug for the new template (e.g., therapist-modern)'
        )
        parser.add_argument(
            '--name',
            type=str,
            default=None,
            help='Display name for the template. Defaults to website name + " Template"'
        )
        parser.add_argument(
            '--description',
            type=str,
            default='',
            help='Description of the template'
        )
        parser.add_argument(
            '--tags',
            type=str,
            default='',
            help='Comma-separated list of tags for LLM matching (e.g., therapist,healthcare)'
        )
        parser.add_argument(
            '--thumbnail',
            type=str,
            default='',
            help='URL to a thumbnail image for the template gallery'
        )
        parser.add_argument(
            '--created-by',
            type=str,
            default='',
            help='Attribution for the template creator'
        )

    def handle(self, *args, **options):
        website_slug = options['website_slug']
        template_slug = options['template_slug']
        
        # Find the website
        try:
            website = Website.objects.get(slug=website_slug)
        except Website.DoesNotExist:
            raise CommandError(f'Website with slug "{website_slug}" does not exist.')
        
        # Parse tags
        tags = []
        if options['tags']:
            tags = [tag.strip() for tag in options['tags'].split(',') if tag.strip()]
        
        # Default name if not provided
        name = options['name'] or f"{website.name} Template"
        
        # Check if template already exists
        existing = SiteTemplate.objects.filter(slug=template_slug).first()
        action = 'Updated' if existing else 'Created'
        
        self.stdout.write(f'Exporting website "{website.name}" to template "{template_slug}"...')
        
        template = export_website_to_template(
            website_id=website.id,
            template_slug=template_slug,
            name=name,
            description=options['description'],
            tags=tags,
            thumbnail_url=options['thumbnail'],
            created_by=options['created_by']
        )
        
        # Count what was exported
        pages_data = template.pages_json.get('pages', []) if isinstance(template.pages_json, dict) else []
        global_blocks = template.pages_json.get('global_blocks', []) if isinstance(template.pages_json, dict) else []
        
        total_blocks = 0
        for page in pages_data:
            total_blocks += self._count_blocks(page.get('blocks', []))
        for block in global_blocks:
            total_blocks += 1 + self._count_blocks(block.get('children', []))
        
        self.stdout.write(self.style.SUCCESS(
            f'{action} template "{template.name}" (slug: {template.slug})\n'
            f'  - Pages: {len(pages_data)}\n'
            f'  - Global blocks (header/footer): {len(global_blocks)}\n'
            f'  - Total blocks: {total_blocks}\n'
            f'  - Tags: {tags or "(none)"}\n'
            f'  - CSS: {"Yes" if template.base_css else "No"}'
        ))
    
    def _count_blocks(self, blocks):
        """Recursively count blocks including children."""
        count = len(blocks)
        for block in blocks:
            children = block.get('children', [])
            if isinstance(children, list):
                count += self._count_blocks(children)
        return count
