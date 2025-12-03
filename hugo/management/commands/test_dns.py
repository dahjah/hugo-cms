from django.core.management.base import BaseCommand
from hugo.deployment_models import DeploymentProvider
from hugo.models import Website
from hugo.deployment_service import CloudflarePagesDeployer
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class Command(BaseCommand):
    help = 'Test DNS record creation for default.monu.dev'
    def handle(self, *args, **options):
        # Get the Pages provider and website
        provider = DeploymentProvider.objects.filter(provider_type='cloudflare_pages').first()
        website = Website.objects.first()
        
        if not provider:
            self.stdout.write(self.style.ERROR('No Pages provider found'))
            return
            
        self.stdout.write(f'Provider: {provider.name}')
        self.stdout.write(f'Zone ID: {provider.cf_zone_id}')
        self.stdout.write(f'Custom Domain: {provider.custom_domain}')
        self.stdout.write(f'Website: {website.name} ({website.slug})')
        
        # Create deployer
        deployer = CloudflarePagesDeployer(provider, website)
        
        # Test DNS creation
        full_domain = f"{website.slug}.{provider.custom_domain}"
        self.stdout.write(f'\nAttempting to create DNS record for: {full_domain}')
        
        result = deployer.create_dns_record(provider.cf_zone_id, full_domain)
        
        if result['success']:
            self.stdout.write(self.style.SUCCESS(f'✓ DNS record created successfully!'))
        else:
            self.stdout.write(self.style.ERROR(f'✗ DNS creation failed: {result.get("error")}'))