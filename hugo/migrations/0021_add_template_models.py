"""
Migration to add SiteTemplate and TemplateCategory models for the template system.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hugo', '0020_add_cairns_blocks'),
    ]

    operations = [
        migrations.CreateModel(
            name='TemplateCategory',
            fields=[
                ('slug', models.CharField(help_text='URL-friendly identifier', max_length=50, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Display name for the category', max_length=100)),
                ('description', models.TextField(blank=True)),
                ('order', models.IntegerField(default=0, help_text='Sort order in template gallery')),
            ],
            options={
                'verbose_name_plural': 'Template Categories',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='SiteTemplate',
            fields=[
                ('id', models.CharField(help_text="URL-friendly identifier (e.g., 'therapy', 'food-truck')", max_length=50, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Display name for the template', max_length=100)),
                ('description', models.TextField(blank=True)),
                ('thumbnail_url', models.CharField(blank=True, help_text='Preview image URL', max_length=500)),
                ('base_css', models.TextField(blank=True, help_text='CSS variables and base styles')),
                ('pages_json', models.JSONField(default=list, help_text='Serialized pages with blocks: [{slug, title, layout, blocks: [...]}]')),
                ('created_by', models.CharField(blank=True, help_text='Attribution for template creator', max_length=100)),
                ('is_featured', models.BooleanField(default=False, help_text='Show prominently in template gallery')),
                ('is_public', models.BooleanField(default=True, help_text='Available to all users')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='templates', to='hugo.templatecategory')),
            ],
            options={
                'ordering': ['-is_featured', 'name'],
            },
        ),
    ]
