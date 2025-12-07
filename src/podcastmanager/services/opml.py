"""
OPML import/export service.

This module handles importing and exporting podcast subscriptions in OPML format,
allowing users to migrate between podcast applications.
"""

from datetime import datetime
from io import BytesIO
from typing import List, Optional, Dict
from xml.etree import ElementTree as ET

from loguru import logger

from podcastmanager.db.models import Podcast


class OPMLService:
    """
    Service for handling OPML import and export.

    OPML (Outline Processor Markup Language) is a standard XML format
    used by podcast applications to share subscription lists.
    """

    @staticmethod
    def parse_opml(opml_content: bytes) -> List[Dict[str, str]]:
        """
        Parse an OPML file and extract podcast RSS feeds.

        Args:
            opml_content: Raw OPML file content (bytes)

        Returns:
            List of dictionaries with podcast information:
            [
                {
                    'title': 'Podcast Name',
                    'rss_url': 'https://...',
                    'description': '...',
                    'website_url': '...'
                }
            ]
        """
        try:
            # Parse XML
            tree = ET.parse(BytesIO(opml_content))
            root = tree.getroot()

            podcasts = []

            # Find all outline elements (podcasts are typically in outline elements)
            # OPML can have nested outlines (categories), so we search recursively
            for outline in root.iter('outline'):
                # Check if this outline represents a podcast
                # Podcasts typically have type="rss" and xmlUrl attribute
                outline_type = outline.get('type', '').lower()
                xml_url = outline.get('xmlUrl') or outline.get('xmlurl')

                if xml_url and (outline_type == 'rss' or not outline_type):
                    podcast_info = {
                        'title': outline.get('text') or outline.get('title', 'Unknown Podcast'),
                        'rss_url': xml_url,
                        'description': outline.get('description', ''),
                        'website_url': outline.get('htmlUrl') or outline.get('htmlurl', ''),
                    }
                    podcasts.append(podcast_info)

            logger.info(f"Parsed OPML file: found {len(podcasts)} podcasts")
            return podcasts

        except ET.ParseError as e:
            logger.error(f"Failed to parse OPML XML: {e}")
            raise ValueError(f"Invalid OPML file: {e}")
        except Exception as e:
            logger.error(f"Error parsing OPML: {e}")
            raise

    @staticmethod
    def generate_opml(podcasts: List[Podcast], title: str = "Podcast Subscriptions") -> str:
        """
        Generate an OPML file from a list of podcasts.

        Args:
            podcasts: List of Podcast objects to export
            title: Title for the OPML file

        Returns:
            OPML content as a string (XML)
        """
        try:
            # Create root OPML element
            opml = ET.Element('opml', version='2.0')

            # Create head element
            head = ET.SubElement(opml, 'head')
            title_elem = ET.SubElement(head, 'title')
            title_elem.text = title

            date_created = ET.SubElement(head, 'dateCreated')
            date_created.text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

            # Create body element
            body = ET.SubElement(opml, 'body')

            # Add podcasts as outline elements
            for podcast in podcasts:
                outline = ET.SubElement(
                    body,
                    'outline',
                    type='rss',
                    text=podcast.title,
                    title=podcast.title,
                    xmlUrl=podcast.rss_url
                )

                # Add optional attributes
                if podcast.description:
                    outline.set('description', podcast.description[:500])
                if podcast.website_url:
                    outline.set('htmlUrl', podcast.website_url)

            # Convert to string with proper formatting
            xml_string = ET.tostring(opml, encoding='unicode', method='xml')

            # Add XML declaration
            opml_content = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_string}'

            logger.info(f"Generated OPML file with {len(podcasts)} podcasts")
            return opml_content

        except Exception as e:
            logger.error(f"Error generating OPML: {e}")
            raise

    @staticmethod
    def validate_opml(opml_content: bytes) -> bool:
        """
        Validate that the content is a valid OPML file.

        Args:
            opml_content: Raw file content

        Returns:
            True if valid OPML, False otherwise
        """
        try:
            tree = ET.parse(BytesIO(opml_content))
            root = tree.getroot()

            # Check if root element is 'opml'
            if root.tag.lower() != 'opml':
                logger.warning(f"Root element is '{root.tag}', expected 'opml'")
                return False

            # Check if there's at least one outline element
            outlines = list(root.iter('outline'))
            if not outlines:
                logger.warning("No outline elements found in OPML")
                return False

            return True

        except ET.ParseError as e:
            logger.error(f"OPML validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"OPML validation error: {e}")
            return False

    @staticmethod
    def count_podcasts_in_opml(opml_content: bytes) -> int:
        """
        Count the number of podcasts in an OPML file.

        Args:
            opml_content: Raw OPML file content

        Returns:
            Number of podcast feeds found
        """
        try:
            podcasts = OPMLService.parse_opml(opml_content)
            return len(podcasts)
        except Exception:
            return 0


# Example OPML for testing/documentation
EXAMPLE_OPML = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>Podcast Subscriptions</title>
    <dateCreated>Mon, 06 Dec 2025 12:00:00 GMT</dateCreated>
  </head>
  <body>
    <outline text="Technology" title="Technology">
      <outline type="rss"
               text="The Daily"
               title="The Daily"
               xmlUrl="https://feeds.simplecast.com/54nAGcIl"
               htmlUrl="https://www.nytimes.com/the-daily"/>
      <outline type="rss"
               text="Reply All"
               title="Reply All"
               xmlUrl="https://feeds.gimletmedia.com/hearreplyall"
               htmlUrl="https://gimletmedia.com/reply-all/"/>
    </outline>
  </body>
</opml>
"""
