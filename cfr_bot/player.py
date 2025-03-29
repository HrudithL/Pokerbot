'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot
import eval7
import random
import numpy as np
from collections import defaultdict

class Player(Bot):
    def __init__(self):
        self.regret_sum = defaultdict(lambda: defaultdict(float))
        self.strategy_sum = defaultdict(lambda: defaultdict(float))
        self.num_actions = 3  # fold, call, raise
        self.iterations = 0
        self.last_action = None  # Add this line
        self.last_info_set = None  # Add this line

    def get_info_set(self, round_state, active):
        """Create a string key for the current game state"""
        street = round_state.street
        my_cards = round_state.hands[active]
        board_cards = round_state.deck[:street]
        my_pip = round_state.pips[active]
        opp_pip = round_state.pips[1-active]
        
        # Sort cards for consistent key
        my_cards_str = ''.join(sorted([str(card) for card in my_cards]))
        board_str = ''.join(sorted([str(card) for card in board_cards]))
        
        return f"S{street}|C{my_cards_str}|B{board_str}|P{my_pip}|O{opp_pip}"

    def get_strategy(self, info_set):
        """Get current strategy for this information set"""
        regrets = [max(0, self.regret_sum[info_set][a]) for a in range(self.num_actions)]
        regret_sum = sum(regrets)
        
        if regret_sum > 0:
            strategy = [regret / regret_sum for regret in regrets]
        else:
            strategy = [1.0 / self.num_actions for a in range(self.num_actions)] * self.num_actions
            
        return strategy

    def update_strategy(self, info_set, strategy, realization_weight):
        """Update strategy sums for this information set"""
        for a in range(self.num_actions):
            self.strategy_sum[info_set][a] += realization_weight * strategy[a]

    def evaluate_hand(self, my_cards, board_cards):
        """Evaluate hand strength using eval7"""
        cards = [eval7.Card(card) for card in my_cards + board_cards]
        hand_value = eval7.evaluate(cards)
        return hand_value

    def get_action(self, game_state, round_state, active):
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot
        
        # Get current game state information
        info_set = self.get_info_set(round_state, active)
        strategy = self.get_strategy(info_set)
        
        # Calculate pot odds and adjust strategy
        pot = my_contribution + opp_contribution
        pot_odds = continue_cost / (pot + continue_cost) if continue_cost > 0 else 0
        
        # Evaluate hand and adjust strategy based on strength
        hand_strength = self.evaluate_hand(my_cards, board_cards)
        if hand_strength > pot_odds:
            # If hand is stronger than pot odds, increase call/raise probability
            strategy[0] *= 0.7  # Reduce fold probability
            strategy[1] *= 1.3  # Increase call probability
            strategy[2] *= 1.2  # Slightly increase raise probability
            # Renormalize
            total = sum(strategy)
            strategy = [s/total for s in strategy]
        
        # Add realization weight calculation
        realization_weight = 1.0 / (self.iterations + 1)
        self.update_strategy(info_set, strategy, realization_weight)
        
        # Convert strategy probabilities to actions
        if RaiseAction in legal_actions:
            min_raise, max_raise = round_state.raise_bounds()
            action_probs = {
                0: ('fold', strategy[0]),
                1: ('call', strategy[1]),
                2: ('raise', strategy[2])
            }
        else:
            action_probs = {
                0: ('fold', strategy[0]),
                1: ('call', strategy[1])
            }
        
        # Select action based on strategy
        hand_strength = self.evaluate_hand(my_cards, board_cards)
        action_type = max(action_probs.items(), key=lambda x: x[1][1])[1][0]
        
        # Update regrets and strategy
        self.iterations += 1
        
        # Store the action and info_set before returning
        self.last_action = action_type
        self.last_info_set = info_set
        
        # Convert selected action to actual poker action
        if action_type == 'raise':
            raise_amount = min_raise
            if hand_strength >.8:  # Strong hand
                raise_amount = max(min_raise, min(max_raise, int(min_raise * 2.5)))
            return RaiseAction(raise_amount)
        elif action_type == 'call':
            if CheckAction in legal_actions:
                return CheckAction()
            if self.iterations > 0 and hand_strength > .8:  # Strong hand
                if RaiseAction in legal_actions:
                    return RaiseAction(max_raise)
            return CallAction()
        else:
            if CheckAction in legal_actions:
                return CheckAction()
            return FoldAction()

    def handle_new_round(self, game_state, round_state, active):
        """
        Initialize tracking for new round and update strategy
        """
        self.last_action = None
        self.last_info_set = None
        
        # Track position and round information
        is_big_blind = bool(active)
        my_cards = round_state.hands[active]
        
        # Initialize base strategy weights based on position
        if is_big_blind:
            base_regrets = {
                0: 0.2,  # Lower fold regret in BB
                1: 0.5,  # Medium call regret
                2: 0.3   # Medium raise regret
            }
        else:  # Small blind
            base_regrets = {
                0: 0.3,  # Medium fold regret
                1: 0.4,  # Medium call regret
                2: 0.3   # Medium raise regret
            }
            
        # Set initial regrets for this hand
        info_set = self.get_info_set(round_state, active)
        if not self.regret_sum[info_set]:
            for action, regret in base_regrets.items():
                self.regret_sum[info_set][action] = regret
        
        # Update average strategy if we have played some rounds
        if self.iterations > 0:
            for info_set in self.strategy_sum:
                total = sum(self.strategy_sum[info_set].values())
                if total > 0:
                    for action in self.strategy_sum[info_set]:
                        self.strategy_sum[info_set][action] /= total

    def handle_round_over(self, game_state, terminal_state, active):
        """
        Update regrets based on the round outcome
        """
        if self.last_action is None or self.last_info_set is None:
            return
            
        my_delta = terminal_state.deltas[active]
        previous_state = terminal_state.previous_state
        
        # Get the last strategy used
        last_strategy = self.get_strategy(self.last_info_set)
        
        # Update strategy with outcome weight
        outcome_weight = abs(my_delta) / STARTING_STACK
        self.update_strategy(self.last_info_set, last_strategy, outcome_weight)
        
        # Convert action type to index
        action_to_index = {'fold': 0, 'call': 1, 'raise': 2}
        action_index = action_to_index[self.last_action]
        
        # Update regrets based on outcome with adjusted weights
        if my_delta > 0:
            # Positive outcome - increase regret for chosen action
            self.regret_sum[self.last_info_set][action_index] += my_delta * 1.5
        else:
            # Negative outcome - be more forgiving of calls
            multiplier = 0.3 if action_index == 0 else 0.7  # Less penalty for non-folds
            self.regret_sum[self.last_info_set][action_index] += my_delta * multiplier
if __name__ == '__main__':
    run_bot(Player(), parse_args())
