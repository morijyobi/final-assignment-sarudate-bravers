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
state = "title"  # title, select_role, input_ip, waiting, username
role = None
ip_address = ""
input_text = ""
username = ""

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
        text = font_common.render("接続完了！ユーザー名入力画面（仮）", True, (0, 255, 0))
        screen.blit(text, (screen_width // 2 - text.get_width() // 2, screen_height // 2))

    pygame.display.flip()

pygame.quit()
sys.exit()
