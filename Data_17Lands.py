import requests
import json

def get_17lands_data(expansion, start_date):
    # This is the internal endpoint 17Lands uses to populate the table
    url = "https://www.17lands.com/card_ratings/data"
    params = {
        "expansion": expansion,
        "format": "PremierDraft",
        "start_date": start_date
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

# Fetch ECL data
ecl_data = get_17lands_data("ECL", "2026-01-20")

if ecl_data:
    # Example: filter for just the name and the "Games in Hand" win rate
    win_rates = []
    for card in ecl_data:
        win_rates.append({
            "name": card["name"],
            "win_rate": card["win_rate"], # This is the decimal value (e.g., 0.643)
            "game_count": card["game_count"]
        })
    
    # Save for your project
    with open('ecl_win_rates.json', 'w') as f:
        json.dump(win_rates, f, indent=4)
        
    print(f"Successfully retrieved data for {len(win_rates)} cards.")