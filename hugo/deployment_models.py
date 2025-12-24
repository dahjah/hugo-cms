from django.db import models
from django.db.models import JSONField

import uuid


class DeploymentProvider(models.Model):
    """
    Configuration for deployment provider (Cloudflare R2, Netlify, Vercel, etc.)
    """
    PROVIDER_TYPES = [
        ('cloudflare_pages', 'Cloudflare Pages'),
        ('cloudflare_r2', 'Cloudflare R2 (Legacy)'),
        ('netlify', 'Netlify'),
        ('vercel', 'Vercel'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, default="New Provider")
    provider_type = models.CharField(max_length=50, choices=PROVIDER_TYPES, default='cloudflare_pages')
    enabled = models.BooleanField(default=False, help_text="Enable automatic deployment on publish")
    is_default = models.BooleanField(default=False, help_text="Make this the default provider for new websites")
    
    # Cloudflare configuration (shared between Pages and R2)
    cf_account_id = models.CharField(max_length=200, blank=True, help_text="Cloudflare Account ID")
    cf_api_token = models.CharField(max_length=200, blank=True, help_text="Cloudflare API Token with Pages and DNS permissions")
    cf_zone_id = models.CharField(max_length=200, blank=True, help_text="Cloudflare Zone ID (for custom domain DNS)")
    custom_domain = models.CharField(max_length=200, blank=True, help_text="Base custom domain (e.g., monu.dev)")
    
    # Cloudflare Pages specific fields  
    pages_project_name = models.CharField(max_length=200, blank=True, help_text="Pages project name (optional, auto-generated if empty)")
    
    # Legacy R2 fields (kept for backward compatibility)
    cf_r2_access_key = models.CharField(max_length=200, blank=True, help_text="[Legacy] R2 Access Key ID")
    cf_r2_secret_key = models.CharField(max_length=200, blank=True, help_text="[Legacy] R2 Secret Access Key")
    cf_bucket_name = models.CharField(max_length=200, blank=True, help_text="[Legacy] R2 Bucket Name")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Deployment Provider"
        verbose_name_plural = "Deployment Providers"
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default:
            # Unset is_default for all other providers
            DeploymentProvider.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class DeploymentHistory(models.Model):
    """
    Track deployment history and status for each publish action
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('building', 'Building'),
        ('uploading', 'Uploading'),
        ('configuring', 'Configuring Domain'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='deployments')
    deployment_provider = models.ForeignKey(DeploymentProvider, on_delete=models.CASCADE, related_name='deployments')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    deployment_url = models.URLField(blank=True, null=True, help_text="URL where the site is deployed")
    
    # Build info
    hugo_version = models.CharField(max_length=50, blank=True)
    build_duration_seconds = models.FloatField(null=True, blank=True)
    
    # Deployment details
    files_uploaded = models.IntegerField(default=0)
    total_size_bytes = models.BigIntegerField(default=0)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    error_traceback = models.TextField(blank=True)
    
    # Metadata
    build_output = models.TextField(blank=True, help_text="Hugo build output logs")
    deployment_metadata = JSONField(default=dict, blank=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Deployment History"
        verbose_name_plural = "Deployment Histories"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.website.name} - {self.status} at {self.started_at}"
