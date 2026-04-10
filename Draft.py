from typing import List

from Booster_Packs import LorwynEclipsedPackGenerator
from Card import Deck


class Player:
    def __init__(self, name, seat_num):
        # The Cards that this Player has previously drafted.
        self.name = name
        self.seat_num = seat_num
        self.deck = Deck()

    def __str__(self):
        return self.name + " (P" + str(self.seat_num) + ")"

    # The evaluation function that determines how "valuable" a given card is to take,
    # given what the player has in their deck and what they know about their opponents.
    def evaluate_card(self, card) -> float:
        return card.win_rate

    # Evaluates all cards in the given selection, adds the (perceived) best one to the deck,
    # then removes the selected card from the selection in-place.
    def draft_best_card(self, selection) -> bool:
        # Do not draft a card if there is nothing to draft.
        if len(selection) <= 0:
            return False

        # There are cards in the selection, so we must evaluate them to determine the best one.

        highest_value = -999
        idx_to_draw = 0

        for idx in range(len(selection)):
            current_value = self.evaluate_card(selection[idx])
            if current_value is None:
                print(selection[idx])
            if current_value > highest_value:
                highest_value = current_value
                idx_to_draw = idx

        self.deck.draft_card(selection[idx_to_draw])
        del selection[idx_to_draw]
        return True

    # Assembles data about the cards currently in the player's deck.
    # def get_deck_stats(self) -> dict:
    #     deck_stats = {
    #         "deck": self.deck,
    #         "deck_size": len(self.deck),
    #         "average_costs":
    #     }


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
            players.append(Player(self.name_pool[seat_idx], seat_idx))

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

table = Table()
ready_players = table.draft()

for ready_player in ready_players:
    print("")
    print("---- " + str(ready_player) + " ----")
    ready_player.deck.print_card_list()
