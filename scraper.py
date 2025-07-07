import requests
import json
import os
import pandas as pd
import requests
import time

# load env
from dotenv import load_dotenv
load_dotenv()

def scrape_all_water_data():
    """
    Scrapes all pages of bottled water data from the Oasis Health API and saves it to a JSON file.
    """
    base_url = "https://app.oasis-health.com/api/items/bottled_water/"
    all_water_items = []
    page = 1
    
    while base_url:
        print(f"Scraping page {page} from {base_url}...")
        try:
            response = requests.get(base_url)
            response.raise_for_status()
            data = response.json()
            
            items = data.get('results', [])
            all_water_items.extend(items)
            
            # Get the next page URL, if it exists
            base_url = data.get('next')
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            break
            
    with open('water_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_water_items, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully scraped and saved {len(all_water_items)} items to water_data.json")

if __name__ == "__main__":
    scrape_all_water_data() 