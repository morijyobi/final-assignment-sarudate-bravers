import pygame
import sys

pygame.init()

# 画面設定
screen_info = pygame.display.Info()
screen_width, screen_height = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("3×3 マルバツゲーム")

# フォント設定
font_title = pygame.font.SysFont("meiryo", 48)
font_common = pygame.font.SysFont("meiryo", 30)
font_board = pygame.font.SysFont("meiryo", 80)

# 色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
DARK_GRAY = (60, 60, 60)

# ゲーム状態
board = [[None for _ in range(3)] for _ in range(3)]
current_player = "○"  # ○が先行、×が後攻
game_over = False
winner = None
my_turn = True  # 自分のターンかどうか
my_symbol = "○"  # 自分の記号（○ or ×）
opponent_symbol = "×"  # 相手の記号

# ネットワーク接続
network = None
current_player = "○"  # ○が先行、×が後攻
game_over = False
winner = None

# プレイヤー情報（デフォルト値）
my_name = "プレイヤー1"
my_icon = "➀"
my_title = "第98代唯一皇帝"

opponent_name = "プレイヤー2"
opponent_icon = "➁"
opponent_title = "第11皇子"

# 盤面設定
board_size = 300
cell_size = board_size // 3
board_x = screen_width // 2 - board_size // 2
board_y = screen_height // 2 - board_size // 2

# 持ち時間設定（秒）
INITIAL_TIME = 10  # 10秒
my_time_left = INITIAL_TIME
opponent_time_left = INITIAL_TIME
turn_start_time = 0  # 現在のターンが始まった時刻
time_over = False  # 時間切れフラグ
time_winner = None  # 時間切れによる勝者

def init_game(my_info=None, opponent_info=None, is_my_turn=True, network_obj=None):
    """ゲームを初期化する"""
    global board, current_player, game_over, winner, my_turn, my_symbol, opponent_symbol, network
    global my_name, my_icon, my_title, opponent_name, opponent_icon, opponent_title
    global my_time_left, opponent_time_left, time_over, time_winner, turn_start_time
    
    # 盤面リセット
    board = [[None for _ in range(3)] for _ in range(3)]
    game_over = False
    winner = None
    
    # 持ち時間リセット
    my_time_left = INITIAL_TIME
    opponent_time_left = INITIAL_TIME
    time_over = False
    time_winner = None
    turn_start_time = 0
    
    # ターン設定
    my_turn = is_my_turn
    if is_my_turn:
        my_symbol = "○"
        opponent_symbol = "×"
        current_player = "○"
    else:
        my_symbol = "×"
        opponent_symbol = "○"
        current_player = "○"  # ゲームは常に○から開始
    
    # ネットワーク接続を設定
    network = network_obj
    
    # プレイヤー情報設定
    if my_info:
        my_name, my_icon, my_title = my_info
    if opponent_info:
        opponent_name, opponent_icon, opponent_title = opponent_info
    
    # 初期ターンのタイマーを開始
    start_turn_timer()
    
    print(f"[DEBUG] ゲーム初期化: 自分={my_symbol}, 相手={opponent_symbol}, 自分のターン={my_turn}")

def format_time(seconds):
    """秒数を分:秒の形式にフォーマット"""
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes:02d}:{secs:02d}"

def start_turn_timer():
    """現在のターンのタイマーを開始"""
    global turn_start_time
    turn_start_time = pygame.time.get_ticks() / 1000.0  # ミリ秒を秒に変換

def update_timer():
    """タイマーを更新し、時間切れをチェック"""
    global my_time_left, opponent_time_left, time_over, time_winner, game_over, turn_start_time
    
    if game_over or time_over or turn_start_time == 0:
        return
    
    current_time = pygame.time.get_ticks() / 1000.0
    elapsed = current_time - turn_start_time
    
    # 現在のプレイヤーの持ち時間を減らす
    if current_player == my_symbol and my_turn:
        my_time_left = max(0, my_time_left - elapsed)
        if my_time_left <= 0:
            time_over = True
            time_winner = opponent_symbol
            game_over = True
            print("[DEBUG] 自分の時間切れ")
    elif current_player == opponent_symbol and not my_turn:
        opponent_time_left = max(0, opponent_time_left - elapsed)
        if opponent_time_left <= 0:
            time_over = True
            time_winner = my_symbol
            game_over = True
            print("[DEBUG] 相手の時間切れ")
    
    # タイマーをリセット
    turn_start_time = current_time

def draw_board():
    """3×3の盤面を描画する"""
    # 盤面位置を現在の画面サイズに基づいて再計算
    global board_x, board_y
    board_x = screen_width // 2 - board_size // 2
    board_y = screen_height // 2 - board_size // 2
    
    # 盤面の背景
    pygame.draw.rect(screen, WHITE, (board_x, board_y, board_size, board_size))
    
    # 格子線を描画
    for i in range(1, 3):
        # 縦線
        pygame.draw.line(screen, BLACK, 
                        (board_x + i * cell_size, board_y), 
                        (board_x + i * cell_size, board_y + board_size), 3)
        # 横線
        pygame.draw.line(screen, BLACK, 
                        (board_x, board_y + i * cell_size), 
                        (board_x + board_size, board_y + i * cell_size), 3)
    
    # 外枠
    pygame.draw.rect(screen, BLACK, (board_x, board_y, board_size, board_size), 3)
    
    # マルバツを描画
    for row in range(3):
        for col in range(3):
            if board[row][col]:
                cell_center_x = board_x + col * cell_size + cell_size // 2
                cell_center_y = board_y + row * cell_size + cell_size // 2
                
                text = font_board.render(board[row][col], True, RED if board[row][col] == "○" else BLUE)
                text_rect = text.get_rect(center=(cell_center_x, cell_center_y))
                screen.blit(text, text_rect)

def draw_player_info():
    """プレイヤー情報を描画する"""
    # 絵文字用の大きなフォントを作成（複数フォントでフォールバック）
    font_emoji = None
    emoji_fonts = ["segoeuiemoji", "notocoloremoji", "twemoji", "applesymbol", "applecoloremoji"]
    for font_name in emoji_fonts:
        try:
            font_emoji = pygame.font.SysFont(font_name, 64)
            break
        except:
            continue
    
    if font_emoji is None:
        font_emoji = font_common  # フォールバック
    
    # 自分の情報（画面左下）
    my_info_x = 20
    my_info_y = screen_height - 180  # アイコンが大きくなるので少し上に移動
    my_name_text = font_common.render(f"名前: {my_name}", True, WHITE)
    my_title_text = font_common.render(f"称号: {my_title}", True, WHITE)
    
    # アイコンを大きく表示
    try:
        my_icon_text = font_emoji.render(my_icon, True, YELLOW)
        icon_rect = my_icon_text.get_rect()
        icon_rect.x = my_info_x
        icon_rect.y = my_info_y + 30
    except:
        # 絵文字フォントが使えない場合は通常フォントを使用
        my_icon_text = font_common.render(f"アイコン: {my_icon}", True, WHITE)
        icon_rect = my_icon_text.get_rect()
        icon_rect.x = my_info_x
        icon_rect.y = my_info_y + 30
    
    # 自分の持ち時間（色分け：時間が少ないと赤色）
    my_time_color = RED if my_time_left < 60 else (YELLOW if my_time_left < 120 else WHITE)
    my_time_text = font_common.render(f"持ち時間: {format_time(my_time_left)}", True, my_time_color)
    
    screen.blit(my_name_text, (my_info_x, my_info_y))
    screen.blit(my_icon_text, icon_rect)
    screen.blit(my_title_text, (my_info_x, my_info_y + 100))  # アイコンが大きくなった分下に移動
    screen.blit(my_time_text, (my_info_x, my_info_y + 130))
    
    # 対戦相手の情報（画面右上）
    opponent_info_x = screen_width - 300
    opponent_info_y = 20
    opp_name_text = font_common.render(f"名前: {opponent_name}", True, WHITE)
    opp_title_text = font_common.render(f"称号: {opponent_title}", True, WHITE)
    
    # 相手のアイコンを大きく表示
    try:
        opp_icon_text = font_emoji.render(opponent_icon, True, YELLOW)
        opp_icon_rect = opp_icon_text.get_rect()
        opp_icon_rect.x = opponent_info_x
        opp_icon_rect.y = opponent_info_y + 30
    except:
        # 絵文字フォントが使えない場合は通常フォントを使用
        opp_icon_text = font_common.render(f"アイコン: {opponent_icon}", True, WHITE)
        opp_icon_rect = opp_icon_text.get_rect()
        opp_icon_rect.x = opponent_info_x
        opp_icon_rect.y = opponent_info_y + 30
    
    # 相手の持ち時間（色分け：時間が少ないと赤色）
    opp_time_color = RED if opponent_time_left < 60 else (YELLOW if opponent_time_left < 120 else WHITE)
    opp_time_text = font_common.render(f"持ち時間: {format_time(opponent_time_left)}", True, opp_time_color)
    
    screen.blit(opp_name_text, (opponent_info_x, opponent_info_y))
    screen.blit(opp_icon_text, opp_icon_rect)
    screen.blit(opp_title_text, (opponent_info_x, opponent_info_y + 100))  # アイコンが大きくなった分下に移動
    screen.blit(opp_time_text, (opponent_info_x, opponent_info_y + 130))

def draw_game_status():
    """ゲーム状態を描画する"""
    if game_over:
        if time_over:
            # 時間切れによる勝敗
            if time_winner == my_symbol:
                status_text = "時間切れ！あなたの勝利！"
                color = GREEN
            else:
                status_text = "時間切れ！相手の勝利！"
                color = RED
        elif winner:
            # 通常の勝敗
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
    """勝敗判定"""
    global game_over, winner
    
    # 行をチェック
    for row in range(3):
        if board[row][0] == board[row][1] == board[row][2] and board[row][0] is not None:
            game_over = True
            winner = board[row][0]
            return
    
    # 列をチェック
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] and board[0][col] is not None:
            game_over = True
            winner = board[0][col]
            return
    
    # 対角線をチェック
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] is not None:
        game_over = True
        winner = board[0][0]
        return
    
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] is not None:
        game_over = True
        winner = board[0][2]
        return
    
    # 引き分けチェック
    if all(board[row][col] is not None for row in range(3) for col in range(3)):
        game_over = True
        winner = None

def handle_click(pos):
    """マウスクリック処理"""
    global current_player, my_turn
    
    if game_over or network is None:
        return
    
    # 自分のターンでない場合は何もしない
    if not (current_player == my_symbol and my_turn):
        print(f"[DEBUG] 自分のターンではありません: current_player={current_player}, my_symbol={my_symbol}, my_turn={my_turn}")
        return
    
    mouse_x, mouse_y = pos
    
    # クリック位置が盤面内かチェック
    if (board_x <= mouse_x <= board_x + board_size and 
        board_y <= mouse_y <= board_y + board_size):
        
        # どのセルがクリックされたか計算
        col = (mouse_x - board_x) // cell_size
        row = (mouse_y - board_y) // cell_size
        
        # セルが空いているかチェック
        if board[row][col] is None:
            # 自分の手を打つ
            board[row][col] = my_symbol
            print(f"[DEBUG] 手を打ちました: ({row}, {col}) = {my_symbol}")
            
            # 相手に手を送信
            move_message = f"MOVE:{row}:{col}:{my_symbol}"
            network.send(move_message)
            print(f"[DEBUG] 相手に手を送信: {move_message}")
            
            check_winner()
            
            # ターン交代
            if not game_over:
                current_player = opponent_symbol
                my_turn = False
                start_turn_timer()  # 相手のターンのタイマーを開始
                print(f"[DEBUG] ターン交代: current_player={current_player}, my_turn={my_turn}")

def process_network_messages():
    """ネットワークメッセージを処理する"""
    global current_player, my_turn
    
    if network is None:
        return
    
    msg = network.receive()
    if msg:
        print(f"[DEBUG] ゲーム中メッセージ受信: {msg}")
        if msg.startswith("MOVE:"):
            # 相手の手を受信
            _, row_str, col_str, symbol = msg.split(":")
            row, col = int(row_str), int(col_str)
            
            # 盤面に相手の手を反映
            if board[row][col] is None:
                board[row][col] = symbol
                print(f"[DEBUG] 相手の手を反映: ({row}, {col}) = {symbol}")
                
                check_winner()
                
                # ターン交代
                if not game_over:
                    current_player = my_symbol
                    my_turn = True
                    start_turn_timer()  # 自分のターンのタイマーを開始
                    print(f"[DEBUG] ターン交代: current_player={current_player}, my_turn={my_turn}")


def main():
    """メインゲームループ"""
    # pygameが初期化されているかチェック
    if not pygame.get_init():
        pygame.init()
        
    # 画面を再設定（main.pyから呼ばれた場合、画面が閉じられている可能性があるため）
    global screen, screen_width, screen_height
    screen_info = pygame.display.Info()
    screen_width, screen_height = screen_info.current_w, screen_info.current_h
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption("3×3 マルバツゲーム")
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        # ネットワークメッセージを処理
        process_network_messages()
        
        # タイマーを更新
        update_timer()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左クリック
                    handle_click(event.pos)
        
        # 画面描画
        screen.fill(DARK_GRAY)
        
        draw_player_info()
        draw_board()
        draw_game_status()
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    # ゲーム初期化
    init_game()
    main()