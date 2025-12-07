#!/usr/bin/env python3
"""
Simple script to get your Plex authentication token.

This will prompt for your Plex username and password, then retrieve your token.
Your credentials are NOT stored - they're only used to authenticate once.
"""

import getpass
import requests
from xml.etree import ElementTree

def get_plex_token():
    """Get Plex token by authenticating with username/password."""

    print("=" * 60)
    print("Plex Token Retriever")
    print("=" * 60)
    print()
    print("This will authenticate with Plex.tv to get your token.")
    print("Your credentials are NOT stored - only used for this request.")
    print()

    # Get credentials
    username = input("Plex Username (email): ").strip()
    password = getpass.getpass("Plex Password: ")

    print()
    print("Authenticating with Plex.tv...")

    try:
        # Authenticate with Plex
        response = requests.post(
            'https://plex.tv/users/sign_in.xml',
            auth=(username, password),
            headers={
                'X-Plex-Client-Identifier': 'PodcastManager',
                'X-Plex-Product': 'Podcast Manager',
                'X-Plex-Version': '1.0'
            }
        )

        if response.status_code == 401:
            print("❌ Authentication failed - incorrect username or password")
            return None

        if response.status_code != 201:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None

        # Parse XML response
        root = ElementTree.fromstring(response.content)
        token = root.get('authToken')

        if token:
            print()
            print("✅ Success! Your Plex token is:")
            print()
            print("=" * 60)
            print(token)
            print("=" * 60)
            print()
            print("Add this to your .env file:")
            print(f"PLEX_TOKEN={token}")
            print()
            return token
        else:
            print("❌ Could not find token in response")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    get_plex_token()
