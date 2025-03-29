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
            strategy = [1.0 / self.num_actions] * self.num_actions
            
        return strategy

    def update_strategy(self, info_set, strategy, realization_weight):
        """Update strategy sums for this information set"""
        for a in range(self.num_actions):
            self.strategy_sum[info_set][a] += realization_weight * strategy[a]

    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        #my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        #game_clock = game_state.game_clock  # the total number of seconds your bot has left to play this game
        #round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        #my_cards = round_state.hands[active]  # your cards
        #big_blind = bool(active)  # True if you are the big blind
        pass

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        #my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        previous_state = terminal_state.previous_state  # RoundState before payoffs
        #street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        #my_cards = previous_state.hands[active]  # your cards
        #opp_cards = previous_state.hands[1-active]  # opponent's cards or [] if not revealed
        pass

    def evaluate_hand(self, my_cards, board_cards):
        """Evaluate hand strength using eval7"""
        cards = [eval7.Card(card) for card in my_cards + board_cards]
        hand_value = eval7.evaluate(cards)
        return hand_value

    def get_action(self, game_state, round_state, active):
        legal_actions = round_state.legal_actions()
        street = round_state.street
        my_cards = round_state.hands[active]
        board_cards = round_state.deck[:street]
        
        # Get current game state information
        info_set = self.get_info_set(round_state, active)
        strategy = self.get_strategy(info_set)
        
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
        
        # Convert selected action to actual poker action
        if action_type == 'raise' and RaiseAction in legal_actions:
            raise_amount = min_raise
            if hand_strength > 0.8:  # Strong hand
                raise_amount = max(min_raise, min(max_raise, int(min_raise * 2.5)))
            return RaiseAction(raise_amount)
        elif action_type == 'call':
            if CheckAction in legal_actions:
                return CheckAction()
            return CallAction()
        else:
            if CheckAction in legal_actions:
                return CheckAction()
            return FoldAction()

    def handle_new_round(self, game_state, round_state, active):
        """
        Update strategy at the start of each round
        """
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
        my_delta = terminal_state.deltas[active]
        previous_state = terminal_state.previous_state
        
        # Update regrets based on outcome
        if my_delta > 0:
            info_set = self.get_info_set(previous_state, active)
            action_taken = self.get_last_action_type(previous_state)
            self.regret_sum[info_set][action_taken] += my_delta

if __name__ == '__main__':
    run_bot(Player(), parse_args())
