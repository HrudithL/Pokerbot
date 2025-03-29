## Inspiration
We were inspired by the fascinating intersection of game theory and artificial intelligence in poker. The challenge of creating an AI that could learn and adapt its strategy in a game of incomplete information drove us to develop this poker bot using Counterfactual Regret Minimization (CFR).

## What it does
Our poker bot plays Texas Hold'em using advanced decision-making algorithms. It:

- Evaluates hand strength dynamically
- Adapts its strategy based on opponent behavior
- Uses CFR to minimize regret and optimize decisions
- Manages bankroll and betting sizes strategically
- Learns from previous hands to improve future play
## How we built it
- Implemented CFR algorithm for strategy optimization
- Used eval7 library for hand strength evaluation
- Created dynamic info-set mapping for state representation
- Developed adaptive betting strategies
- Built modular architecture for easy strategy updates
## Challenges we ran into
- Balancing exploration vs exploitation in learning
- Handling the massive game state space efficiently
- Optimizing performance within the 180-second game clock
- Creating effective strategies against various opponent types
- Managing memory usage with large strategy tables
## Accomplishments that we're proud of
- Successfully implemented a working CFR algorithm
- Created a bot that adapts to opponent patterns
- Achieved positive results against baseline opponents
- Built an efficient state representation system
- Developed a scalable architecture for future improvements
## What we learned
- Deep understanding of CFR and poker AI algorithms
- Practical experience with game theory concepts
- Importance of efficient state representation
- Challenges of real-time decision making
- Balance between theoretical and practical approaches
## What's next for Bot
- Implement deep learning for pattern recognition
- Add multi-table support
- Improve opponent modeling
- Optimize memory usage
- Develop more sophisticated betting strategies
- Create a web interface for visualization
- Add support for more poker variants
