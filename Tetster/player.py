'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

import random


class Player(Bot):
    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.
        '''
        self.played_hands = 0
        self.won_hands = 0
        self.opponent_tendencies = {
            'aggression_factor': 0.5,  # Track opponent's aggression
            'fold_frequency': 0.5,     # Track opponent's folding frequency
            'raise_frequency': 0.5     # Track opponent's raising frequency
        }
        self.position_multiplier = {0: 1.2, 3: 1.1, 4: 0.9, 5: 0.8}  # Adjust based on street

    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts.
        '''
        self.hole_cards = round_state.hands[active]
        self.played_hands += 1
        self.round_actions = []
        self.my_position = 'BB' if active else 'SB'

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Learn from the round that just ended
        '''
        my_delta = terminal_state.deltas[active]
        previous_state = terminal_state.previous_state
        opp_cards = previous_state.hands[1-active]

        # Update win/loss record
        if my_delta > 0:
            self.won_hands += 1

        # Update opponent tendencies
        if opp_cards:  # If cards were revealed
            opp_actions = [action for action in self.round_actions if action['player'] == (1-active)]
            if opp_actions:
                # Update aggression factor
                raises = sum(1 for action in opp_actions if action['type'] == 'raise')
                self.opponent_tendencies['raise_frequency'] = (
                    0.9 * self.opponent_tendencies['raise_frequency'] +
                    0.1 * (raises / len(opp_actions))
                )

    def get_action(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        '''
        legal_actions = round_state.legal_actions()
        street = round_state.street
        my_cards = round_state.hands[active]
        board_cards = round_state.deck[:street]
        my_pip = round_state.pips[active]
        opp_pip = round_state.pips[1-active]
        my_stack = round_state.stacks[active]
        continue_cost = opp_pip - my_pip
        pot = my_pip + opp_pip

        # Calculate hand strength and pot odds
        hand_strength = self.evaluate_hand(my_cards, board_cards)
        hand_strength *= self.position_multiplier.get(street, 1.0)
        pot_odds = continue_cost / (pot + continue_cost) if continue_cost > 0 else 0

        if RaiseAction in legal_actions:
            min_raise, max_raise = round_state.raise_bounds()
            
            # Premium hand strategy
            if hand_strength > 0.8:
                raise_amount = min(max_raise, int(pot * 0.75))
                return RaiseAction(raise_amount)

            # Strong hand strategy
            elif hand_strength > 0.7:
                if street < 3 or self.opponent_tendencies['fold_frequency'] > 0.4:
                    raise_amount = min(max_raise, int(pot * 0.5))
                    return RaiseAction(raise_amount)

            # Semi-bluff with drawing hands
            elif hand_strength > 0.5 and street in [3, 4]:
                if random.random() < 0.6:
                    return RaiseAction(min_raise)

        # Check when possible
        if CheckAction in legal_actions:
            if hand_strength > 0.4 or street == 0:
                return CheckAction()
            
        # Consider folding
        if continue_cost > 0:
            if hand_strength < pot_odds:
                if continue_cost > my_stack // 4:  # Don't fold if investment is small
                    return FoldAction()

        # Call as a default action
        return CallAction()

    def evaluate_hand(self, cards, board_cards=[]):
        '''
        Enhanced hand evaluation
        '''
        if not cards:
            return 0
        
        ranks = [card[0] for card in cards]
        suits = [card[1] for card in cards]
        
        # Convert face cards to numerical values
        value_dict = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10}
        values = [value_dict.get(r, int(r)) for r in ranks]
        
        # Pocket pairs
        if ranks[0] == ranks[1]:
            pair_value = values[0]
            if pair_value >= 10:  # High pairs
                return 0.9
            elif pair_value >= 7:  # Medium pairs
                return 0.7
            return 0.6
        
        # High cards
        max_value = max(values)
        min_value = min(values)
        
        # Suited cards
        if suits[0] == suits[1]:
            return 0.5 + max_value/30
        
        # Connected cards
        if abs(max_value - min_value) == 1:
            return 0.4 + max_value/30
        
        # High card strength
        if max_value >= 12:
            return 0.3 + max_value/30
            
        return 0.2


if __name__ == '__main__':
    run_bot(Player(), parse_args())
