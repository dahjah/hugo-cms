"""
Deployment service layer for building and deploying Hugo sites.
Supports Cloudflare R2 with custom domain configuration.
"""
import subprocess
import os
import time
from pathlib import Path
from django.conf import settings
from django.utils import timezone
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class HugoBuilder:
    """
    Build Hugo static sites from source files.
    """
    def __init__(self, hugo_binary_path=None):
        self.hugo_binary = hugo_binary_path or os.path.join(settings.BASE_DIR, 'bin', 'hugo')
        
    def build(self, source_dir, output_dir=None, minify=True):
        """
        Build Hugo site to static files.
        
        Args:
            source_dir: Path to Hugo source directory (with hugo.toml)
            output_dir: Where to output the built site (default: source_dir/public)
            minify: Whether to minify output
            
        Returns:
            dict with:
                - success: bool
                - output_dir: Path to built site
                - build_output: stdout from Hugo
                - duration_seconds: build time
                - error: error message if failed
        """
        start_time = time.time()
        source_path = Path(source_dir)
        
        if not source_path.exists():
            return {
                'success': False,
                'error': f'Source directory does not exist: {source_dir}'
            }
        
        # Default output dir
        if output_dir is None:
            output_dir = source_path / 'public'
        else:
            output_dir = Path(output_dir)
        
        # Build command
        cmd = [str(self.hugo_binary), '--source', str(source_path)]
        
        if minify:
            cmd.append('--minify')
        
        if output_dir != source_path / 'public':
            cmd.extend(['--destination', str(output_dir)])
        
        try:
            logger.info(f"Running Hugo build: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=str(source_path),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'build_output': result.stdout + '\n' + result.stderr,
                    'duration_seconds': duration,
                    'error': f'Hugo build failed with exit code {result.returncode}'
                }
            
            return {
                'success': True,
                'output_dir': str(output_dir),
                'build_output': result.stdout,
                'duration_seconds': duration
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Hugo build timed out after 5 minutes',
                'duration_seconds': time.time() - start_time
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration_seconds': time.time() - start_time
            }
    
    def get_version(self):
        """Get Hugo version."""
        try:
            result = subprocess.run(
                [str(self.hugo_binary), 'version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return 'unknown'
        except Exception:
            return 'unknown'


class CloudflareR2Deployer:
    """
    Deploy static sites to Cloudflare R2 and configure custom domains.
    """
    def __init__(self, deployment_provider):
        """
        Args:
            deployment_provider: DeploymentProvider model instance
        """
        self.provider = deployment_provider
        self.account_id = deployment_provider.cf_account_id
        self.bucket_name = deployment_provider.cf_bucket_name
        
        # Initialize S3-compatible client for R2
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=deployment_provider.cf_r2_access_key,
            aws_secret_access_key=deployment_provider.cf_r2_secret_key,
            region_name='auto'  # R2 uses 'auto' region
        )
    
    def upload_directory(self, local_dir, prefix=''):
        """
        Upload entire directory to R2 bucket.
        
        Args:
            local_dir: Path to directory to upload
            prefix: S3 prefix (folder) to upload to
            
        Returns:
            dict with:
                - success: bool
                - files_uploaded: int
                - total_size_bytes: int
                - error: error message if failed
        """
        local_path = Path(local_dir)
        
        if not local_path.exists() or not local_path.is_dir():
            return {
                'success': False,
                'error': f'Local directory does not exist: {local_dir}'
            }
        
        files_uploaded = 0
        total_size = 0
        errors = []
        
        # Walk through all files
        for file_path in local_path.rglob('*'):
            if file_path.is_file():
                # Calculate S3 key
                rel_path = file_path.relative_to(local_path)
                s3_key = str(Path(prefix) / rel_path) if prefix else str(rel_path)
                
                # Determine content type
                content_type = self._get_content_type(file_path)
                
                try:
                    # Upload file
                    self.s3_client.upload_file(
                        str(file_path),
                        self.bucket_name,
                        s3_key,
                        ExtraArgs={'ContentType': content_type}
                    )
                    files_uploaded += 1
                    total_size += file_path.stat().st_size
                    logger.info(f"Uploaded: {s3_key}")
                    
                except ClientError as e:
                    error_msg = f"Failed to upload {s3_key}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
        
        if errors:
            return {
                'success': False,
                'files_uploaded': files_uploaded,
                'total_size_bytes': total_size,
                'error': '\n'.join(errors)
            }
        
        return {
            'success': True,
            'files_uploaded': files_uploaded,
            'total_size_bytes': total_size
        }
    
    def _get_content_type(self, file_path):
        """Determine content type based on file extension."""
        import mimetypes
        content_type, _ = mimetypes.guess_type(str(file_path))
        return content_type or 'application/octet-stream'
    
    def configure_custom_domain(self, domain):
        """
        Configure custom domain for R2 bucket via Cloudflare API.
        
        Args:
            domain: Domain name (e.g., site1.monu.dev)
            
        Returns:
            dict with success status and any errors
        """
        import requests
        
        if not self.provider.cf_api_token:
            return {
                'success': False,
                'error': 'Cloudflare API token not configured'
            }
        
        headers = {
            'Authorization': f'Bearer {self.provider.cf_api_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Configure R2 bucket custom domain
            url = f'https://api.cloudflare.com/client/v4/accounts/{self.account_id}/r2/buckets/{self.bucket_name}/domains'
            
            payload = {
                'domain': domain
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                logger.info(f"Custom domain configured: {domain}")
                return {'success': True}
            else:
                error_msg = response.json().get('errors', [{}])[0].get('message', 'Unknown error')
                logger.error(f"Failed to configure custom domain: {error_msg}")
                return {
                    'success': False,
                    'error': f'Cloudflare API error: {error_msg}'
                }
                
        except Exception as e:
            logger.exception(f"Error configuring custom domain: {domain}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_dns_record(self, zone_id, domain, target):
        """
        Create CNAME DNS record pointing to R2 bucket.
        
        Args:
            zone_id: Cloudflare zone ID for monu.dev
            domain: Full domain name (e.g., site1.monu.dev)
            target: Target CNAME (R2 bucket URL)
            
        Returns:
            dict with success status
        """
        import requests
        
        if not self.provider.cf_api_token:
            return {
                'success': False,
                'error': 'Cloudflare API token not configured'
            }
        
        headers = {
            'Authorization': f'Bearer {self.provider.cf_api_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Extract subdomain from full domain
            subdomain = domain.split('.')[0]
            
            # Create DNS record
            url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records'
            
            payload = {
                'type': 'CNAME',
                'name': subdomain,
                'content': target,
                'ttl': 1,  # Auto
                'proxied': False  # Don't proxy through Cloudflare
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                logger.info(f"DNS record created: {domain} -> {target}")
                return {'success': True}
            else:
                # Check if record already exists
                data = response.json()
                errors = data.get('errors', [])
                if any('already exists' in str(err).lower() for err in errors):
                    logger.info(f"DNS record already exists: {domain}")
                    return {'success': True, 'already_exists': True}
                
                error_msg = errors[0].get('message', 'Unknown error') if errors else 'Unknown error'
                logger.error(f"Failed to create DNS record: {error_msg}")
                return {
                    'success': False,
                    'error': f'Cloudflare DNS API error: {error_msg}'
                }
                
        except Exception as e:
            logger.exception(f"Error creating DNS record: {domain}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_deployment_url(self):
        """
        Get the deployment URL for the site.
        Returns custom domain if configured, otherwise R2 public URL.
        """
        if self.provider.custom_domain:
            return f"https://{self.provider.custom_domain}"
        else:
            # R2 public URL format
            return f"https://{self.bucket_name}.{self.account_id}.r2.cloudflarestorage.com"


class DeploymentOrchestrator:
    """
    Orchestrate the full deployment process: build + upload + configure.
    """
    def __init__(self, deployment_provider):
        self.provider = deployment_provider
        self.website = deployment_provider.website
        self.builder = HugoBuilder()
        self.deployer = CloudflareR2Deployer(deployment_provider)
    
    def deploy(self, source_dir):
        """
        Execute full deployment: build Hugo site and upload to R2.
        
        Args:
            source_dir: Path to Hugo source directory
            
        Returns:
            DeploymentHistory instance with results
        """
        from .deployment_models import DeploymentHistory
        
        # Create deployment history record
        deployment = DeploymentHistory.objects.create(
            website=self.website,
            deployment_provider=self.provider,
            status='building',
            hugo_version=self.builder.get_version()
        )
        
        try:
            # Step 1: Build Hugo site
            logger.info(f"Building Hugo site for {self.website.name}")
            build_result = self.builder.build(source_dir, minify=True)
            
            deployment.build_output = build_result.get('build_output', '')
            deployment.build_duration_seconds = build_result.get('duration_seconds', 0)
            
            if not build_result['success']:
                deployment.status = 'failed'
                deployment.error_message = build_result.get('error', 'Unknown build error')
                deployment.completed_at = timezone.now()
                deployment.save()
                return deployment
            
            # Step 2: Upload to R2
            logger.info(f"Uploading to Cloudflare R2: {self.provider.cf_bucket_name}")
            deployment.status = 'uploading'
            deployment.save()
            
            upload_result = self.deployer.upload_directory(build_result['output_dir'])
            
            deployment.files_uploaded = upload_result.get('files_uploaded', 0)
            deployment.total_size_bytes = upload_result.get('total_size_bytes', 0)
            
            if not upload_result['success']:
                deployment.status = 'failed'
                deployment.error_message = upload_result.get('error', 'Unknown upload error')
                deployment.completed_at = timezone.now()
                deployment.save()
                return deployment
            
            # Step 3: Configure DNS and Custom Domain
            if self.provider.custom_domain and self.provider.cf_api_token:
                logger.info(f"Configuring custom domain: {self.provider.custom_domain}")
                deployment.status = 'configuring'
                deployment.save()
                
                # Configure R2 custom domain
                domain_result = self.deployer.configure_custom_domain(self.provider.custom_domain)
                
                if not domain_result['success']:
                    logger.warning(f"Custom domain configuration failed: {domain_result.get('error')}")
                    # Don't fail deployment, just log warning
                
                # Create DNS CNAME record if zone_id is provided
                if self.provider.cf_zone_id:
                    # Target is the R2 bucket public URL  
                    target = f"{self.provider.cf_bucket_name}.{self.provider.cf_account_id}.r2.cloudflarestorage.com"
                    dns_result = self.deployer.create_dns_record(
                        self.provider.cf_zone_id,
                        self.provider.custom_domain,
                        target
                    )
                    
                    if not dns_result['success']:
                        logger.warning(f"DNS record creation failed: {dns_result.get('error')}")
                        # Don't fail deployment, just log warning
            
            # Step 4: Success
            deployment.status = 'success'
            deployment.deployment_url = self.deployer.get_deployment_url()
            deployment.completed_at = timezone.now()
            deployment.save()
            
            logger.info(f"Deployment successful: {deployment.deployment_url}")
            return deployment
            
        except Exception as e:
            logger.exception(f"Deployment failed for {self.website.name}")
            deployment.status = 'failed'
            deployment.error_message = str(e)
            deployment.error_traceback = __import__('traceback').format_exc()
            deployment.completed_at = timezone.now()
            deployment.save()
            return deployment
