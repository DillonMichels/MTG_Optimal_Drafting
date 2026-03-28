import requests
import json
import time

def get_final_dataset():
    # 1. FETCH THE ENTIRE SET POOL (ECL + Special Guests 129-148)
    print("Downloading all card data from Scryfall (ECL + SPG)...")
    search_query = "set:ecl or (set:spg cn>=129 cn<=148)"
    url = f"https://api.scryfall.com/cards/search?q={search_query}"
    
    scryfall_pool = []
    while url:
        resp = requests.get(url).json()
        scryfall_pool.extend(resp.get('data', []))
        url = resp.get('next_page')
        time.sleep(0.1)
    
    print(f"Scryfall Pool Loaded: {len(scryfall_pool)} cards found.")

    # 2. CREATE A ROBUST LOOKUP MAP
    # We map both the full name AND the front-side name to the card object
    master_lookup = {}
    for card in scryfall_pool:
        full_name = card['name'].lower().strip()
        front_name = full_name.split(" // ")[0].strip()
        
        master_lookup[full_name] = card
        master_lookup[front_name] = card

    # 3. LOAD YOUR 17LANDS DATA
    with open('ecl_win_rates.json', 'r') as f:
        lands_data = json.load(f)

    # 4. MATCH AND MERGE
    final_dataset = []
    missing_names = []

    for entry in lands_data:
        # Normalize the name from 17Lands
        lands_name = entry['name'].lower().strip()
        
        # Try to find it in our Scryfall pool
        if lands_name in master_lookup:
            card_data = master_lookup[lands_name].copy() # Copy to avoid side effects
            card_data['17lands_win_rate'] = entry['win_rate']
            card_data['17lands_game_count'] = entry.get('game_count', 0)
            final_dataset.append(card_data)
        else:
            missing_names.append(entry['name'])

    # 5. SAVE AND REPORT
    with open('mtg_ai_final_dataset.json', 'w') as f:
        json.dump(final_dataset, f, indent=4)

    print("\n--- Final Report ---")
    print(f"Total cards in 17Lands file: {len(lands_data)}")
    print(f"Successfully matched and saved: {len(final_dataset)}")
    
    if missing_names:
        print(f"Still missing {len(missing_names)} cards: {missing_names}")
    else:
        print("Success! 100% match achieved. Go Pack!")

get_final_dataset()