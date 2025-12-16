
import os
import django
import sys
from pathlib import Path

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hugo.models import Website
from hugo.deployment_models import DeploymentProvider
from hugo.deployment_service import DeploymentOrchestrator

def deploy():
    try:
        # Get Website
        website = Website.objects.get(slug='strippin-v2')
        print(f"Found Website: {website.name}")
        
        # Get Provider
        try:
            provider = DeploymentProvider.objects.get(name='Monudev Cloudflare Pages')
        except DeploymentProvider.DoesNotExist:
            print("Provider 'Monudev Cloudflare Pages' not found!")
            print("Available Providers:")
            for p in DeploymentProvider.objects.all():
                print(f" - {p.name} ({p.provider_type})")
            return

        print(f"Using Provider: {provider.name}")

        # Deploy
        orchestrator = DeploymentOrchestrator(provider, website)
        
        source_dir = Path(os.getcwd()) / 'hugo_output' / 'strippin-v2'
        print(f"Starting Deployment from source: {source_dir}...")
        
        deployment = orchestrator.deploy(source_dir)
        
        print(f"Deployment Status: {deployment.status}")
        if deployment.error_message:
            print(f"Error: {deployment.error_message}")
        else:
             print(f"Deployed URL: {deployment.deployment_url}")
            
    except Exception as e:
        print(f"Deployment Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deploy()
