import tkinter as tk
import pygame
import threading
import sys
from tkinter import ttk
from network import Network # network.pyは別途用意済みと仮定
import threexthree  # 3x3ゲームモジュールをインポート
import fivexfive
import math  # ←★これ追加！
import random

pygame.init()
pygame.mixer.init()  # ←★音楽機能を初期化
screen_info = pygame.display.Info()
screen_width, screen_height = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("コード・サルダテ")


try:
    background_image = pygame.image.load("./D-T9JlqUYAEo7q5.png")
    background_image = pygame.transform.scale(background_image, (screen_width, screen_height))
    print("[DEBUG] 背景画像を正常に読み込みました")
except (pygame.error, FileNotFoundError) as e:
    print(f"[DEBUG] 背景画像が見つかりません: {e}")
    background_image = pygame.Surface((screen_width, screen_height))
    background_image.fill((20, 20, 20))  # 暗い灰色の背景
    
# 背景画像の読み込み
try:
    start_background = pygame.image.load("lelouch.png")
    start_background = pygame.transform.scale(start_background, (screen_width, screen_height))
except pygame.error:
    print("[DEBUG] lelouch.png が見つかりません。黒い背景を使用します。")
    start_background = pygame.Surface((screen_width, screen_height))
    start_background.fill((0, 0, 0))

try:
    game_background = pygame.image.load("D-T9JlqUYAEo7q5.png")
    game_background = pygame.transform.scale(game_background, (screen_width, screen_height))
except pygame.error:
    print("[DEBUG] D-T9JlqUYAEo7q5.png が見つかりません。スタート背景を使用します。")
    game_background = start_background

# 現在の背景画像（初期はスタート画面の背景）
current_background = start_background

# BGM設定
try:
    # BGMファイルを読み込み（mp3, wav, oggなどに対応）
    pygame.mixer.music.load("bgm.mp3")  # BGMファイルのパスを指定
    pygame.mixer.music.set_volume(0.3)  # 音量設定（0.0-1.0）
    pygame.mixer.music.play(-1)  # -1でループ再生
    print("[DEBUG] BGM再生開始")
except (pygame.error, FileNotFoundError):
    print("[DEBUG] BGMファイルが見つかりません。BGMなしで継続します。")
except Exception as e:
    print(f"[DEBUG] BGM読み込みエラー: {e}")

# BGM関連変数
bgm_volume = 0.3  # 初期音量
bgm_enabled = True  # BGMのオン/オフ


font_title = pygame.font.SysFont("meiryo", 48)
font_subtitle = pygame.font.SysFont("meiryo", 24)
font_button = pygame.font.SysFont("meiryo", 36)
font_common = pygame.font.SysFont("meiryo", 28)
# 絵文字専用フォントを追加（複数フォントでフォールバック）
font_emoji = None
emoji_fonts = ["segoeuiemoji", "notocoloremoji", "twemoji", "applesymbol", "applecoloremoji"]
for font_name in emoji_fonts:
    try:
        font_emoji = pygame.font.SysFont(font_name, 48)
        print(f"[DEBUG] 絵文字フォント '{font_name}' を使用します")
        break
    except:
        continue

if font_emoji is None:
    print("[DEBUG] 絵文字フォントが見つかりません。通常フォントを使用します")
    font_emoji = font_common

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

def process_network_messages():
    global opponent_username, opponent_icon_index, opponent_title_index, opponent_ready, state, turn_decided, my_turn, turn_announcement_timer, running, difficulty, role, username, selected_icon_index, selected_title_index, pending_info_response
    msg = network.receive()
    if msg:
        print(f"[DEBUG] 受信メッセージ: {msg}")
        if msg.startswith("INFO:"):
            parts = msg.split(":")
            if len(parts) >= 5:  # 新しい形式: INFO:name:icon:title:difficulty
                _, name, icon_idx, title_idx, diff = parts
                opponent_username = name
                opponent_icon_index = int(icon_idx)
                opponent_title_index = int(title_idx)
                difficulty = diff  # クライアント側でも難易度を設定
                print(f"[DEBUG] 相手情報更新（難易度付き）: {opponent_username}, {opponent_icon_index}, {opponent_title_index}, {difficulty}")
            else:  # 古い形式との互換性
                _, name, icon_idx, title_idx = parts
                opponent_username = name
                opponent_icon_index = int(icon_idx)
                opponent_title_index = int(title_idx)
                print(f"[DEBUG] 相手情報更新: {opponent_username}, {opponent_icon_index}, {opponent_title_index}")
            
            # サーバー側が難易度選択中にクライアントのINFOを受信した場合の処理
            if state == "select_difficulty" and role == "server":
                if difficulty:
                    # 既に難易度選択済みの場合、即座に応答
                    print("[DEBUG] サーバー側: クライアントのINFO受信、応答を送信")
                    info_response = f"INFO:{username}:{selected_icon_index}:{selected_title_index}:{difficulty}"
                    network.send(info_response)
                else:
                    # 難易度未選択の場合、応答待機フラグを設定
                    print("[DEBUG] サーバー側: クライアントのINFO受信、難易度選択後に応答予定")
                    pending_info_response = True
            
            if state == "waiting_for_host_rule":
                state = "preparation"
                print("[DEBUG] クライアント側: preparation に遷移")
        elif msg == "READY":
            opponent_ready = True
            print("[DEBUG] 相手がREADYになった！")
        elif msg == "CANCEL_READY":
            opponent_ready = False
            print("[DEBUG] 相手がREADYキャンセル！")
        elif msg.startswith("TURN:"):
            # 相手から先行後攻情報を受信
            _, opponent_turn_str = msg.split(":")
            opponent_turn = opponent_turn_str == "True"
            my_turn = not opponent_turn  # 相手の逆が自分
            turn_decided = True
            turn_announcement_timer = pygame.time.get_ticks()
            print(f"[DEBUG] 相手から先行後攻受信: 自分={'先行（○）' if my_turn else '後攻（×）'}")
        elif msg == "GAME_START":
            # 相手からゲーム開始メッセージを受信
            print("[DEBUG] 相手からGAME_STARTメッセージを受信")
            if difficulty == "3x3":
                print("[DEBUG] 3x3ゲームを開始します")
                # プレイヤー情報を準備
                my_info = (username, pulldown_icon[selected_icon_index], pulldown_title[selected_title_index])
                opponent_info = (opponent_username, pulldown_icon[opponent_icon_index], pulldown_title[opponent_title_index])
                
                # threexthree.pyのゲームを初期化して開始
                threexthree.init_game(my_info, opponent_info, my_turn, network)
                
                # メインループを終了してthreexthree.pyのメインループに移行
                running = False
                # threexthree.pyのメインループを実行
                threexthree.main()
                # threexthree.pyが終了したらプログラム全体を終了
                pygame.quit()
                sys.exit()
                
        elif difficulty == "5x5":
            network.send("GAME_START")
            my_info = (username, pulldown_icon[selected_icon_index], pulldown_title[selected_title_index])
            opponent_info = (opponent_username, pulldown_icon[opponent_icon_index], pulldown_title[opponent_title_index])

            fivexfive.init_game(my_info, opponent_info, my_turn, network)
            running = False
            fivexfive.main()
            pygame.quit()
            sys.exit()
            

# 準備確認用
my_ready = False
opponent_ready = False
opponent_username = ""
opponent_icon_index = None
opponent_title_index = None
opponent_info_received = False  # 相手のINFO受信済みかどうか
pending_info_response = False  # サーバー側でクライアントINFO受信済み、応答待機中

# 先行後攻決定用
turn_decided = False  # 先行後攻が決定済みか
my_turn = None  # True: 自分が先行（○）, False: 自分が後攻（×）
turn_announcement_timer = 0  # 先行後攻発表のタイマー


effect_timer = 0
effect_type = None  # "spark", "thunder", "fire"
shake_offset = [0, 0]

pulldown_icon = ["😎", "😊", "🐱", "🐶", "🍀", "🌸", "😃"]
pulldown_title = ["第98代唯一皇帝", "第11皇子", "修羅" ,"失楽園"]

icon_dropdown_open = False
title_dropdown_open = False
selected_icon_index = 0
selected_title_index = 0

difficulty_buttons = {
    "3x3": pygame.Rect(screen_width // 2 - 340, screen_height // 2 - 60, 220, 80),
    "5x5": pygame.Rect(screen_width // 2 - 110, screen_height // 2 - 60, 220, 80),
    "3x3x3": pygame.Rect(screen_width // 2 + 120, screen_height // 2 - 60, 220, 80),
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
# 相手のユーザー情報
opponent_username = ""
opponent_icon_index = None
opponent_title_index = None


start_button_rect = pygame.Rect(screen_width // 2 - 120, screen_height - 180, 240, 80)
room_create_button = pygame.Rect(screen_width // 2 - 220, screen_height // 2, 200, 90)
room_join_button = pygame.Rect(screen_width // 2 + 30, screen_height // 2, 200, 90)
back_button_rect = pygame.Rect(20, 20, 160, 80)
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

def draw_effect(effect_type, center_x, center_y):
    if effect_type == "spark":
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.randint(10, 60)
            end_x = center_x + math.cos(angle) * dist
            end_y = center_y + math.sin(angle) * dist
            pygame.draw.line(screen, (0, 255, 0), (center_x, center_y), (end_x, end_y), 2)
    elif effect_type == "thunder":
        for _ in range(3):
            start = (center_x + random.randint(-30, 30), center_y - 40)
            end = (center_x + random.randint(-30, 30), center_y + 40)
            pygame.draw.line(screen, (255, 255, 0), start, end, 4)
    elif effect_type == "fire":
        for _ in range(30):
            x = center_x + random.randint(-40, 40)
            y = center_y + random.randint(-40, 40)
            radius = random.randint(3, 6)
            pygame.draw.circle(screen, (255, random.randint(50, 100), 0), (x, y), radius)

running = True
while running:

    process_network_messages()
    # screen.blit(background_image, (0, 0))

    # マウス位置取得
    mouse_pos = pygame.mouse.get_pos()
    
    # タイトル画面でのスタートボタンホバー効果
    if state == "title":
        if start_button_rect.collidepoint(mouse_pos):
            current_background = game_background  # ホバー時は D-T9JlqUYAEo7q5.png
        else:
            current_background = start_background  # 通常時は lelouch.png
    
    # 揺れ効果の処理

    shake_offset = [0, 0]
    if effect_timer > 0 and pygame.time.get_ticks() - effect_timer < 500:
        shake_offset = [random.randint(-5, 5), random.randint(-5, 5)]
    else:
        effect_timer = 0
        effect_type = None

    # 現在の背景を描画（揺れ効果込み）
    screen.blit(current_background, (shake_offset[0], shake_offset[1]))
    now = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            print("現在のstate:", state)
            
            if state == "preparation":
                if my_ready_button.collidepoint(event.pos):
                    if not my_ready:
                        network.send("READY")
                        my_ready = True
                        print("[DEBUG] 自分がREADYになった")
                    else:
                        network.send("CANCEL_READY")
                        my_ready = False
                        print("[DEBUG] 自分がREADYキャンセルした")
            
            
            
            if state == "username":
                if len(username.strip()) > 0 and decide_button_rect.collidepoint(event.pos):
                    if role == "server":
                        state = "select_difficulty"
                    else:
                        state = "waiting_for_host_rule"
                                # アイコンドロップダウン開閉・選択
                                
                if icon_box.collidepoint(event.pos):
                    icon_dropdown_open = not icon_dropdown_open
                    title_dropdown_open = False  # 称号が開いていたら閉じる
                elif icon_dropdown_open:
                    for i in range(len(pulldown_icon)):
                        item_rect = pygame.Rect(icon_box.x, icon_box.y + 50 * (i + 1), icon_box.width, 50)  # 高さを50に変更
                        if item_rect.collidepoint(event.pos):
                            selected_icon_index = i
                            icon_dropdown_open = False
                            break

                # 称号ドロップダウン開閉・選択
                if title_box.collidepoint(event.pos):
                    title_dropdown_open = not title_dropdown_open
                    icon_dropdown_open = False  # アイコンが開いていたら閉じる
                elif title_dropdown_open:
                    for i in range(len(pulldown_title)):
                        item_rect = pygame.Rect(title_box.x, title_box.y + 50 * (i + 1), title_box.width, 50)  # 高さを50に変更
                        if item_rect.collidepoint(event.pos):
                            selected_title_index = i
                            title_dropdown_open = False
                            break


            # 戻るボタン処理
            if back_button_rect.collidepoint(event.pos) and state != "title":
                # 状態により戻る先を変更
                if state == "room_menu":
                    state = "title"

                elif state in ["ip_display", "ip_input", "waiting", "username", "rule_selection", "select_difficulty", "waiting_for_host_rule", "preparation"]:
                    state = "room_menu"
                    
                    # ★ 接続リセット処理を追加
                    if network.connected:
                        print("[DEBUG] 接続をリセットします")
                        network.disconnect()
                    server_ready = False
                    client_ready = False
                    server_button_pressed = False
                    both_connected = False
                    input_text = ""
                    cursor_pos = 0
                    username = ""
                    difficulty = None
                    
                    # 先行後攻状態をリセット
                    turn_decided = False
                    my_turn = None
                    turn_announcement_timer = 0
                    input_text = ""
                    cursor_pos = 0
                    username = ""
                    difficulty = None

                elif state in ["ip_display", "ip_input", "waiting", "username", "rule_selection"]:
                    state = "room_menu"
                elif state in ["select_difficulty", "waiting_for_host_rule"]:
                    state = "username"
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
                    current_background = game_background  # クリック後は D-T9JlqUYAEo7q5.png を維持
                    state = "room_menu"


            elif state == "room_menu":
                if room_create_button.collidepoint(event.pos):
                    role = "server"
                    ip_address = network.get_my_ip()
                    state = "ip_display"
                    # サーバー関連フラグをリセット
                    server_ready = False
                    server_button_pressed = False
                    # ネットワーク接続をリセット
                    if network.connected:
                        network.disconnect()
                elif room_join_button.collidepoint(event.pos):
                    role = "client"
                    input_text = ""
                    cursor_pos = 0
                    state = "ip_input"
                    # クライアント関連フラグをリセット
                    client_ready = False
                    # ネットワーク接続をリセット
                    if network.connected:
                        network.disconnect()

            
            elif state == "select_difficulty":
                for key, rect in difficulty_buttons.items():
                    if rect.collidepoint(event.pos):
                        difficulty = key
                        
                        # エフェクト種類を設定
                        if key == "3x3":
                            effect_type = "spark"
                        elif key == "5x5":
                            effect_type = "thunder"
                        elif key == "3x3x3":
                            effect_type = "fire"
                        effect_timer = pygame.time.get_ticks()

                # 準備完了ボタンが押されたとき
                if ready_button.collidepoint(event.pos) and difficulty:
                    print(f"[DEBUG] 難易度選択完了: {difficulty}")
                    
                    
                    # 自分と相手の準備状態をリセット
                    my_ready = False
                    opponent_ready = False
                    
                    # 先行後攻状態をリセット
                    turn_decided = False
                    my_turn = None
                    turn_announcement_timer = 0
                    
                    import time
                    time.sleep(0.3)  # ★ 追加！
                    
                    info_message = f"INFO:{username}:{selected_icon_index}:{selected_title_index}:{difficulty}"
                    network.send(info_message)
                    
                    # 待機中のクライアント応答があれば送信
                    if pending_info_response:
                        print("[DEBUG] サーバー側: 待機中だったクライアント応答を送信")
                        pending_info_response = False

                    # 画面遷移と初期化
                    state = "preparation"
                    my_ready = False
                    opponent_ready = False


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
            print(f"[DEBUG] キー押下: {event.key}, 名前: {pygame.key.name(event.key)}")
            
            # BGM音量調整（全画面共通）- 日本語キーボード対応版
            keys = pygame.key.get_pressed()
            
            # +キーの検出（複数パターン対応）
            plus_pressed = (
                event.key == pygame.K_EQUALS or  # =キー
                event.key == pygame.K_KP_PLUS or  # テンキーの+
                (event.key == pygame.K_SEMICOLON and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])) or  # Shift + ;
                (event.key == pygame.K_EQUALS and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]))  # Shift + =
            )
            
            # -キーの検出（複数パターン対応）
            minus_pressed = (
                event.key == pygame.K_MINUS or  # -キー
                event.key == pygame.K_KP_MINUS or  # テンキーの-
                (event.key == pygame.K_MINUS and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]))  # Shift + -
            )
            
            if plus_pressed:
                print("[DEBUG] +キーが押されました")
                if bgm_volume < 1.0:
                    bgm_volume = min(1.0, bgm_volume + 0.1)
                    pygame.mixer.music.set_volume(bgm_volume)
                    print(f"[DEBUG] BGM音量アップ: {bgm_volume:.1f}")
            elif minus_pressed:
                print("[DEBUG] -キーが押されました")
                if bgm_volume > 0.0:
                    bgm_volume = max(0.0, bgm_volume - 0.1)
                    pygame.mixer.music.set_volume(bgm_volume)
                    print(f"[DEBUG] BGM音量ダウン: {bgm_volume:.1f}")
            elif event.key == pygame.K_m:
                print("[DEBUG] Mキーが押されました")
                bgm_enabled = not bgm_enabled
                if bgm_enabled:
                    pygame.mixer.music.set_volume(bgm_volume)
                    print("[DEBUG] BGMオン")
                else:
                    pygame.mixer.music.set_volume(0)
                    print("[DEBUG] BGMオフ")
            
            # 各状態での個別キー処理
            elif state == "ip_input":
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
                    print(f"[DEBUG] Enterキー押下: IPアドレス='{trimmed_ip}'")
                    if trimmed_ip:
                        print("[DEBUG] Enterキー: 接続処理開始")
                        state = "waiting"
                        client_thread = threading.Thread(target=connect_client_thread, args=(trimmed_ip,), daemon=True)
                        client_thread.start()
                    else:
                        print("[DEBUG] Enterキー: IPアドレスが空のため接続せず")
                elif event.unicode.isprintable() and len(input_text) < 15:
                    input_text = input_text[:cursor_pos] + event.unicode + input_text[cursor_pos:]
                    cursor_pos += 1

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

            elif state == "ip_display":
                # ルーム作成画面でEnterキーを押すと準備OKボタンを押したことになる
                if event.key == pygame.K_RETURN and role == "server" and not server_ready and not server_button_pressed:
                    print("[DEBUG] Enterキー: サーバー準備OKボタン押下")
                    server_button_pressed = True
                    server_thread = threading.Thread(target=start_server_thread, daemon=True)
                    server_thread.start()

            elif state == "preparation":
                # 準備完了画面でEnterキーを押すとREADYボタンを押したことになる
                if event.key == pygame.K_RETURN:
                    if not my_ready:
                        network.send("READY")
                        my_ready = True
                        print("[DEBUG] Enterキー: 自分がREADYになった")
                    else:
                        network.send("CANCEL_READY")
                        my_ready = False
                        print("[DEBUG] Enterキー: 自分がREADYキャンセルした")

            elif state == "select_difficulty":
                # 難易度選択画面でEnterキーを押すと準備完了ボタンを押したことになる
                if event.key == pygame.K_RETURN and difficulty:
                    print(f"[DEBUG] Enterキー: 難易度選択完了 {difficulty}")
                    
                    # 自分と相手の準備状態をリセット
                    my_ready = False
                    opponent_ready = False
                    
                    # 先行後攻状態をリセット
                    turn_decided = False
                    my_turn = None
                    turn_announcement_timer = 0
                    
                    import time
                    time.sleep(0.3)
                    
                    info_message = f"INFO:{username}:{selected_icon_index}:{selected_title_index}:{difficulty}"
                    network.send(info_message)
                    
                    # 待機中のクライアント応答があれば送信
                    if pending_info_response:
                        print("[DEBUG] サーバー側: 待機中だったクライアント応答を送信（Enter）")
                        pending_info_response = False

                    # 画面遷移と初期化
                    state = "preparation"
                    my_ready = False
                    opponent_ready = False

            elif state == "rule_selection":
                if event.key == pygame.K_ESCAPE:
                    state = "username"

        elif event.type == pygame.KEYUP and event.key == pygame.K_BACKSPACE:
            backspace_pressed = False

        elif event.type == pygame.KEYUP and event.key == pygame.K_BACKSPACE:
            backspace_pressed = False
            
    if state == "preparation":
        if my_ready and opponent_ready and not turn_decided:
            # 先行後攻をランダムで決定
            my_turn = random.choice([True, False])  # True: 先行（○）, False: 後攻（×）
            turn_decided = True
            turn_announcement_timer = pygame.time.get_ticks()
            
            # ネットワークで先行後攻情報を送信
            turn_message = f"TURN:{my_turn}"
            network.send(turn_message)
            
            print(f"[DEBUG] 先行後攻決定: 自分={'先行（○）' if my_turn else '後攻（×）'}")
        
        # 3秒後にゲーム画面へ遷移
        if turn_decided and pygame.time.get_ticks() - turn_announcement_timer > 3000:
            print("[DEBUG] 先行後攻決定完了 → 3x3ゲーム開始")
            
            # 選択された難易度が3x3の場合のみthreexthree.pyを呼び出し
            if difficulty == "3x3":
                # 相手にゲーム開始メッセージを送信
                network.send("GAME_START")
                print("[DEBUG] 相手にGAME_STARTメッセージを送信")
                
                # プレイヤー情報を準備
                my_info = (username, pulldown_icon[selected_icon_index], pulldown_title[selected_title_index])
                opponent_info = (opponent_username, pulldown_icon[opponent_icon_index], pulldown_title[opponent_title_index])
                
                # threexthree.pyのゲームを初期化して開始
                threexthree.init_game(my_info, opponent_info, my_turn, network)
                
                # メインループを終了してthreexthree.pyのメインループに移行
                running = False
                # threexthree.pyのメインループを実行
                threexthree.main()
                # threexthree.pyが終了したらプログラム全体を終了
                pygame.quit()
                sys.exit()
            else:
                # 他の難易度の場合は従来通り
                state = "game"
                
            if difficulty == "5x5":
                # 相手にゲーム開始メッセージを送信
                network.send("GAME_START")
                print("[DEBUG] 相手にGAME_STARTメッセージを送信")
                
                # プレイヤー情報を準備
                my_info = (username, pulldown_icon[selected_icon_index], pulldown_title[selected_title_index])
                opponent_info = (opponent_username, pulldown_icon[opponent_icon_index], pulldown_title[opponent_title_index])
                
                # threexthree.pyのゲームを初期化して開始
                fivexfive.init_game(my_info, opponent_info, my_turn, network)
                
                # メインループを終了してthreexthree.pyのメインループに移行
                running = False
                # threexthree.pyのメインループを実行
                fivexfive.main()
                # threexthree.pyが終了したらプログラム全体を終了
                pygame.quit()
                sys.exit()
            else:
                # 他の難易度の場合は従来通り
                state = "game"

    # バックスペース長押し処理（IP入力画面）
    if state == "ip_input" and backspace_pressed:
        if now - backspace_timer > 300:
            if cursor_pos > 0:
                input_text = input_text[:cursor_pos - 1] + input_text[cursor_pos:]
                cursor_pos -= 1
            backspace_timer = now - 200

    # ネットワーク接続状態によるステート遷移

    if role == "server" and state == "ip_display" and server_ready and network.connected:
        both_connected = True
    elif role == "client" and state == "waiting" and client_ready and network.connected:
        both_connected = True

    if role == "server" and state == "ip_display" and getattr(network, "server_waiting", False) and server_button_pressed:
        server_ready = True


    if role == "client" and state == "waiting" and network.connected:
        client_ready = True

    if state in ["ip_display", "waiting", "ip_input"]:
        if role == "server" and server_ready and network.connected:
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
        label = font_common.render("ルーム入室画面", True, WHITE)
        screen.blit(label, (screen_width // 2 - label.get_width() // 2, 150))
        draw_ip_input_field(screen, input_text, cursor_pos)
        draw_button(connect_button_rect, "接続", font_common, DARK_GRAY, WHITE)
        draw_button(back_button_rect, "← 戻る", font_common, DARK_GRAY, WHITE)

    elif state == "waiting":
        text = font_common.render("接続中...", True, YELLOW)
        screen.blit(text, (screen_width // 2 - text.get_width() // 2, screen_height // 2))
        draw_button(back_button_rect, "← 戻る", font_common, DARK_GRAY, WHITE)

    elif state == "username":
        # タイトル描画
        title_text = font_common.render("ユーザー情報設定", True, WHITE)
        screen.blit(title_text, (screen_width // 2 - title_text.get_width() // 2, screen_height // 2 - 200))

        # ユーザーネームラベル描画位置
        label_x = screen_width // 2 - 200
        label_y = screen_height // 2 - 60
        name_label = font_common.render("ユーザーネーム:", True, WHITE)
        screen.blit(name_label, (label_x, label_y))

        # ラベルの右隣にテキスト入力枠配置
        label_width = name_label.get_width()
        input_x = label_x + label_width + 10  # ラベル右端＋10pxスペース
        input_y = label_y + 1  # ラベル高さに合わせて微調整

        name_input_rect = pygame.Rect(input_x, input_y, 275, 35)
        pygame.draw.rect(screen, DARK_GRAY, name_input_rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, name_input_rect, 2, border_radius=8)

        # 入力中のユーザーネーム表示
        name_surface = font_common.render(username, True, WHITE)
        screen.blit(name_surface, (name_input_rect.x + 10, name_input_rect.y + (name_input_rect.height - name_surface.get_height()) // 2))

        # 点滅カーソル表示
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = name_input_rect.x + 10 + font_common.size(username)[0]
            pygame.draw.line(screen, WHITE, (cursor_x, name_input_rect.y + 5), (cursor_x, name_input_rect.y + name_input_rect.height - 5), 2)

        # ユーザーネーム入力済みなら決定ボタン表示
        if len(username.strip()) > 0:
            decide_button_rect = pygame.Rect(screen_width // 2 - 75, screen_height // 2 + 120, 150, 50)
            pygame.draw.rect(screen, RED, decide_button_rect, border_radius=12)
            pygame.draw.rect(screen, WHITE, decide_button_rect, 2, border_radius=12)
            decide_text = font_common.render("決定", True, WHITE)
            screen.blit(decide_text, (decide_button_rect.centerx - decide_text.get_width() // 2,
                                    decide_button_rect.centery - decide_text.get_height() // 2))

        # 戻るボタン表示
        draw_button(back_button_rect, "← 戻る", font_common, DARK_GRAY, WHITE)
        
        # ▼ アイコン・称号プルダウンメニュー ▼
        # アイコンボックスを絵文字用に大きく調整
        icon_box = pygame.Rect(screen_width // 2 - 180, input_y + 80, 160, 50)  # 幅120→160、高さ40→50に拡大
        title_box = pygame.Rect(screen_width // 2 + 30, input_y + 80, 220, 50)  # 高さを50に統一

        # ボックス背景と枠線
        pygame.draw.rect(screen, DARK_GRAY, icon_box, border_radius=8)
        pygame.draw.rect(screen, WHITE, icon_box, 2, border_radius=8)
        pygame.draw.rect(screen, DARK_GRAY, title_box, border_radius=8)
        pygame.draw.rect(screen, WHITE, title_box, 2, border_radius=8)

        # 現在の選択肢表示
        try:
            # アイコンボックス用に少し小さめの絵文字フォントを使用
            icon_font_small = pygame.font.SysFont("segoeuiemoji", 32)  # 48→32に縮小
            icon_label = icon_font_small.render(pulldown_icon[selected_icon_index], True, YELLOW)
        except:
            icon_label = font_common.render(pulldown_icon[selected_icon_index], True, WHITE)
        screen.blit(icon_label, (icon_box.centerx - icon_label.get_width() // 2, icon_box.y + (icon_box.height - icon_label.get_height()) // 2))
        title_label = font_common.render(pulldown_title[selected_title_index], True, WHITE)
        screen.blit(title_label, (title_box.centerx - title_label.get_width() // 2, title_box.y + (title_box.height - title_label.get_height()) // 2))

        # ドロップダウンリスト展開（アイコン）
        if icon_dropdown_open:
            for i, item in enumerate(pulldown_icon):
                item_rect = pygame.Rect(icon_box.x, icon_box.y + 50 * (i + 1), icon_box.width, 50)  # 高さ40→50に拡大
                bg_color = (70, 130, 200) if i == selected_icon_index else DARK_GRAY  # 選択中なら青背景
                pygame.draw.rect(screen, bg_color, item_rect, border_radius=8)
                pygame.draw.rect(screen, WHITE, item_rect, 1, border_radius=8)
                try:
                    item_label = icon_font_small.render(item, True, YELLOW)
                except:
                    item_label = font_common.render(item, True, WHITE)
                screen.blit(item_label, (item_rect.centerx - item_label.get_width() // 2, item_rect.y + (item_rect.height - item_label.get_height()) // 2))


        # ドロップダウンリスト展開（称号）
        if title_dropdown_open:
            for i, item in enumerate(pulldown_title):
                item_rect = pygame.Rect(title_box.x, title_box.y + 50 * (i + 1), title_box.width, 50)  # 高さを50に統一
                bg_color = (70, 130, 200) if i == selected_title_index else DARK_GRAY  # 選択中なら青背景
                pygame.draw.rect(screen, bg_color, item_rect, border_radius=8)
                pygame.draw.rect(screen, WHITE, item_rect, 1, border_radius=8)
                item_label = font_common.render(item, True, WHITE)
                screen.blit(item_label, (item_rect.centerx - item_label.get_width() // 2, item_rect.y + (item_rect.height - item_label.get_height()) // 2))


    elif state == "select_difficulty":
        title_surf = render_text_with_outline("難易度選択", font_title, SOFT_WHITE_BLUE, DEEP_BLUE_GRAY)
        screen.blit(title_surf, (screen_width // 2 - title_surf.get_width() // 2, 150))

        for key, rect in difficulty_buttons.items():
            color = {"3x3": (0, 200, 0), "5x5": (230, 230, 0), "3x3x3": (200, 0, 0)}[key]
            pygame.draw.rect(screen, color, rect, border_radius=12)

            if difficulty == key:
                pygame.draw.rect(screen, WHITE, rect, 4, border_radius=12)

            label = font_button.render(key, True, (0, 0, 0))
            screen.blit(label, (rect.x + (rect.width - label.get_width()) // 2, rect.y + 15))

                # 選択された説明文を画面下に表示
            if difficulty:
                desc = font_common.render(difficulty_descriptions[difficulty], True, WHITE)
                screen.blit(desc, (
                    screen_width // 2 - desc.get_width() // 2,
                    ready_button.y - 60  # ← ここに注目
                ))
                if effect_type:
                    center = difficulty_buttons[difficulty].center
                    draw_effect(effect_type, center[0], center[1])

                # 準備完了ボタン
            ready_color = (0, 180, 180) if difficulty else DARK_GRAY
            pygame.draw.rect(screen, ready_color, ready_button, border_radius=12)
            ready_label = font_button.render("準備完了", True, WHITE)
            screen.blit(ready_label, (ready_button.x + (ready_button.width - ready_label.get_width()) // 2,
                                    ready_button.y + (ready_button.height - ready_label.get_height()) // 2))

            draw_button(back_button_rect, "← 戻る", font_common, DARK_GRAY, WHITE)

        
    elif state == "preparation":
                # printを先頭に入れて、このブロックが呼ばれているか確認する
        
                screen.blit(background_image, (0, 0))
                y_base = screen_height // 3
                left_x = screen_width // 4
                right_x = screen_width * 3 // 4

                # 自分の情報表示
                name_surface = font_common.render(username, True, WHITE)
                
                if name_surface is None:
                    print("⚠️ name_surfaceがNoneです！")
                else:
                    screen.blit(name_surface, (left_x - name_surface.get_width() // 2, y_base))
                    
                screen.blit(name_surface, (left_x - name_surface.get_width() // 2, y_base))
                try:
                    # 準備画面でも小さめの絵文字フォントを使用
                    icon_font_small = pygame.font.SysFont("segoeuiemoji", 32)
                    icon_surface = icon_font_small.render(pulldown_icon[selected_icon_index], True, YELLOW)
                except:
                    icon_surface = font_common.render(pulldown_icon[selected_icon_index], True, WHITE)
                screen.blit(icon_surface, (left_x - icon_surface.get_width() // 2, y_base + 40))
                title_surface = font_common.render(pulldown_title[selected_title_index], True, WHITE)
                screen.blit(title_surface, (left_x - title_surface.get_width() // 2, y_base + 80))

                # 自分のREADYボタン
                my_ready_button = pygame.Rect(left_x - 70, y_base + 140, 140, 50)
                ready_color = (0, 180, 0) if my_ready else DARK_GRAY
                pygame.draw.rect(screen, ready_color, my_ready_button, border_radius=12)
                label = font_common.render("READY", True, WHITE)
                screen.blit(label, (my_ready_button.centerx - label.get_width() // 2,
                                    my_ready_button.centery - label.get_height() // 2))

                # 相手の情報
                opp_name = opponent_username if opponent_username else "???"
                opp_icon = pulldown_icon[opponent_icon_index] if opponent_icon_index is not None else "?"
                opp_title = pulldown_title[opponent_title_index] if opponent_title_index is not None else "???"
                opp_name_surface = font_common.render(opp_name, True, WHITE)
                screen.blit(opp_name_surface, (right_x - opp_name_surface.get_width() // 2, y_base))
                try:
                    # 相手のアイコンも小さめのフォントを使用
                    opp_icon_surface = icon_font_small.render(opp_icon, True, YELLOW)
                except:
                    opp_icon_surface = font_common.render(opp_icon, True, WHITE)
                screen.blit(opp_icon_surface, (right_x - opp_icon_surface.get_width() // 2, y_base + 40))
                opp_title_surface = font_common.render(opp_title, True, WHITE)
                screen.blit(opp_title_surface, (right_x - opp_title_surface.get_width() // 2, y_base + 80))

                # 相手のREADY状態表示
                opp_status = "READY" if opponent_ready else "WAITING..."
                opp_color = (0, 255, 0) if opponent_ready else GRAY
                opp_status_surf = font_common.render(opp_status, True, opp_color)
                screen.blit(opp_status_surf, (right_x - opp_status_surf.get_width() // 2, y_base + 150))

                # 中央に「VS」または先行後攻発表
                if turn_decided:
                    # 先行後攻が決定済みの場合、発表を表示
                    my_role = "先行（○）" if my_turn else "後攻（×）"
                    opponent_role = "後攻（×）" if my_turn else "先行（○）"
                    
                    # 自分の役割を左側に表示
                    my_role_surf = font_common.render(my_role, True, YELLOW)
                    screen.blit(my_role_surf, (left_x - my_role_surf.get_width() // 2, y_base + 200))
                    
                    # 相手の役割を右側に表示
                    opp_role_surf = font_common.render(opponent_role, True, YELLOW)
                    screen.blit(opp_role_surf, (right_x - opp_role_surf.get_width() // 2, y_base + 200))
                    
                    # 中央に「先行後攻決定！」
                    announcement_surf = font_title.render("先行後攻決定！", True, RED)
                    screen.blit(announcement_surf, (screen_width // 2 - announcement_surf.get_width() // 2, screen_height // 2 - 30))
                    
                    # カウントダウン表示
                    remaining_time = max(0, 3 - (pygame.time.get_ticks() - turn_announcement_timer) // 1000)
                    countdown_surf = font_common.render(f"ゲーム開始まであと {remaining_time} 秒", True, WHITE)
                    screen.blit(countdown_surf, (screen_width // 2 - countdown_surf.get_width() // 2, screen_height // 2 + 50))
                else:
                    # まだ決定していない場合、従来のVS表示
                    vs_surf = font_title.render("VS", True, RED)
                    screen.blit(vs_surf, (screen_width // 2 - vs_surf.get_width() // 2, screen_height // 2 - 30))
                # 戻るボタン
                draw_button(back_button_rect, "← 戻る", font_common, DARK_GRAY, WHITE)

    elif state == "waiting_for_host_rule":
        # まだ送ってなければ
        if not hasattr(network, "info_sent"):
            info_message = f"INFO:{username}:{selected_icon_index}:{selected_title_index}"
            network.send(info_message)
            print("[DEBUG] クライアント → INFOメッセージ送信:", info_message)
            network.info_sent = True

        # メッセージ受信処理はメインのprocess_network_messages()関数で処理される
        print(f"[DEBUG] waiting_for_host_rule状態: opponent_username={opponent_username}, difficulty={difficulty}")

        # --- 画面描画 ---
        text = font_common.render("ホストの難易度選択を待機中...", True, YELLOW)
        screen.blit(text, (screen_width // 2 - text.get_width() // 2, screen_height // 2))
        draw_button(back_button_rect, "← 戻る", font_common, DARK_GRAY, WHITE)

    # BGM情報表示（全画面共通）
    bgm_info = f"BGM: {'ON' if bgm_enabled else 'OFF'} | 音量: {int(bgm_volume * 100)}%"
    bgm_text = pygame.font.SysFont("meiryo", 16).render(bgm_info, True, (200, 200, 200))
    screen.blit(bgm_text, (10, screen_height - 30))
    
    # BGM操作説明
    control_info = "+/-: 音量調整 | M: ミュート切替"
    control_text = pygame.font.SysFont("meiryo", 14).render(control_info, True, (150, 150, 150))
    screen.blit(control_text, (10, screen_height - 50))

    pygame.display.flip()
    pygame.time.Clock().tick(30)

pygame.quit()
sys.exit()