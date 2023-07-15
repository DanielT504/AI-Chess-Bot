# AI Chess Bot
**You can see the 2nd version of my code here: https://github.com/DanielT504/AI-Chess-Bot-2.0

This AI uses a minimax tree with a specified depth, at which point an evaluation function determines a heuristic based on piece weights, material balance, pawn structure, piece mobility, captures, king safety, and threatened pieces.

The AI does not implement advanced chess concepts such as opening books, endgame tables, or position-specific knowledge, and thus plays very passively and has difficulty initiating confrontation. When prompted to react, it can play at novice level depending on the depth specified.

Several improvements have also been implemented, including Alpha-Beta pruning, transposition table enhancements, iterative deepening, quiescence searching, aspiration window searching, move ordering. Late move ordering is also partially functional, and I have plans to parallelize find_best_move to shorten calculations and allow for deeper trees. For clarification see below. 

![chess-bot](https://github.com/DanielT504/AI-Chess-Bot/assets/62156098/739c55d3-dd72-46ca-be57-dd1eba5d5dc9)

---------------------------------------

 - Alpha-Beta pruning reduces the number of evaluated nodes by eliminating branches that are guaranteed to lead to worse scores.

 - The transposition table stores evaluated board positions and their scores. This helps to avoid redundant computations.

 - Iterative deepening progressively explores deeper levels of the search tree, providing results for shallower depths and allowing timely responses.

 - The quiescence search focuses on capturing moves and forcing moves to prevent the AI from making shallow evaluations and missing important tactics or threats.

 - The aspiration window search dynamically adjusts the search window based on previous search results, narrowing down the search while still finding the best move.

 - Move ordering is based on capturing moves, promotion moves, check moves, and non-capture/non-promotion moves, in that priority order.

 - Late move reduction reduces the depth of search for non-capturing moves to save computation time, performing a full search only if necessary.

---------------------------------------

#Instructions
To play as white, black, or a random color, comment out the other two calls at the bottom of the file. In the same spot, you can also change the depth of the minimax tree in constants.py, which will improve the opponent performance but exponentially increase the calculation time (recommended no more than 5).

If you want to integrate the chess AI into your own project, you can use the `determine_best_move` function to get the AI's best move for a given board state and depth. The board state should be a valid FEN string representing the current board position. For example:

board_state = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"  # Example board state
depth = 2  # Specify the desired depth for the AI
best_move = determine_best_move(board_state, depth)
print("Best move:", best_move)

---------------------------------------

TODO:

Algorithmic: add parallelization and improve late move reduction

GUI: add piece icons, flip king/queen when user plays black, fix termination criteria

Code: test determine_best_move, general refactoring
