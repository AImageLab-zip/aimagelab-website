#!/usr/bin/env python3
"""
Test script to verify IRIS API connectivity and response format.
Run this to ensure the IRIS API is accessible before running imports.
"""

import requests
import xml.etree.ElementTree as ET
import sys


def test_iris_api():
    """Test IRIS API with a sample author"""
    
    # Test with Costantino Grana's IRIS ID
    test_iris_id = 65510
    api_url = f"https://wss.unimore.it/public/WebApiPubblicazioni/api/pubblicazioni/GetPubblDtgByIdAutore?par1={test_iris_id}"
    
    print("=" * 60)
    print("IRIS API Connectivity Test")
    print("=" * 60)
    print(f"\nTesting with IRIS ID: {test_iris_id}")
    print(f"API URL: {api_url}\n")
    
    try:
        print("Sending request...")
        response = requests.get(api_url, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ ERROR: Unexpected status code {response.status_code}")
            return False
        
        print("✓ Request successful\n")
        
        # Parse XML
        print("Parsing XML response...")
        root = ET.fromstring(response.content)
        
        # Count publications
        publications = root.findall('PubblDtgAutore')
        pub_count = len(publications)
        
        print(f"✓ XML parsed successfully")
        print(f"✓ Found {pub_count} publications\n")
        
        if pub_count > 0:
            # Show sample publication
            sample_pub = publications[0]
            
            print("Sample Publication:")
            print("-" * 60)
            
            fields = ['Id', 'Titolo', 'Anno', 'Autori', 'Tipo', 'Rivista']
            for field in fields:
                element = sample_pub.find(field)
                value = element.text if element is not None and element.text else '(empty)'
                if field == 'Titolo':
                    value = value[:100] + '...' if len(value) > 100 else value
                if field == 'Autori':
                    value = value[:80] + '...' if len(value) > 80 else value
                print(f"  {field}: {value}")
            
            print("-" * 60)
        
        # Test attachment API with first publication
        if pub_count > 0:
            pub_id = publications[0].find('Id')
            if pub_id is not None and pub_id.text:
                print(f"\nTesting attachment API with publication ID: {pub_id.text}")
                
                attachment_url = f"https://wss.unimore.it/public/WebApiPubblicazioni/api/pubblicazioni/GetPubblAllById?par1={pub_id.text}"
                att_response = requests.get(attachment_url, timeout=30)
                
                if att_response.status_code == 200:
                    print("✓ Attachment API accessible")
                    
                    att_root = ET.fromstring(att_response.content)
                    attachments = att_root.findall('PubblAllegati')
                    
                    if attachments:
                        print(f"✓ Found {len(attachments)} attachment(s)")
                        for att in attachments:
                            url_elem = att.find('URL')
                            if url_elem is not None and url_elem.text:
                                print(f"  PDF URL: {url_elem.text[:100]}...")
                    else:
                        print("  (No attachments for this publication)")
                else:
                    print(f"❌ Attachment API returned status {att_response.status_code}")
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        print("\nThe IRIS API is accessible and returning expected data.")
        print("You can proceed with the import process.\n")
        
        return True
        
    except requests.RequestException as e:
        print(f"\n❌ Network Error: {e}")
        print("\nPossible issues:")
        print("  - No internet connection")
        print("  - IRIS API is down or unreachable")
        print("  - Firewall blocking the connection")
        return False
        
    except ET.ParseError as e:
        print(f"\n❌ XML Parse Error: {e}")
        print("\nThe API returned invalid XML.")
        print("Response preview:")
        print(response.text[:500])
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        return False


if __name__ == '__main__':
    success = test_iris_api()
    sys.exit(0 if success else 1)
