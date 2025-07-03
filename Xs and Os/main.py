import pygame
import threading
import sys
from network import Network

pygame.init()
screen_info = pygame.display.Info()
screen_width, screen_height = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("コード・サルダテ")

# 背景画像とフォント設定
background_image = pygame.image.load("D-T9JlqUYAEo7q5.png")
background_image = pygame.transform.scale(background_image, (screen_width, screen_height))

font_title = pygame.font.SysFont("meiryo", 48)
font_subtitle = pygame.font.SysFont("meiryo", 24)
font_button = pygame.font.SysFont("meiryo", 32)
font_common = pygame.font.SysFont("meiryo", 28)

# 色
RED = (200, 30, 30)
SOFT_WHITE_BLUE = (210, 230, 255)
DEEP_BLUE_GRAY = (40, 60, 90)

# 通信用
network = Network()

# 状態管理
state = "title"  # title, select_role, input_ip, waiting, username, rule_selection, waiting_for_host_rule, select_difficulty
role = None
ip_address = ""
input_text = ""
username = ""
difficulty = None

# 難易度選択用のボタン
difficulty_buttons = {
    "3x3": pygame.Rect(screen_width // 2 - 270, screen_height // 2 - 50, 150, 60),
    "5x5": pygame.Rect(screen_width // 2 - 75, screen_height // 2 - 50, 150, 60),
    "3x3x3": pygame.Rect(screen_width // 2 + 120, screen_height // 2 - 50, 150, 60),
}
ready_button = pygame.Rect(screen_width // 2 - 100, screen_height // 2 + 130, 200, 60)

# 難易度説明
difficulty_descriptions = {
    "3x3": "シンプルな9マス、初心者向け！",
    "5x5": "25マスの中量級、戦略的な展開！",
    "3x3x3": "立体3次元、上級者向けモード！"
}

button_rect = pygame.Rect(screen_width // 2 - 100, screen_height - 150, 200, 60)

def render_text_with_outline(text, font, text_color, outline_color):
    base = font.render(text, True, text_color)
    outline = pygame.Surface((base.get_width() + 4, base.get_height() + 4), pygame.SRCALPHA)
    for dx in [-2, 0, 2]:
        for dy in [-2, 0, 2]:
            if dx != 0 or dy != 0:
                outline.blit(font.render(text, True, outline_color), (dx + 2, dy + 2))
    outline.blit(base, (2, 2))
    return outline

# 通信スレッド
def start_server():
    global state
    network.start_server()
    state = "username"

def connect_to_server(ip):
    global state
    network.connect_to_server(ip)
    if network.connected:
        state = "username"

# メインループ
running = True
while running:
    screen.blit(background_image, (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if state == "title":
                running = False
            elif state in ["select_role", "input_ip", "waiting"]:
                state = "title"
                input_text = ""
        if event.type == pygame.MOUSEBUTTONDOWN and state == "title":
            if button_rect.collidepoint(event.pos):
                state = "select_role"

        if state == "select_role" and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                role = "server"
                ip_address = network.get_my_ip()
                state = "waiting"
                threading.Thread(target=start_server, daemon=True).start()
            elif event.key == pygame.K_c:
                role = "client"
                input_text = ""
                state = "input_ip"

        elif state == "input_ip" and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                state = "waiting"
                threading.Thread(target=connect_to_server, args=(input_text,), daemon=True).start()
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            else:
                input_text += event.unicode
                
        elif state == "username" and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if len(username.strip()) > 0:
                    print(f"ユーザー名: {username}")
                    # ホストの場合は難易度選択画面へ、クライアントは待機画面へ
                    if role == "server":
                        state = "select_difficulty"
                    else:
                        state = "waiting_for_host_rule"
            elif event.key == pygame.K_BACKSPACE:
                if len(username) > 0:
                    username = username[:-1]
            elif event.key == pygame.K_ESCAPE:
                state = "title"
                username = ""
            elif event.unicode.isprintable():
                if len(username) < 12:  # 名前の最大長制限
                    username += event.unicode

        elif state == "rule_selection" and event.type == pygame.KEYDOWN:
            # ホスト用のルール選択処理（後で実装）
            if event.key == pygame.K_ESCAPE:
                state = "username"
        
        elif state == "select_difficulty" and event.type == pygame.MOUSEBUTTONDOWN:
            for key, rect in difficulty_buttons.items():
                if rect.collidepoint(event.pos):
                    difficulty = key
            if ready_button.collidepoint(event.pos) and difficulty:
                print(f"選択された難易度: {difficulty}")
                # ここで次の状態へ遷移（ゲーム開始など）
                # state = "game" など

    # 状態別 描画
    if state == "title":
        title_surf = render_text_with_outline("コード・サルダテ", font_title, SOFT_WHITE_BLUE, DEEP_BLUE_GRAY)
        screen.blit(title_surf, (screen_width // 2 - title_surf.get_width() // 2, 150))

        subtitle = "〜置いていいのは、置かれる覚悟があるマスだけだ〜"
        subtitle_surf = render_text_with_outline(subtitle, font_subtitle, SOFT_WHITE_BLUE, DEEP_BLUE_GRAY)
        screen.blit(subtitle_surf, (screen_width // 2 - subtitle_surf.get_width() // 2, 220))

        pygame.draw.rect(screen, RED, button_rect)
        start_text = font_button.render("スタート", True, (255, 255, 255))
        screen.blit(start_text, (button_rect.centerx - start_text.get_width() // 2,
                                 button_rect.centery - start_text.get_height() // 2))

    elif state == "select_role":
        msg = "Sキー：サーバーとして開始　Cキー：クライアントで接続（Escで戻る）"
        text = font_common.render(msg, True, (255, 255, 255))
        screen.blit(text, (screen_width // 2 - text.get_width() // 2, screen_height // 2))

    elif state == "input_ip":
        prompt = "サーバーのIPを入力（Enterで接続 / Escで戻る）:"
        prompt_surf = font_common.render(prompt, True, (255, 255, 255))
        screen.blit(prompt_surf, (screen_width // 2 - prompt_surf.get_width() // 2, screen_height // 2 - 30))

        ip_surf = font_common.render(input_text, True, (255, 255, 255))
        screen.blit(ip_surf, (screen_width // 2 - ip_surf.get_width() // 2, screen_height // 2 + 10))

    elif state == "waiting":
        if role == "server":
            msg = f"接続待機中... あなたのIP: {ip_address}（Escで戻る）"
        else:
            msg = "接続中...（Escで戻る）"
        text = font_common.render(msg, True, (255, 255, 0))
        screen.blit(text, (screen_width // 2 - text.get_width() // 2, screen_height // 2))

    elif state == "username":
        # タイトル
        title_text = font_common.render("ユーザー情報設定", True, (255, 255, 255))
        screen.blit(title_text, (screen_width // 2 - title_text.get_width() // 2, screen_height // 2 - 200))
        
        # ユーザーネーム入力
        name_label = font_common.render("ユーザーネーム:", True, (255, 255, 255))
        screen.blit(name_label, (screen_width // 2 - 200, screen_height // 2 - 40))
        
        name_input_rect = pygame.Rect(screen_width // 2 - 50, screen_height // 2 - 45, 200, 35)
        pygame.draw.rect(screen, (60, 60, 60), name_input_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), name_input_rect, 2, border_radius=8)
        
        name_surface = font_common.render(username, True, (255, 255, 255))
        screen.blit(name_surface, (name_input_rect.x + 10, name_input_rect.y + (name_input_rect.height - name_surface.get_height()) // 2))
        
        # カーソル表示
        if pygame.time.get_ticks() % 1000 < 500:  # 点滅カーソル
            cursor_x = name_input_rect.x + 10 + font_common.size(username)[0]
            pygame.draw.line(screen, (255, 255, 255), (cursor_x, name_input_rect.y + 5), (cursor_x, name_input_rect.y + name_input_rect.height - 5), 2)
        
        # 決定ボタン
        if len(username.strip()) > 0:
            decide_button_rect = pygame.Rect(screen_width // 2 - 75, screen_height // 2 + 50, 150, 50)
            pygame.draw.rect(screen, RED, decide_button_rect, border_radius=12)
            pygame.draw.rect(screen, (255, 255, 255), decide_button_rect, 2, border_radius=12)
            decide_text = font_common.render("決定", True, (255, 255, 255))
            screen.blit(decide_text, (decide_button_rect.centerx - decide_text.get_width() // 2,
                                     decide_button_rect.centery - decide_text.get_height() // 2))
        
        # 操作説明
        instruction = font_common.render("Enterキーで決定 / Escキーで戻る", True, (100, 100, 100))
        screen.blit(instruction, (screen_width // 2 - instruction.get_width() // 2, screen_height // 2 + 120))

    elif state == "select_difficulty":
        # 難易度選択画面（ホスト専用）
        title_surf = render_text_with_outline("難易度選択", font_title, SOFT_WHITE_BLUE, DEEP_BLUE_GRAY)
        screen.blit(title_surf, (screen_width // 2 - title_surf.get_width() // 2, 150))

        # 難易度ボタンを描画
        for key, rect in difficulty_buttons.items():
            color = {"3x3": (0, 200, 0), "5x5": (230, 230, 0), "3x3x3": (200, 0, 0)}[key]
            pygame.draw.rect(screen, color, rect, border_radius=12)

            # 選択されたボタンに白い枠を追加
            if difficulty == key:
                pygame.draw.rect(screen, (255, 255, 255), rect, 4, border_radius=12)

            label = font_button.render(key, True, (0, 0, 0))
            screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

        # 選択された難易度の説明を表示
        if difficulty:
            desc_text = difficulty_descriptions[difficulty]
            desc_surf = font_common.render(desc_text, True, (255, 255, 255))
            screen.blit(desc_surf, (screen_width // 2 - desc_surf.get_width() // 2, screen_height // 2 + 30))

        # 準備完了ボタン
        if difficulty:
            pygame.draw.rect(screen, RED, ready_button, border_radius=12)
            pygame.draw.rect(screen, (255, 255, 255), ready_button, 2, border_radius=12)
            ready_text = font_button.render("準備完了", True, (255, 255, 255))
            screen.blit(ready_text, (ready_button.centerx - ready_text.get_width() // 2,
                                     ready_button.centery - ready_text.get_height() // 2))
        else:
            # 難易度が選択されていない場合はグレーアウト
            pygame.draw.rect(screen, (100, 100, 100), ready_button, border_radius=12)
            pygame.draw.rect(screen, (150, 150, 150), ready_button, 2, border_radius=12)
            ready_text = font_button.render("準備完了", True, (200, 200, 200))
            screen.blit(ready_text, (ready_button.centerx - ready_text.get_width() // 2,
                                     ready_button.centery - ready_text.get_height() // 2))
        
        # 操作説明
        instruction = font_common.render("難易度を選択してから準備完了ボタンを押してください", True, (200, 200, 200))
        screen.blit(instruction, (screen_width // 2 - instruction.get_width() // 2, screen_height // 2 + 200))

    elif state == "rule_selection":
        # ホスト用のルール選択画面
        title_surf = font_common.render("ルール選択", True, (255, 255, 255))
        screen.blit(title_surf, (screen_width // 2 - title_surf.get_width() // 2, screen_height // 2 - 100))
        
        instruction_surf = font_common.render("ルールを選択してください（実装予定）", True, (255, 255, 255))
        screen.blit(instruction_surf, (screen_width // 2 - instruction_surf.get_width() // 2, screen_height // 2))
        
        escape_surf = font_common.render("Escキーで戻る", True, (255, 255, 255))
        screen.blit(escape_surf, (screen_width // 2 - escape_surf.get_width() // 2, screen_height // 2 + 50))

    elif state == "waiting_for_host_rule":
        # クライアント用の待機画面
        title_surf = font_common.render("ホストがルールを選択中です。", True, (255, 255, 0))
        screen.blit(title_surf, (screen_width // 2 - title_surf.get_width() // 2, screen_height // 2 - 50))
        
        wait_surf = font_common.render("しばらくお待ちください...", True, (255, 255, 255))
        screen.blit(wait_surf, (screen_width // 2 - wait_surf.get_width() // 2, screen_height // 2 + 20))
        
        escape_surf = font_common.render("Escキーでタイトルに戻る", True, (200, 200, 200))
        screen.blit(escape_surf, (screen_width // 2 - escape_surf.get_width() // 2, screen_height // 2 + 80))

    pygame.display.flip()

pygame.quit()
sys.exit()