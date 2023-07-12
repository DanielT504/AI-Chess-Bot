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

    # Evaluate piece mobility (number of legal moves)
    mobility_score = 0.1 * (len(list(board.legal_moves)) - len(list(board.legal_moves)))

    # Calculate the total score
    total_score = (material_score + pawn_structure_score + mobility_score) * board.turn

    return total_score


def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0 or board.is_game_over():
        # If the maximum depth is reached or the game is over, evaluate the board and return its score
        return evaluate_board(board)

    if maximizing_player:
        max_eval = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                # Beta cutoff
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                # Alpha cutoff
                break
        return min_eval


def find_best_move(board, depth):
    best_eval = float('-inf')
    best_move = None
    for move in board.legal_moves:
        board.push(move)
        eval_score = minimax(board, depth - 1, float('-inf'), float('inf'), False)
        board.pop()
        if eval_score > best_eval:
            best_eval = eval_score
            best_move = move
    return best_move


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
    global board, player_color
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

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


# Example usage
depth = 3  # Specify the desired depth for the AI

# Play as White
play_as_white(depth)

# Play as Black
play_as_black(depth)

# Play with random color
play_random_color(depth)