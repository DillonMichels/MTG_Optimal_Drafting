from enum import IntEnum
import json

heavy_dataset = "mtg_ai_final_dataset.json"


class Color(IntEnum):
    COLORLESS = 0,
    RED = 1,
    BLUE = 2,
    GREEN = 3,
    BLACK = 4,
    WHITE = 5


class Rarity(IntEnum):
    # "None" isn't a Rarity, but its existence helps with error logging.
    NONE = -1,
    COMMON = 0,
    UNCOMMON = 1,
    RARE = 2,
    MYTHIC = 3


text_to_color = {
    'R': Color.RED, 'U': Color.BLUE, 'G': Color.GREEN, 'B': Color.BLACK, 'W': Color.WHITE
}
color_to_emoji = {
    Color.COLORLESS: "❔", Color.RED: "🔥", Color.GREEN: "🥬", Color.BLUE: "💧", Color.WHITE: "💮", Color.BLACK: "🩻"
}
text_to_rarity = {
    "common": Rarity.COMMON, "uncommon": Rarity.UNCOMMON, "rare": Rarity.RARE, "mythic": Rarity.MYTHIC
}


# A single Magic: The Gathering card's data, simplified down from 17Lands' JSON information.
class Card:

    # For now, Card ignores double-sided-ness...

    def __init__(self, card_data):
        self.id = card_data.get("id")
        self.name = card_data.get("name")
        self.set = card_data.get("set")
        self.combined_cost = card_data.get("cmc")
        self.rarity = text_to_rarity.get(card_data.get("rarity"), Rarity.NONE)

        self.color_identity = []
        input_color_id = card_data.get("color_identity")
        for color_code in input_color_id:
            self.color_identity.append(text_to_color[color_code])
        if not self.color_identity:
            self.color_identity = [Color.COLORLESS]
        else:
            self.color_identity.sort()

        self.keywords = card_data.get("keywords")
        self.win_rate = card_data.get("17lands_win_rate")
        # Some cards have a win rate of "null" in the data set, which is why we need to explicitly overwrite Nones.
        if self.win_rate is None:
            self.win_rate = 0.50
        self.game_count = card_data.get("17lands_game_count", 0)

    def __str__(self):
        result = "\t" + str(int(self.combined_cost)) + " Mana\t"

        result += color_to_emoji[Color.RED] if Color.RED in self.color_identity else "▪️"
        result += color_to_emoji[Color.GREEN] if Color.GREEN in self.color_identity else "▪️"
        result += color_to_emoji[Color.BLUE] if Color.BLUE in self.color_identity else "▪️"
        result += color_to_emoji[Color.BLACK] if Color.BLACK in self.color_identity else "▪️"
        result += color_to_emoji[Color.WHITE] if Color.WHITE in self.color_identity else "▪️"

        result += " [" + self.name + "]"
        return result


# A collection of cards that can be evaluated on its consistency and viability in an MTG game.
class Deck:

    def __init__(self):
        self.cards = []
        # Represents frequency of mana cost, from 0 through 9+.
        self.cost_frequency = [0] * 10
        # Represents frequency of color identity, in [Colorless R U G W B] order.
        self.color_frequency = [0] * 6
        # Represents the average win rate of all cards.
        self.average_win_rate = 0.00

    def print_card_list(self):
        print("Deck List:")

        card_list = list(self.cards)
        current_cost = 0
        while len(card_list) > 0:
            for card_idx in range(len(card_list) - 1, -1, -1):
                card = card_list[card_idx]
                if card.combined_cost == current_cost:
                    print(str(card))
                    del card_list[card_idx]
            current_cost += 1

        # for card in self.cards:
        #     print(str(disp_num) + ". " + str(card))

    # Add a new card to this deck, storing it and updating metrics.
    def draft_card(self, card):
        # Add the card to the card list.
        self.cards.append(card)

        # Record the cost and color(s) of the new card.
        self.cost_frequency[int(card.combined_cost)] += 1
        for color in card.color_identity:
            self.color_frequency[int(color.value)] += 1

        # Recalculate the average win rate of the deck after the addition.
        win_rate_sum = self.average_win_rate * (len(self.cards) - 1)
        win_rate_sum += card.win_rate
        self.average_win_rate = win_rate_sum / len(self.cards)

    def calculate_playability(self):
        """The Evaluator: Turns the deck state into a single multi-objective score."""
        if not self.cards:
            return 0.5

        # 1. Quality (Average of top 23 cards to ignore 'sideboard chaff')
        top_rates = sorted([c.win_rate for c in self.cards], reverse=True)[:23]
        quality = sum(top_rates) / len(top_rates)

        # 2. Coherency (Percentage of cards in the two main colors)
        color_counts = sorted(self.color_frequency.values(), reverse=True)
        coherency = (color_counts[0] + color_counts[1]) / len(self.cards)

        # 3. Curve Fitness (Penalty based on Mean Squared Error)
        # Ideal counts for CMCs 1, 2, 3, 4, 5+ in a standard 23-card deck
        ideal = [2, 4, 6, 4, 2] 
        actual = [self.cost_frequency[i] for i in range(1, 6)]
        
        # Calculate MSE: sum of (actual - ideal)^2
        curve_penalty = sum((a - i)**2 for a, i in zip(actual, ideal))

        # Weights: Quality is King, but Coherency and Curve are the tie-breakers
        # w3 is very small because MSE grows quickly
        w1, w2, w3 = 1.0, 0.2, 0.005
        
        return (w1 * quality) + (w2 * coherency) - (w3 * curve_penalty)
