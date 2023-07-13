import chess
import tkinter as tk
from tkinter import messagebox
import random
import pygame

# Global variables for GUI
board_buttons = {}
selected_square = None
player_color = None

# Board dimensions
BOARD_WIDTH = BOARD_HEIGHT = 600
SQUARE_SIZE = BOARD_WIDTH // 8

# Colors
LIGHT_SQUARE_COLOR = (240, 217, 181)
DARK_SQUARE_COLOR = (181, 136, 99)
SELECTED_SQUARE_COLOR = (122, 158, 202)

# Transposition table
transposition_table = {}


def load_piece_images():
    piece_images = {}
    pieces = ["p", "n", "b", "r", "q", "k"]
    colors = ["w", "b"]
    for piece in pieces:
        for color in colors:
            filename = f"images/{piece}_{color}.png"
            image = pygame.image.load(filename)
            image = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
            piece_images[color + piece] = image
    return piece_images


# Load piece images
piece_images = load_piece_images()


def evaluate_board(board):
    # Piece weights
    piece_weights = {
        chess.KING: 200,
        chess.QUEEN: 9,
        chess.ROOK: 5,
        chess.BISHOP: 3,
        chess.KNIGHT: 3,
        chess.PAWN: 1
    }

    # Evaluate material balance
    material_score = sum(
        (len(board.pieces(piece_type, chess.WHITE)) - len(board.pieces(piece_type, chess.BLACK))) * weight
        for piece_type, weight in piece_weights.items()
    )

    # Evaluate pawn structure
    white_pawns = list(board.pieces(chess.PAWN, chess.WHITE))
    black_pawns = list(board.pieces(chess.PAWN, chess.BLACK))

    doubled_pawns = sum(
        white_pawns.count(p) > 1
        for p in white_pawns
    ) - sum(
        black_pawns.count(p) > 1
        for p in black_pawns
    )

    blocked_pawns = sum(
        board.is_pinned(chess.WHITE, p)
        for p in white_pawns
    ) - sum(
        board.is_pinned(chess.BLACK, p)
        for p in black_pawns
    )

    isolated_pawns = sum(
        not any(board.piece_at(attacked_square) and board.piece_at(attacked_square).piece_type == chess.PAWN
                for attacked_square in board.attacks(p))
        for p in white_pawns + black_pawns
    )

    pawn_structure_score = -0.5 * (doubled_pawns + blocked_pawns + isolated_pawns)

    # Evaluate piece mobility
    player_legal_moves = list(board.legal_moves)
    opponent_legal_moves = list(board.legal_moves)
    mobility_score = 0.1 * (len(player_legal_moves) - len(opponent_legal_moves))

    # Evaluate captures
    captures_score = 0.5 * len([move for move in board.legal_moves if board.is_capture(move)])

    # Evaluate king safety
    player_king_square = board.king(chess.WHITE)
    opponent_king_square = board.king(chess.BLACK)
    king_safety_score = 0.0
    if player_king_square and opponent_king_square:
        player_king_file = chess.square_file(player_king_square)
        player_king_rank = chess.square_rank(player_king_square)
        opponent_king_file = chess.square_file(opponent_king_square)
        opponent_king_rank = chess.square_rank(opponent_king_square)
        king_distance = abs(player_king_file - opponent_king_file) + abs(player_king_rank - opponent_king_rank)
        king_safety_score = -0.05 * king_distance

    # Evaluate threatened pieces
    threatened_pieces_score = 0.0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == board.turn:
            if any(move.to_square == square and board.is_capture(move) for move in opponent_legal_moves):
                threatened_pieces_score -= piece_weights.get(piece.piece_type, 0)

    # Calculate the total score
    total_score = (material_score + pawn_structure_score + mobility_score + captures_score
                   + king_safety_score + threatened_pieces_score) * board.turn

    return total_score

def quiescence_search(board, alpha, beta, depth):
    stand_pat = evaluate_board(board)
    if depth == 0 or board.is_game_over():
        return stand_pat

    if stand_pat >= beta:
        return beta

    if alpha < stand_pat:
        alpha = stand_pat

    for move in board.legal_moves:
        if board.is_capture(move):
            board.push(move)
            score = -quiescence_search(board, -beta, -alpha, depth - 1)
            board.pop()

            if score >= beta:
                return beta

            if score > alpha:
                alpha = score

    return alpha

def alphabeta(board, depth, alpha, beta, maximizing_player):
    # Check if the current position is already evaluated
    key = (board.board_fen(), depth)
    if key in transposition_table:
        return transposition_table[key]

    if depth == 0 or board.is_game_over():
        # If the maximum depth is reached or the game is over, evaluate the board and return its score
        score = evaluate_board(board)
        transposition_table[key] = score
        return score

    if depth <= 0:
        return quiescence_search(board, alpha, beta, depth)

    if maximizing_player:
        for move in board.legal_moves:
            board.push(move)
            eval_score = alphabeta(board, depth - 1, alpha, beta, False)
            board.pop()
            if eval_score >= beta:
                return beta
            if eval_score > alpha:
                alpha = eval_score
        return alpha
    else:
        for move in board.legal_moves:
            board.push(move)
            eval_score = alphabeta(board, depth - 1, alpha, beta, True)
            board.pop()
            if eval_score <= alpha:
                return alpha
            if eval_score < beta:
                beta = eval_score
        return beta


def determine_best_move(board_state, depth):
    board = chess.Board(board_state)
    best_move = find_best_move(board, depth)
    return best_move.uci()


def on_square_click(square):
    global selected_square
    if selected_square is None:
        selected_square = square
    else:
        move = chess.Move(selected_square, square)
        if move in board.legal_moves:
            board.push(move)
            refresh_board()
            selected_square = None
            if player_color == chess.WHITE:
                make_ai_move()
            else:
                refresh_board()  # Refresh the board to update the player's move
                make_ai_move()  # Make AI move after player's move
        else:
            messagebox.showinfo("Invalid Move", "Invalid move. Please try again.")
            selected_square = None


def refresh_board():
    for square, button in board_buttons.items():
        if player_color == chess.WHITE:
            piece = board.piece_at(square)
        else:
            flipped_square = chess.square(chess.square_file(square), 7 - chess.square_rank(square))
            piece = board.piece_at(flipped_square)
        piece_symbol = piece.symbol() if piece else ""
        button["text"] = piece_symbol


def make_ai_move():
    best_move = find_best_move(board, depth)
    board.push(best_move)
    refresh_board()


def create_board_ui(root):
    global board_buttons
    board_frame = tk.Frame(root)
    board_frame.pack()
    for row in range(8):
        for col in range(8):
            square = chess.square(col, 7 - row)
            if player_color == chess.WHITE:
                button = tk.Button(board_frame, width=5, height=2, command=lambda sq=square: on_square_click(sq))
            else:
                button = tk.Button(board_frame, width=5, height=2, command=lambda sq=square: on_square_click(
                    chess.square(chess.square_file(sq), 7 - chess.square_rank(sq))))
            button.grid(row=row, column=col)
            board_buttons[square] = button


def find_best_move(board, depth, aspiration_window=100):
    best_eval = float('-inf')
    best_move = None

    for current_depth in range(1, depth + 1):
        if best_move is not None:
            # Narrow the aspiration window around the previous best move
            alpha = best_eval - aspiration_window
            beta = best_eval + aspiration_window
        else:
            alpha = float('-inf')
            beta = float('inf')

        ordered_moves = order_moves(board.legal_moves)  # Order the moves

        for move in ordered_moves:
            board.push(move)
            eval_score = alphabeta(board, current_depth - 1, alpha, beta, maximizing_player=False)
            board.pop()
            if eval_score > best_eval:
                best_eval = eval_score
                best_move = move

    return best_move

def order_moves(moves):
    ordered_moves = []

    # Capture moves
    capture_moves = [move for move in moves if board.is_capture(move)]
    ordered_moves.extend(capture_moves)

    # Promotion moves
    promotion_moves = [move for move in moves if move.promotion]
    ordered_moves.extend(promotion_moves)

    # Check moves
    check_moves = [move for move in moves if board.is_check()]
    ordered_moves.extend(check_moves)

    # Non-capture and non-promotion moves
    non_capture_moves = [move for move in moves if move not in capture_moves and move not in promotion_moves]
    ordered_moves.extend(non_capture_moves)

    return ordered_moves


def play_as_white(depth):
    global board, player_color
    player_color = chess.WHITE
    board = chess.Board()
    root = tk.Tk()
    root.title("Chess")
    create_board_ui(root)
    refresh_board()
    root.mainloop()

def play_as_black(depth):
    global board, player_color
    player_color = chess.BLACK
    board = chess.Board()
    root = tk.Tk()
    root.title("Chess")
    create_board_ui(root)
    refresh_board()
    if player_color == chess.BLACK:
        make_ai_move()  # AI makes the first move as Black
    root.mainloop()

def play_random_color(depth):
    if random.choice([True, False]):
        play_as_white(depth)
    else:
        play_as_black(depth)


def play_chess(depth):
    global board, player_color, selected_square
    pygame.init()
    screen = pygame.display.set_mode((BOARD_WIDTH, BOARD_HEIGHT))
    clock = pygame.time.Clock()
    board = chess.Board()
    player_color = random.choice([chess.WHITE, chess.BLACK])
    selected_square = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    file = mouse_pos[0] // SQUARE_SIZE
                    rank = 7 - (mouse_pos[1] // SQUARE_SIZE)
                    square = chess.square(file, rank)
                    if selected_square:
                        move = chess.Move(selected_square, square)
                        if move in board.legal_moves:
                            board.push(move)
                            refresh_board()
                            selected_square = None
                            if player_color == chess.WHITE:
                                make_ai_move()
                        else:
                            selected_square = square
                    else:
                        if player_color == chess.WHITE:
                            piece = board.piece_at(square)
                        else:
                            piece = board.piece_at(chess.square(chess.square_file(square),
                                                                 7 - chess.square_rank(square)))
                        if player_color == chess.WHITE and piece and piece.color == chess.WHITE:
                            selected_square = square
                        elif player_color == chess.BLACK and piece and piece.color == chess.BLACK:
                            selected_square = square

        screen.fill((255, 255, 255))
        if selected_square is not None:
            selected_square_pos = selected_square if player_color == chess.WHITE else chess.square(chess.square_file(selected_square),
                                                                                                 7 - chess.square_rank(selected_square))
            pygame.draw.rect(screen, SELECTED_SQUARE_COLOR, (
                chess.square_file(selected_square_pos) * SQUARE_SIZE,
                (7 - chess.square_rank(selected_square_pos)) * SQUARE_SIZE,
                SQUARE_SIZE, SQUARE_SIZE))

        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                color = LIGHT_SQUARE_COLOR if (row + col) % 2 == 0 else DARK_SQUARE_COLOR
                piece = board.piece_at(square)
                if piece:
                    piece_image = piece_images[piece.symbol()]
                    screen.blit(piece_image, (col * SQUARE_SIZE, row * SQUARE_SIZE))
                pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


# Example usage
depth = 2  # Specify the desired depth for the AI

# Play as White
play_as_white(depth)

# Play as Black
play_as_black(depth)

# Play with random color
play_random_color(depth)
