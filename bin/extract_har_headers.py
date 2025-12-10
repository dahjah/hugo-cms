import json

def extract_headers(filepath, url_partial):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
            
        entries = har_data['log']['entries']
        
        for entry in entries:
            request = entry['request']
            if url_partial in request['url'] and entry['response']['status'] == 200:
                print(f"Found successful request to: {request['url']}")
                print("Headers:")
                for h in request['headers']:
                    # keys usually lowercase in http/2 or standardized in HAR sometimes
                    print(f"'{h['name']}': '{h['value']}',")
                return

        print("No matching successful request found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_headers('dawgz-menu.har', '/menu/')
