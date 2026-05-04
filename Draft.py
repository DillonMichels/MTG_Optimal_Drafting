from typing import List
import copy
import statistics
from mcts import MCTSNode, DraftState
from Booster_Packs import LorwynEclipsedPackGenerator
from Card import Deck, Color


class Player:
    def __init__(self, name, seat_num, is_ai=False, color_bias=None):
        # The Cards that this Player has previously drafted.
        self.name = name
        self.seat_num = seat_num
        self.is_ai = is_ai  # Flag to determine if this player uses MCTS
        self.deck = Deck()
        # New: color_bias should be a Color enum or None
        self.color_bias = color_bias

    def __str__(self):
        return f"{self.name} (P{self.seat_num})"

    def evaluate_card(self, card) -> float:
        """
        The baseline evaluation function. 
        Used by greedy bots and as a starting point for MCTS.
        """
        # Baseline: Just use the 17Lands win rate
        score = card.win_rate
        
        # If this bot "really likes" a color, add a massive flat bonus
        # 0.15 is huge (it turns a 50% win rate card into a 65% one)
        if self.color_bias is not None:
            if self.color_bias in card.color_identity:
                score += 0.15
                
        return score

    def draft_best_card(self, selection) -> bool:
        """
        Evaluates all cards in the pack, selects the best one, 
        and updates the deck and the pack.
        """
        if not selection or len(selection) <= 0:
            return False

        if self.is_ai:
            # AI uses Monte Carlo Tree Search to 'look ahead'
            # Note: 100 iterations is a good balance of speed/quality for 1,000 drafts.
            chosen_card = self.mcts_search(selection, iterations=100)
        else:
            # Baseline bots just take the card with the highest win_rate
            chosen_card = max(selection, key=self.evaluate_card)

        # Update the actual state of the draft
        self.deck.draft_card(chosen_card)
        selection.remove(chosen_card)
        return True

    def mcts_search(self, selection, iterations):
        """
        Runs the MCTS algorithm to simulate draft futures.
        """
        # Initialize the state with current deck and pack
        # packs_remaining is hardcoded to 3 for the baseline
        initial_state = DraftState(
            deck=self.deck, 
            current_pack=selection, 
            packs_remaining=3, 
            player_index=self.seat_num
        )
        root = MCTSNode(state=initial_state)

        for _ in range(iterations):
            node = root
            
            # 1. SELECTION: Follow the UCT path down to a leaf
            while node.is_fully_expanded() and node.children:
                node = node.best_child()

            # 2. EXPANSION: Create a new node for an untried card
            if not node.is_fully_expanded():
                node = node.expand()
            
            # 3. SIMULATION (Rollout): Get a score for this path
            reward = self.simulate_rollout(node.state)

            # 4. BACKPROPAGATION: Update the tree with the result
            while node is not None:
                node.visits += 1
                node.total_reward += reward
                node = node.parent

        # Return the action (card) from the child that was explored the most
        return max(root.children, key=lambda c: c.visits).action
    
    def simulate_rollout(self, state):
        """
        Heuristic evaluation of a simulated state.
        Now includes a synergy bonus to favor consistent color pairs.
        """
        temp_deck = copy.deepcopy(state.deck)
        cards_needed = 45 - len(temp_deck.cards)
    
        # "Fast-forward" the rest of the draft greedily
        # We use a simplified 'ghost pack' simulation
        for _ in range(cards_needed):
            # In a real rollout, you'd pull from your dataset here.
            # For a fast baseline, we assume the AI gets an 'average' card 
            # from the set that matches its current top colors.
            temp_deck.average_win_rate *= 0.99 # Slight decay for 'unknown' future cards
        
        # Calculate synergy at the END of the simulated draft
        color_counts = sorted(temp_deck.color_frequency, reverse=True)
        consistency = (color_counts[0] + color_counts[1]) / len(temp_deck.cards)
    
        return temp_deck.average_win_rate + (consistency * 0.05)

    # Optional: Method for your final reporting/analysis
    def get_deck_stats(self) -> dict:
        return {
            "name": self.name,
            "is_ai": self.is_ai,
            "avg_win_rate": self.deck.average_win_rate,
            "cards_count": len(self.deck.cards)
        }
class Table:
    pack_gen = LorwynEclipsedPackGenerator("mtg_ai_final_dataset.json")
    name_pool = ["Amy", "Bob", "Cam", "Dee", "Ema", "Fia", "Gab", "Han"]
    player_count = 8
    packs_per_player = 3

    def __init__(self):
        pass

    def draft(self) -> List[Player]:

        players = []
        # Instantiate new players who will draft cards.
        for seat_idx in range(self.player_count):
            name = self.name_pool[seat_idx]

            is_ai = False  
            bias = None
            if seat_idx == 0:
                is_ai = True  # # Amy is the AI
            elif name == "Bob":
                bias = Color.WHITE # Bob forces White
            elif name == "Cam":
                bias = Color.BLUE  # Cam forces Blue
            players.append(Player(name, seat_idx, is_ai=is_ai, color_bias=bias))

        # For a full draft, have all players at the table draft one booster pack's worth of cards, three times.
        # In each subsequent rotation, players pass packs in the opposite direction.
        self.pack_rotation(players, -1)
        self.pack_rotation(players, 1)
        self.pack_rotation(players, -1)

        return players

    # Simulates one full booster pack's worth of card draws for every player in 'players',
    # passing packs 'pass_offset' indices down the line between draws.
    def pack_rotation(self, players, pass_offset):

        booster_packs = []
        # Generate new packs, one for each player's seat at the table.
        for pack in range(self.player_count):
            booster_packs.append(self.pack_gen.generate_pack())

        # Once, for every card in a pack (such that all packs are emptied)...
        for cards_left in range(len(booster_packs[0]), 0, -1):

            # Ask all players to draft one card from the pack in front of them.
            for player_idx in range(len(players)):
                players[player_idx].draft_best_card(booster_packs[player_idx])

            # Once players are done selecting, pass each player's pack a specified number of seats around the table.
            booster_packs = booster_packs[pass_offset:] + booster_packs[:pass_offset]

# --- SIMULATION EXECUTION ---
NUM_DRAFTS = 1000
ai_win_rates = []
baseline_win_rates = []

print(f"Starting {NUM_DRAFTS} simulation drafts. This may take a while...")

for i in range(NUM_DRAFTS):
    table = Table()
    ready_players = table.draft()
    
    # Store the AI's result (Seat 0)
    ai_win_rates.append(ready_players[0].deck.average_win_rate)
    
    # Store the average of all 7 baseline bots for comparison
    baselines = [p.deck.average_win_rate for p in ready_players[1:]]
    baseline_win_rates.append(statistics.mean(baselines))
    
    if (i + 1) % 10 == 0:
        print(f"Completed Draft {i + 1}/{NUM_DRAFTS}...")

# --- FINAL REPORTING ---
print("\n" + "="*30)
print("DRAFT SIMULATION RESULTS")
print("="*30)
print(f"AI (MCTS) Mean Win Rate:       {statistics.mean(ai_win_rates):.4f}")
print(f"Baseline (Greedy) Mean Win Rate: {statistics.mean(baseline_win_rates):.4f}")
print(f"Performance Lift:             {((statistics.mean(ai_win_rates) - statistics.mean(baseline_win_rates)) * 100):.2f}%")
print("="*30)
