
from django.core.management import call_command
from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
import os
import json
from hugo.schemas import BusinessProfile

class IngestProfileCommandTest(TestCase):
    def setUp(self):
        self.output_file = "test_profile_output.json"

    def tearDown(self):
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    @patch('hugo.management.commands.ingest_profile.orchestrate')
    def test_ingest_profile_command(self, mock_orchestrate):
        # Setup Mock
        mock_profile = BusinessProfile(
            name="Test Biz",
            slug="test-biz",
            description="A test business",
            reviews=[{'text': 'Great', 'rating': 5}],
            social_links=[{'platform': 'tiktok', 'url': 'http://tiktok.com/@test'}]
        )
        mock_orchestrate.return_value = mock_profile

        # Execute Command
        call_command(
            'ingest_profile', 
            urls=['https://test.com'], 
            output=self.output_file,
            stdout=MagicMock()
        )

        # Verify
        mock_orchestrate.assert_called_once_with(['https://test.com'])
        self.assertTrue(os.path.exists(self.output_file))
        
        with open(self.output_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(data['name'], "Test Biz")
            self.assertEqual(data['slug'], "test-biz")
            self.assertEqual(len(data['reviews']), 1)
