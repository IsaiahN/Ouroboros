The problem with locksmith and some of the other ARC 3 AGI games is crystal clear now. You've abstracted concepts from the real world (game lives, little squares to denote actions remaining) and we humans understand this from gameplay and society (going to school), but an agent that was "born" into this game world only, and has no outside understanding is left to the level of the understanding of the programmer (plato's allegory of the cave). A first grader couldnt beat this game because they arent trained (but are conscious and sentient still), while an adult human can.

My model has been stuck on locksmith for ages, because i suck at IQ games, but also because my understanding of the action system was fundamentally flawed -> agents have incomplete knowledge on all the ways that actions can be used. 

Now that i have that understanding, I can give them the ruleset on (not how to beat this game - would be useless longterm) but how to move about the board and observe the board (the world model / self model) and then they can use that to form the theories on the winning conditions for each level.

The way i was building my model was that everything they learned about actions came from the ARC 3 API DOCs (the sun casing shadows was objective truth in platos cave) but your documentation is not sufficient. Which means agents cannot be trained from scratch (without outside knowledge) and make it to the later levels.

The only agents capable of beating these game levels are 

1) the agents that brute forced their understanding, and then reverse engineered the sequence, and even those might not understand the rules of the game they are playing. (They are good at correlation not casuality)

2) the LLM powered agents (using chatgpt, gemini, etc) because LLM have alot of out of game context about human culture like the concept of game lives, understanding of game mechanics, and are multimodal so they can visualize the grid and would generally do alot better at game play than any thing someone could train from scratch.
