import pygame
import threading
import sys
from network import Network  # network.pyは別途用意済みと仮定

pygame.init()
screen_info = pygame.display.Info()
screen_width, screen_height = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("コード・サルダテ")

background_image = pygame.image.load("D-T9JlqUYAEo7q5.png")
background_image = pygame.transform.scale(background_image, (screen_width, screen_height))

font_title = pygame.font.SysFont("meiryo", 48)
font_subtitle = pygame.font.SysFont("meiryo", 24)
font_button = pygame.font.SysFont("meiryo", 36)
font_common = pygame.font.SysFont("meiryo", 28)

RED = (200, 30, 30)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (60, 60, 60)
SOFT_WHITE_BLUE = (210, 230, 255)
DEEP_BLUE_GRAY = (40, 60, 90)

network = Network()

state = "title"  # title, room_menu, ip_display, ip_input, waiting, username, select_difficulty, rule_selection, waiting_for_host_rule
role = None
ip_address = ""
input_text = ""
username = ""
difficulty = None

difficulty_buttons = {
    "3x3": pygame.Rect(screen_width // 2 - 270, screen_height // 2 - 50, 150, 60),
    "5x5": pygame.Rect(screen_width // 2 - 75, screen_height // 2 - 50, 150, 60),
    "3x3x3": pygame.Rect(screen_width // 2 + 120, screen_height // 2 - 50, 150, 60),
}
ready_button = pygame.Rect(screen_width // 2 - 100, screen_height // 2 + 130, 200, 60)

difficulty_descriptions = {
    "3x3": "シンプルな9マス、初心者向け！",
    "5x5": "25マスの中量級、戦略的な展開！",
    "3x3x3": "立体3次元、上級者向けモード！"
}

cursor_pos = 0
backspace_pressed = False
backspace_timer = 0
input_x = screen_width // 2 - 70
input_y = screen_height // 2

server_ready = False
client_ready = False
server_thread = None
client_thread = None
server_button_pressed = False  # ボタン押下済みフラグ

start_button_rect = pygame.Rect(screen_width // 2 - 120, screen_height - 180, 240, 80)
room_create_button = pygame.Rect(screen_width // 2 - 180, screen_height // 2, 170, 70)
room_join_button = pygame.Rect(screen_width // 2 + 10, screen_height // 2, 170, 70)
back_button_rect = pygame.Rect(20, 20, 140, 50)
connect_button_rect = pygame.Rect(screen_width - 140, screen_height - 70, 120, 50)
ready_button_rect = connect_button_rect

def render_text_with_outline(text, font, text_color, outline_color):
    base = font.render(text, True, text_color)
    outline = pygame.Surface((base.get_width() + 4, base.get_height() + 4), pygame.SRCALPHA)
    for dx in [-2, 0, 2]:
        for dy in [-2, 0, 2]:
            if dx != 0 or dy != 0:
                outline.blit(font.render(text, True, outline_color), (dx + 2, dy + 2))
    outline.blit(base, (2, 2))
    return outline

def draw_button(rect, text, font, bg_color, text_color, border_color=(255,255,255), radius=12):
    pygame.draw.rect(screen, bg_color, rect, border_radius=radius)
    pygame.draw.rect(screen, border_color, rect, 2, border_radius=radius)
    label = font.render(text, True, text_color)
    screen.blit(label, (
        rect.x + (rect.width - label.get_width()) // 2,
        rect.y + (rect.height - label.get_height()) // 2
    ))

def start_server_thread():
    global server_ready
    print("[DEBUG] サーバースレッド開始")
    network.start_server()
    print("[DEBUG] サーバー起動完了（接続待機中）")
    server_ready = True

def connect_to_server(ip):
    global client_ready
    ip = ip.strip()  # 余計な空白を除去
    print(f"[DEBUG] クライアント接続先IP: {ip}")
    network.connect_to_server(ip)
    if network.connected:
        client_ready = True

def connect_client_thread(ip):
    connect_to_server(ip)

def draw_ip_input_field(screen, input_text, cursor_pos):
    screen.blit(font_common.render("アドレス:", True, WHITE), (screen_width // 2 - 200, input_y))
    text_surface = font_common.render(input_text, True, WHITE)
    screen.blit(text_surface, (input_x, input_y))
    cursor_x = input_x + font_common.size(input_text[:cursor_pos])[0]
    pygame.draw.line(screen, WHITE, (cursor_x, input_y), (cursor_x, input_y + font_common.get_height()), 2)

def get_cursor_pos_from_mouse(x, text, start_x):
    for i in range(len(text) + 1):
        if start_x + font_common.size(text[:i])[0] > x:
            return i
    return len(text)

running = True
while running:
    screen.blit(background_image, (0, 0))
    now = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 戻るボタン処理
            if back_button_rect.collidepoint(event.pos) and state != "title":
                # 状態により戻る先を変更
                if state == "room_menu":
                    state = "title"
                elif state in ["ip_display", "ip_input", "waiting", "username", "select_difficulty", "rule_selection", "waiting_for_host_rule"]:
                    state = "room_menu"
                server_ready = False
                client_ready = False
                server_button_pressed = False
                input_text = ""
                cursor_pos = 0
                username = ""
                difficulty = None

            # 各画面でのボタン処理
            if state == "title":
                if start_button_rect.collidepoint(event.pos):
                    state = "room_menu"

            elif state == "room_menu":
                if room_create_button.collidepoint(event.pos):
                    role = "server"
                    ip_address = network.get_my_ip()
                    state = "ip_display"
                elif room_join_button.collidepoint(event.pos):
                    role = "client"
                    input_text = ""
                    cursor_pos = 0
                    state = "ip_input"

            elif state == "select_difficulty":
                for key, rect in difficulty_buttons.items():
                    if rect.collidepoint(event.pos):
                        difficulty = key
                if ready_button.collidepoint(event.pos) and difficulty:
                    print(f"[DEBUG] 難易度選択完了: {difficulty}")
                    # 難易度決定後の処理（例：ゲーム開始やルール画面へ遷移）
                    # state = "rule_selection"  # 必要に応じて変更

            elif state == "ip_display" and role == "server":
                if ready_button_rect.collidepoint(event.pos) and not server_ready and not server_button_pressed:
                    print("[DEBUG] サーバー準備OKボタン押下")
                    server_button_pressed = True
                    server_thread = threading.Thread(target=start_server_thread, daemon=True)
                    server_thread.start()

            elif state == "ip_input":
                if connect_button_rect.collidepoint(event.pos):
                    trimmed_ip = input_text.strip()
                    if trimmed_ip:
                        state = "waiting"
                        client_thread = threading.Thread(target=connect_client_thread, args=(trimmed_ip,), daemon=True)
                        client_thread.start()
                else:
                    mx, my = event.pos
                    if input_y <= my <= input_y + font_common.get_height():
                        cursor_pos = get_cursor_pos_from_mouse(mx, input_text, input_x)

        elif event.type == pygame.KEYDOWN:
            if state == "ip_input":
                if event.key == pygame.K_BACKSPACE:
                    backspace_pressed = True
                    backspace_timer = now
                    if cursor_pos > 0:
                        input_text = input_text[:cursor_pos - 1] + input_text[cursor_pos:]
                        cursor_pos -= 1
                elif event.key == pygame.K_LEFT and cursor_pos > 0:
                    cursor_pos -= 1
                elif event.key == pygame.K_RIGHT and cursor_pos < len(input_text):
                    cursor_pos += 1
                elif event.key == pygame.K_RETURN:
                    trimmed_ip = input_text.strip()
                    if trimmed_ip:
                        state = "waiting"
                        client_thread = threading.Thread(target=connect_client_thread, args=(trimmed_ip,), daemon=True)
                        client_thread.start()
                elif event.unicode.isprintable() and len(input_text) < 15:
                    input_text = input_text[:cursor_pos] + event.unicode + input_text[cursor_pos:]
                    cursor_pos += 1

            elif event.type == pygame.KEYUP and event.key == pygame.K_BACKSPACE:
                backspace_pressed = False

            elif state == "username":
                if event.key == pygame.K_RETURN:
                    if len(username.strip()) > 0:
                        print(f"[DEBUG] ユーザー名設定: {username}")
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
                    if len(username) < 12:
                        username += event.unicode

            elif state == "rule_selection":
                if event.key == pygame.K_ESCAPE:
                    state = "username"

        elif event.type == pygame.KEYUP and event.key == pygame.K_BACKSPACE:
            backspace_pressed = False

    # バックスペース長押し処理（IP入力画面）
    if state == "ip_input" and backspace_pressed:
        if now - backspace_timer > 300:
            if cursor_pos > 0:
                input_text = input_text[:cursor_pos - 1] + input_text[cursor_pos:]
                cursor_pos -= 1
            backspace_timer = now - 200

    # ネットワーク接続状態によるステート遷移
    if role == "server" and state == "ip_display" and getattr(network, "server_waiting", False):
        server_ready = True

    if role == "client" and state == "waiting" and network.connected:
        client_ready = True

    if state in ["ip_display", "waiting", "ip_input"]:
        if role == "server" and server_ready:
            print("[DEBUG] サーバー接続完了 → ユーザー名入力画面へ")
            state = "username"
        elif role == "client" and client_ready:
            print("[DEBUG] クライアント接続完了 → ユーザー名入力画面へ")
            state = "username"

    # 画面描画
    if state == "title":
        title_surf = render_text_with_outline("コード・サルダテ", font_title, WHITE, GRAY)
        screen.blit(title_surf, (screen_width // 2 - title_surf.get_width() // 2, 150))
        subtitle = "〜置いていいのは、置かれる覚悟があるマスだけだ〜"
        subtitle_surf = render_text_with_outline(subtitle, font_subtitle, WHITE, GRAY)
        screen.blit(subtitle_surf, (screen_width // 2 - subtitle_surf.get_width() // 2, 220))
        draw_button(start_button_rect, "スタート", font_button, RED, WHITE)

    elif state == "room_menu":
        title = font_common.render("ルーム作成画面", True, WHITE)
        screen.blit(title, (screen_width // 2 - title.get_width() // 2, screen_height // 2 - 100))
        draw_button(room_create_button, "ルームを作成", font_common, DARK_GRAY, WHITE)
        draw_button(room_join_button, "ルームに入る", font_common, DARK_GRAY, WHITE)
        draw_button(back_button_rect, "← 戻る", font_common, DARK_GRAY, WHITE)

    elif state == "ip_display":
        label = font_common.render("ルーム作成画面", True, WHITE)
        screen.blit(label, (screen_width // 2 - label.get_width() // 2, 150))
        addr_label = font_common.render("アドレス:", True, WHITE)
        addr_label_x = screen_width // 2 - 200
        addr_label_y = screen_height // 2
        screen.blit(addr_label, (addr_label_x, addr_label_y))
        ip_text = font_common.render(ip_address, True, WHITE)
        screen.blit(ip_text, (addr_label_x + addr_label.get_width() + 40, addr_label_y))
        info = font_common.render("あなたのIPアドレスはこちらです。", True, WHITE)
        screen.blit(info, (screen_width // 2 - info.get_width() // 2, screen_height // 2 + 50))
        if not server_ready:
            label_text = "接続待機中..." if server_button_pressed else "準備OK"
            draw_button(ready_button_rect, label_text, font_common, DARK_GRAY, WHITE)
        else:
            ready_text = font_common.render("準備完了！", True, YELLOW)
            screen.blit(ready_text, (
                ready_button_rect.x + (ready_button_rect.width - ready_text.get_width()) // 2,
                ready_button_rect.y + (ready_button_rect.height - ready_text.get_height()) // 2
            ))
        draw_button(back_button_rect, "← 戻る", font_common, DARK_GRAY, WHITE)

    elif state == "ip_input":
        label = font_common.render("IPアドレス入力画面", True, WHITE)
        screen.blit(label, (screen_width // 2 - label.get_width() // 2, 150))
        draw_ip_input_field(screen, input_text, cursor_pos)
        draw_button(connect_button_rect, "接続", font_common, DARK_GRAY, WHITE)
        draw_button(back_button_rect, "← 戻る", font_common, DARK_GRAY, WHITE)

    elif state == "waiting":
        text = font_common.render("接続中...", True, YELLOW)
        screen.blit(text, (screen_width // 2 - text.get_width() // 2, screen_height // 2))
        draw_button(back_button_rect, "← 戻る", font_common, DARK_GRAY, WHITE)

    elif state == "username":
        title_text = font_common.render("ユーザー情報設定", True, WHITE)
        screen.blit(title_text, (screen_width // 2 - title_text.get_width() // 2, screen_height // 2 - 200))

        name_label = font_common.render("ユーザーネーム:", True, WHITE)
        screen.blit(name_label, (screen_width // 2 - 200, screen_height // 2 - 40))

        name_input_rect = pygame.Rect(screen_width // 2 - 50, screen_height // 2 - 45, 200, 35)
        pygame.draw.rect(screen, DARK_GRAY, name_input_rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, name_input_rect, 2, border_radius=8)

        name_surface = font_common.render(username, True, WHITE)
        screen.blit(name_surface, (name_input_rect.x + 10, name_input_rect.y + (name_input_rect.height - name_surface.get_height()) // 2))

        # 点滅カーソル
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = name_input_rect.x + 10 + font_common.size(username)[0]
            pygame.draw.line(screen, WHITE, (cursor_x, name_input_rect.y + 5), (cursor_x, name_input_rect.y + name_input_rect.height - 5), 2)

        # 決定ボタン（ユーザーネームがあるときのみ）
        if len(username.strip()) > 0:
            decide_button_rect = pygame.Rect(screen_width // 2 - 75, screen_height // 2 + 50, 150, 50)
            pygame.draw.rect(screen, RED, decide_button_rect, border_radius=12)
            pygame.draw.rect(screen, WHITE, decide_button_rect, 2, border_radius=12)
            decide_text = font_common.render("決定", True, WHITE)
            screen.blit(decide_text, (decide_button_rect.centerx - decide_text.get_width() // 2,
                                     decide_button_rect.centery - decide_text.get_height() // 2))

        instruction = font_common.render("Enterキーで決定 / Escキーで戻る", True, GRAY)
        screen.blit(instruction, (screen_width // 2 - instruction.get_width() // 2, screen_height // 2 + 120))
        draw_button(back_button_rect, "← 戻る", font_common, DARK_GRAY, WHITE)

    elif state == "select_difficulty":
        title_surf = render_text_with_outline("難易度選択", font_title, SOFT_WHITE_BLUE, DEEP_BLUE_GRAY)
        screen.blit(title_surf, (screen_width // 2 - title_surf.get_width() // 2, 150))

        for key, rect in difficulty_buttons.items():
            color = {"3x3": (0, 200, 0), "5x5": (230, 230, 0), "3x3x3": (200, 0, 0)}[key]
            pygame.draw.rect(screen, color, rect, border_radius=12)

            if difficulty == key:
                pygame.draw.rect(screen, WHITE, rect, 4, border_radius=12)

            label = font_button.render(key, True, (0, 0, 0))
            screen.blit(label, (rect.x + (rect.width - label.get_width()) // 2, rect.y + 10))

            desc = font_common.render(difficulty_descriptions[key], True, WHITE)
            screen.blit(desc, (rect.x + 10, rect.y + 40))

        # 準備完了ボタン
        ready_color = (0, 180, 180) if difficulty else DARK_GRAY
        pygame.draw.rect(screen, ready_color, ready_button, border_radius=12)
        ready_label = font_button.render("準備完了", True, WHITE)
        screen.blit(ready_label, (ready_button.x + (ready_button.width - ready_label.get_width()) // 2,
                                  ready_button.y + (ready_button.height - ready_label.get_height()) // 2))

        draw_button(back_button_rect, "← 戻る", font_common, DARK_GRAY, WHITE)

    elif state == "waiting_for_host_rule":
        text = font_common.render("ホストの難易度選択を待機中...", True, YELLOW)
        screen.blit(text, (screen_width // 2 - text.get_width() // 2, screen_height // 2))
        draw_button(back_button_rect, "← 戻る", font_common, DARK_GRAY, WHITE)

    pygame.display.flip()
    pygame.time.Clock().tick(30)

pygame.quit()
sys.exit()
