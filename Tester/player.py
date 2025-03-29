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
        self.position_weights = {
            'SB': {'premium': 0.9, 'strong': 0.7, 'playable': 0.5},
            'BB': {'premium': 0.95, 'strong': 0.8, 'playable': 0.6}
        }
        self.hand_ranges = {
            'premium': ['AA', 'KK', 'QQ', 'AK', 'AKs'],
            'strong': ['JJ', 'TT', '99', 'AQ', 'AJs', 'KQs'],
            'playable': ['88', '77', 'ATs', 'KJs', 'QJs']
        }
        self.aggression_factor = 0.7
        self.round_history = []

    def get_hand_strength(self, my_cards, board_cards=[]):
        card1, card2 = my_cards[0], my_cards[1]
        rank1, rank2 = card1[0], card2[0]
        suited = card1[1] == card2[1]
        
        # Convert hand to standard notation
        hand = ''.join(sorted([rank1, rank2], reverse=True))
        if suited:
            hand += 's'
            
        # Evaluate hand category
        if hand in self.hand_ranges['premium']:
            return 'premium'
        if hand in self.hand_ranges['strong']:
            return 'strong'
        if hand in self.hand_ranges['playable']:
            return 'playable'
        return 'weak'

    def get_action(self, game_state, round_state, active):
        legal_actions = round_state.legal_actions()
        street = round_state.street
        my_cards = round_state.hands[active]
        my_pip = round_state.pips[active]
        opp_pip = round_state.pips[1-active]
        my_stack = round_state.stacks[active]
        continue_cost = opp_pip - my_pip
        pot = my_pip + opp_pip
        
        # Position determination
        position = 'BB' if active else 'SB'
        
        # Hand strength calculation
        hand_category = self.get_hand_strength(my_cards)
        position_weight = self.position_weights[position][hand_category] if hand_category in self.position_weights[position] else 0.2
        
        # Preflop strategy
        if street == 0:
            if RaiseAction in legal_actions:
                min_raise, max_raise = round_state.raise_bounds()
                if hand_category == 'premium':
                    raise_amount = min(max_raise, min_raise + int(pot * 1.5))
                    return RaiseAction(raise_amount)
                elif hand_category == 'strong':
                    raise_amount = min(max_raise, min_raise + int(pot * 0.75))
                    return RaiseAction(raise_amount)
                elif hand_category == 'playable' and random.random() < 0.7:
                    return RaiseAction(min_raise)
            
            if CallAction in legal_actions:
                if hand_category in ['premium', 'strong', 'playable']:
                    return CallAction()
                if random.random() < 0.2:  # Sometimes call with weak hands
                    return CallAction()
            
            if CheckAction in legal_actions:
                return CheckAction()
                
            return FoldAction()
            
        # Postflop strategy
        else:
            if RaiseAction in legal_actions:
                min_raise, max_raise = round_state.raise_bounds()
                if position_weight > 0.7:  # Premium or strong hands
                    raise_size = min(max_raise, min_raise + int(pot * 0.8))
                    return RaiseAction(raise_size)
                elif position_weight > 0.5 and random.random() < 0.6:  # Semi-bluff with playable hands
                    return RaiseAction(min_raise)
            
            if CheckAction in legal_actions:
                if position_weight > 0.3:  # Don't always check with decent hands
                    return CheckAction()
            
            if CallAction in legal_actions:
                if position_weight > 0.4 or continue_cost < pot * 0.2:  # Call with decent hands or small bets
                    return CallAction()
            
            return FoldAction()

    def handle_round_over(self, game_state, terminal_state, active):
        my_delta = terminal_state.deltas[active]
        previous_state = terminal_state.previous_state
        
        # Store round result for adaptation
        self.round_history.append({
            'delta': my_delta,
            'street': previous_state.street,
            'position': 'BB' if active else 'SB'
        })
        
        # Adjust aggression based on results
        if len(self.round_history) > 10:
            recent_results = self.round_history[-10:]
            win_rate = sum(1 for r in recent_results if r['delta'] > 0) / 10
            self.aggression_factor = max(0.5, min(0.9, win_rate + 0.3))
            
    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts.
        '''
        self.hole_cards = round_state.hands[active]
        self.my_bankroll = game_state.bankroll
        self.round_num = game_state.round_num
        self.big_blind = bool(active)
        
        # Reset round-specific variables
        self.street_actions = []
        self.round_raised = False
        self.opponent_actions = []
        
        # Store position for strategy adjustment
        self.position = 'BB' if active else 'SB'
        
        # Track stack sizes
        self.initial_stack = round_state.stacks[active]
        self.opponent_stack = round_state.stacks[1-active]
if __name__ == '__main__':
    run_bot(Player(), parse_args())
