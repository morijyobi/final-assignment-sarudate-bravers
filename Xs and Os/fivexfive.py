import pygame
import sys

pygame.init()

# 画面設定
screen_info = pygame.display.Info()
screen_width, screen_height = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("5×5 マルバツゲーム")

# フォント設定
font_title = pygame.font.SysFont("meiryo", 48)
font_common = pygame.font.SysFont("meiryo", 30)
font_board = pygame.font.SysFont("meiryo", 50)  # 盤面に合わせて少し小さく

# 色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
DARK_GRAY = (60, 60, 60)

# ゲーム状態
board = [[None for _ in range(5)] for _ in range(5)]
current_player = "○"
game_over = False
winner = None
my_turn = True
my_symbol = "○"
opponent_symbol = "×"

# ネットワーク接続（仮）
network = None

# プレイヤー情報
my_name = "プレイヤー1"
my_icon = "➀"
my_title = "第98代唯一皇帝"

opponent_name = "プレイヤー2"
opponent_icon = "➁"
opponent_title = "第11皇子"

# 盤面設定
board_size = 400  # ← 縮小（500から400）
cell_size = board_size // 5
board_x = screen_width // 2 - board_size // 2
board_y = screen_height // 2 - board_size // 2

# 制限時間
INITIAL_TIME = 60
my_time_left = INITIAL_TIME
opponent_time_left = INITIAL_TIME
turn_start_time = 0
time_over = False
time_winner = None

def init_game(my_info=None, opponent_info=None, is_my_turn=True, network_obj=None):
    global board, current_player, game_over, winner, my_turn, my_symbol, opponent_symbol, network
    global my_name, my_icon, my_title, opponent_name, opponent_icon, opponent_title
    global my_time_left, opponent_time_left, time_over, time_winner, turn_start_time

    board = [[None for _ in range(5)] for _ in range(5)]
    game_over = False
    winner = None

    my_time_left = INITIAL_TIME
    opponent_time_left = INITIAL_TIME
    time_over = False
    time_winner = None
    turn_start_time = 0

    my_turn = is_my_turn
    if is_my_turn:
        my_symbol = "○"
        opponent_symbol = "×"
        current_player = "○"
    else:
        my_symbol = "×"
        opponent_symbol = "○"
        current_player = "○"

    network = network_obj

    if my_info:
        my_name, my_icon, my_title = my_info
    if opponent_info:
        opponent_name, opponent_icon, opponent_title = opponent_info

    start_turn_timer()

def format_time(seconds):
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes:02d}:{secs:02d}"

def start_turn_timer():
    global turn_start_time
    turn_start_time = pygame.time.get_ticks() / 1000.0

def update_timer():
    global my_time_left, opponent_time_left, time_over, time_winner, game_over, turn_start_time

    if game_over or time_over or turn_start_time == 0:
        return

    current_time = pygame.time.get_ticks() / 1000.0
    elapsed = current_time - turn_start_time

    if current_player == my_symbol and my_turn:
        my_time_left = max(0, my_time_left - elapsed)
        if my_time_left <= 0:
            time_over = True
            time_winner = opponent_symbol
            game_over = True
    elif current_player == opponent_symbol and not my_turn:
        opponent_time_left = max(0, opponent_time_left - elapsed)
        if opponent_time_left <= 0:
            time_over = True
            time_winner = my_symbol
            game_over = True

    turn_start_time = current_time

def draw_board():
    global board_x, board_y
    board_x = screen_width // 2 - board_size // 2
    board_y = screen_height // 2 - board_size // 2

    pygame.draw.rect(screen, WHITE, (board_x, board_y, board_size, board_size))

    for i in range(1, 5):
        pygame.draw.line(screen, BLACK,
                         (board_x + i * cell_size, board_y),
                         (board_x + i * cell_size, board_y + board_size), 3)
        pygame.draw.line(screen, BLACK,
                         (board_x, board_y + i * cell_size),
                         (board_x + board_size, board_y + i * cell_size), 3)

    pygame.draw.rect(screen, BLACK, (board_x, board_y, board_size, board_size), 3)

    for row in range(5):
        for col in range(5):
            if board[row][col]:
                cell_center_x = board_x + col * cell_size + cell_size // 2
                cell_center_y = board_y + row * cell_size + cell_size // 2

                text = font_board.render(board[row][col], True, RED if board[row][col] == "○" else BLUE)
                text_rect = text.get_rect(center=(cell_center_x, cell_center_y))
                screen.blit(text, text_rect)

def draw_player_info():
    my_info_x = 20
    my_info_y = screen_height - 150
    my_name_text = font_common.render(f"名前: {my_name}", True, WHITE)
    my_icon_text = font_common.render(f"アイコン: {my_icon}", True, WHITE)
    my_title_text = font_common.render(f"称号: {my_title}", True, WHITE)

    my_time_color = RED if my_time_left < 10 else WHITE
    my_time_text = font_common.render(f"持ち時間: {format_time(my_time_left)}", True, my_time_color)

    screen.blit(my_name_text, (my_info_x, my_info_y))
    screen.blit(my_icon_text, (my_info_x, my_info_y + 30))
    screen.blit(my_title_text, (my_info_x, my_info_y + 60))
    screen.blit(my_time_text, (my_info_x, my_info_y + 90))

    opponent_info_x = screen_width - 300
    opponent_info_y = 20
    opp_name_text = font_common.render(f"名前: {opponent_name}", True, WHITE)
    opp_icon_text = font_common.render(f"アイコン: {opponent_icon}", True, WHITE)
    opp_title_text = font_common.render(f"称号: {opponent_title}", True, WHITE)

    opp_time_color = RED if opponent_time_left < 10 else WHITE
    opp_time_text = font_common.render(f"持ち時間: {format_time(opponent_time_left)}", True, opp_time_color)

    screen.blit(opp_name_text, (opponent_info_x, opponent_info_y))
    screen.blit(opp_icon_text, (opponent_info_x, opponent_info_y + 30))
    screen.blit(opp_title_text, (opponent_info_x, opponent_info_y + 60))
    screen.blit(opp_time_text, (opponent_info_x, opponent_info_y + 90))

def draw_game_status():
    if game_over:
        if time_over:
            if time_winner == my_symbol:
                status_text = "時間切れ！あなたの勝利！"
                color = GREEN
            else:
                status_text = "時間切れ！相手の勝利！"
                color = RED
        elif winner:
            if winner == my_symbol:
                status_text = "あなたの勝利！"
                color = GREEN
            else:
                status_text = "相手の勝利！"
                color = RED
        else:
            status_text = "引き分け！"
            color = YELLOW
    else:
        if network is None:
            status_text = "ネットワーク接続が必要です"
            color = RED
        elif my_turn:
            status_text = "あなたのターンです"
            color = GREEN
        else:
            status_text = "相手のターンです"
            color = YELLOW

    status_surface = font_title.render(status_text, True, color)
    status_rect = status_surface.get_rect(center=(screen_width // 2, 100))
    screen.blit(status_surface, status_rect)

def check_winner():
    global game_over, winner

    # 行チェック
    for row in range(5):
        if board[row][0] and all(board[row][col] == board[row][0] for col in range(5)):
            game_over = True
            winner = board[row][0]
            return

    # 列チェック
    for col in range(5):
        if board[0][col] and all(board[row][col] == board[0][col] for row in range(5)):
            game_over = True
            winner = board[0][col]
            return

    # 対角線チェック
    if board[0][0] and all(board[i][i] == board[0][0] for i in range(5)):
        game_over = True
        winner = board[0][0]
        return

    if board[0][4] and all(board[i][4 - i] == board[0][4] for i in range(5)):
        game_over = True
        winner = board[0][4]
        return

    # 引き分け
    if all(board[row][col] is not None for row in range(5) for col in range(5)):
        game_over = True
        winner = None

def handle_click(pos):
    global current_player, my_turn

    if game_over or network is None:
        return

    if not (current_player == my_symbol and my_turn):
        return

    mouse_x, mouse_y = pos

    if (board_x <= mouse_x <= board_x + board_size and
        board_y <= mouse_y <= board_y + board_size):

        col = (mouse_x - board_x) // cell_size
        row = (mouse_y - board_y) // cell_size

        if board[row][col] is None:
            board[row][col] = my_symbol
            move_message = f"MOVE:{row}:{col}:{my_symbol}"
            network.send(move_message)
            check_winner()

            if not game_over:
                current_player = opponent_symbol
                my_turn = False
                start_turn_timer()

def process_network_messages():
    global current_player, my_turn

    if network is None:
        return

    msg = network.receive()
    if msg:
        if msg.startswith("MOVE:"):
            _, row_str, col_str, symbol = msg.split(":")
            row, col = int(row_str), int(col_str)

            if board[row][col] is None:
                board[row][col] = symbol
                check_winner()

                if not game_over:
                    current_player = my_symbol
                    my_turn = True
                    start_turn_timer()

def main():
    if not pygame.get_init():
        pygame.init()

    global screen, screen_width, screen_height
    screen_info = pygame.display.Info()
    screen_width, screen_height = screen_info.current_w, screen_info.current_h
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption("5×5 マルバツゲーム")

    clock = pygame.time.Clock()
    running = True

    while running:
        process_network_messages()
        update_timer()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    handle_click(event.pos)

        screen.fill(DARK_GRAY)

        draw_player_info()
        draw_board()
        draw_game_status()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    init_game()
    main()
