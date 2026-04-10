import json
import random
from typing import List

import requests
from fpdf import FPDF
from io import BytesIO

from Card import Card


class LorwynEclipsedPackGenerator:
    def __init__(self, dataset_path):
        # 1. Load the data
        try:
            with open(dataset_path, 'r') as f:
                self.all_cards = json.load(f)
        except FileNotFoundError:
            print(f"Error: {dataset_path} not found. Ensure your data script has run.")
            exit()
        
        # 2. Categorize the pools
        self.ecl_cards = [c for c in self.all_cards if c.get('set') == 'ecl']
        self.spg_cards = [c for c in self.all_cards if c.get('set') == 'spg']
        
        # 3. Create rarity buckets
        self.commons = [c for c in self.ecl_cards if c['rarity'] == 'common']
        self.uncommons = [c for c in self.ecl_cards if c['rarity'] == 'uncommon']
        self.rares = [c for c in self.ecl_cards if c['rarity'] == 'rare']
        self.mythics = [c for c in self.ecl_cards if c['rarity'] == 'mythic']

        # 4. Filter for STRICTLY MONOCOLORED (Slots 1-5 Signal)
        self.color_commons = {
            'W': [c for c in self.commons if c.get('colors') == ['W']],
            'U': [c for c in self.commons if c.get('colors') == ['U']],
            'B': [c for c in self.commons if c.get('colors') == ['B']],
            'R': [c for c in self.commons if c.get('colors') == ['R']],
            'G': [c for c in self.commons if c.get('colors') == ['G']]
        }

    def generate_pack(self) -> List[Card]:
        pack_data = []
        chosen_ids = set()

        def add_to_pack(pool):
            available = [c for c in pool if c['id'] not in chosen_ids]
            if not available: return None
            card = random.choice(available)
            pack_data.append(card)
            chosen_ids.add(card['id'])
            return card

        # Slots 1-5: Monocolored Signal Commons
        for color in ['W', 'U', 'B', 'R', 'G']:
            add_to_pack(self.color_commons[color])

        # Slot 6: Any ECL common (Hybrid/Colorless allowed)
        add_to_pack(self.commons)

        # Slot 7: Special Guest Slot (1/55 chance)
        if random.random() < (1/55) and self.spg_cards:
            add_to_pack(self.spg_cards)
        else:
            add_to_pack(self.commons)

        # Slots 8-10: Three ECL Uncommons
        for _ in range(3):
            add_to_pack(self.uncommons)

        # Slot 11: Main Rare/Mythic Slot (1/8 chance for Mythic)
        if random.random() < 0.125:
            add_to_pack(self.mythics)
        else:
            add_to_pack(self.rares)

        # Slots 12 & 13: Wildcards (Play Booster weights)
        wildcard_weights = [0.20, 0.60, 0.18, 0.02] 
        foil_weights = [0.60, 0.30, 0.09, 0.01]

        for weights in [wildcard_weights, foil_weights]:
            rarity = random.choices(['common', 'uncommon', 'rare', 'mythic'], weights=weights)[0]
            pool = {'common': self.commons, 'uncommon': self.uncommons, 
                    'rare': self.rares, 'mythic': self.mythics}[rarity]
            add_to_pack(pool)

        cards = []
        for card_data in pack_data:
            cards.append(Card(card_data))

        return cards

class PDFPackVisualizer:
    @staticmethod
    def generate_pdf(pack, filename="lorwyn_pack_visual.pdf"):
        print(f"Generating PDF: {filename}...")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Lorwyn Eclipsed - Draft Pack Simulation", center=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        # NEW GRID SETTINGS (4 columns to fit all 13 on one page)
        cols = 4
        card_w = 42   # mm (Slightly smaller for better fit)
        card_h = 59   # mm (Maintains MTG aspect ratio)
        margin_x = 6  # mm
        margin_y = 8  # mm
        start_x = 12
        start_y = 25

        for i, card in enumerate(pack):
            row = i // cols
            col = i % cols
            x = start_x + (col * (card_w + margin_x))
            y = start_y + (row * (card_h + margin_y))

            # SPEED FIX: Use 'small' instead of 'normal'
            img_url = ""
            if 'image_uris' in card:
                img_url = card['image_uris']['small'] # Much faster download
            elif 'card_faces' in card:
                # Still handles your Ashling/Oko DFCs
                img_url = card['card_faces'][0]['image_uris']['small']

            if img_url:
                try:
                    # Sequential downloads are the bottleneck; 'small' helps a ton
                    response = requests.get(img_url, timeout=5)
                    img_data = BytesIO(response.content)
                    pdf.image(img_data, x=x, y=y, w=card_w)
                    
                    # Add a small label under the card
                    pdf.set_xy(x, y + card_h + 1)
                    pdf.set_font("Helvetica", "", 7)
                    # Shorten name if it's too long for the column
                    display_name = (card['name'][:22] + '..') if len(card['name']) > 24 else card['name']
                    pdf.cell(card_w, 4, display_name, align='C')
                except Exception as e:
                    print(f"Error fetching {card['name']}: {e}")

        pdf.output(filename)
        print(f"Successfully saved all 13 cards to {filename}")

# --- SINGLE EXECUTION POINT ---
if __name__ == "__main__":
    DATA_PATH = 'mtg_ai_final_dataset.json'
    
    # 1. Initialize Generator
    gen = LorwynEclipsedPackGenerator(DATA_PATH)
    
    # 2. Generate a pack
    simulated_pack = gen.generate_pack()
    
    # 3. Print to terminal (for quick verification)
    print("\n[Pack Contents]")
    for i, c in enumerate(simulated_pack):
        print(f"Slot {i+1:2}: {c['name']} ({c['rarity']})")
    
    # 4. Generate the PDF
    PDFPackVisualizer.generate_pdf(simulated_pack, "CSC520_Simulated_Pack.pdf")
