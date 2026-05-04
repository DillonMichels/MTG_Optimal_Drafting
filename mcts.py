import copy
import math
import random

class DraftState:
    def __init__(self, deck, current_pack, packs_remaining, player_index):
        # We use deepcopy so the AI's "imagination" doesn't change your real deck
        self.deck = copy.deepcopy(deck) 
        self.current_pack = list(current_pack)
        self.packs_remaining = packs_remaining
        self.player_index = player_index

    def get_possible_actions(self):
        return self.current_pack

    def get_next_state(self, action):
        """
        This replaces 'move'. MCTS needs to create a NEW state 
        to explore a branch without destroying the current one.
        """
        # 1. Create the new state
        next_state = DraftState(
            self.deck, 
            self.current_pack, 
            self.packs_remaining, 
            self.player_index
        )
        
        # 2. Perform the action (Draft the card)
        next_state.deck.draft_card(action)
        
        # 3. FIX FOR LINE 16: Remove the card so it's not there for the next pick
        if action in next_state.current_pack:
            next_state.current_pack.remove(action)
            
        return next_state
class MCTSNode:
    def __init__(self, state, parent=None, action=None):
        self.state = state  # The DraftState
        self.parent = parent
        self.action = action  # The card picked to get here
        self.children = []
        self.visits = 0
        self.total_reward = 0.0
        # Tracks which cards in the current pack haven't been "simulated" yet
        self.untried_actions = list(state.get_possible_actions())

    def is_fully_expanded(self):
        return len(self.untried_actions) == 0

    def best_child(self, c_param=1.41):
        """The UCT formula: balances exploitation (win rate) and exploration."""
        choices_weights = [
            (c.total_reward / c.visits) + c_param * math.sqrt((2 * math.log(self.visits) / c.visits))
            for c in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]

    def expand(self):
        # Instead of pop(), sort the untried actions by win_rate
        # so the AI explores 'good' cards first.
        self.untried_actions.sort(key=lambda x: x.win_rate)
        action = self.untried_actions.pop() 
    
        next_state = self.state.get_next_state(action)
        child_node = MCTSNode(next_state, parent=self, action=action)
        self.children.append(child_node)
        return child_node

    def simulate_rollout(self):
        """
        The 'Rollout' phase. Finishes the draft greedily 
        to see how 'good' the final deck looks.
        """
        current_rollout_state = self.state
        # For the baseline, we simulate picking the highest win-rate 
        # cards for the remainder of the 45 picks.
        # Penalty for a bad mana curve
        # If we have too many expensive cards (5+ CMC), reduce the score
        expensive_cards = sum(state.deck.cost_frequency[5:])
        if expensive_cards > 5:
            score -= 0.02 # A small 'clunkiness' tax
        
        return current_rollout_state.deck.average_win_rate
