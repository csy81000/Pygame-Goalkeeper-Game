"""Pygame으로 만든 골키퍼 미니게임.

프로젝트 폴더를 어디에 두더라도 실행할 수 있도록 모든 리소스 경로는
이 파일의 위치를 기준으로 계산한다.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pygame


SCREEN_SIZE = (900, 600)
FPS = 60

PROJECT_DIR = Path(__file__).resolve().parent
ASSET_DIR = PROJECT_DIR / "assets"
DATA_DIR = PROJECT_DIR / "data"
SELECTION_FILE = DATA_DIR / "selection.json"
RANKING_FILE = DATA_DIR / "ranking.tsv"

DEFAULT_SELECTION = {
    "stadium": "stadium1.png",
    "ball": "ball1.png",
    "glove": "gloves1.png",
}

ITEM_OPTIONS = {
    "stadium": ["stadium1.png", "stadium2.png", "stadium3.png"],
    "ball": ["ball1.png", "ball2.png", "ball3.png"],
    "glove": ["gloves1.png", "gloves2-1.png", "gloves3.png"],
}

WHITE = (255, 255, 255)
BLACK = (25, 25, 25)
LIGHT_GRAY = (225, 225, 225)
GREEN = (30, 180, 80)
RED = (210, 60, 60)
BLUE = (65, 135, 220)


def asset_path(filename: str) -> Path:
    """등록된 에셋 이름을 안전한 절대 경로로 변환한다."""

    allowed_assets = {name for names in ITEM_OPTIONS.values() for name in names}
    allowed_assets.update(
        {
            "gloves2.png",
            "kicker1.png",
            "kicker2.png",
            "stadium1-1.png",
            "stadium2-1.png",
            "stadium3-1.png",
        }
    )
    if filename not in allowed_assets:
        raise ValueError(f"알 수 없는 에셋입니다: {filename}")
    return ASSET_DIR / filename


def load_selection() -> dict[str, str]:
    selection = DEFAULT_SELECTION.copy()
    if not SELECTION_FILE.exists():
        return selection

    try:
        saved = json.loads(SELECTION_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return selection

    for category, options in ITEM_OPTIONS.items():
        if saved.get(category) in options:
            selection[category] = saved[category]
    return selection


def save_selection(selection: dict[str, str]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    SELECTION_FILE.write_text(
        json.dumps(selection, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_ranking(limit: int = 10) -> list[tuple[str, int]]:
    if not RANKING_FILE.exists():
        return []

    ranking: list[tuple[str, int]] = []
    for line in RANKING_FILE.read_text(encoding="utf-8").splitlines():
        try:
            name, score_text = line.rsplit("\t", maxsplit=1)
            ranking.append((name, int(score_text)))
        except (ValueError, TypeError):
            continue
    return sorted(ranking, key=lambda item: item[1], reverse=True)[:limit]


def save_score(name: str, score: int) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    safe_name = name.replace("\t", " ").replace("\n", " ").strip() or "player"
    with RANKING_FILE.open("a", encoding="utf-8") as ranking_file:
        ranking_file.write(f"{safe_name}\t{score}\n")


class GoalkeeperGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Goalkeeper Game")
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.SysFont(None, 72)
        self.heading_font = pygame.font.SysFont(None, 44)
        self.button_font = pygame.font.SysFont(None, 34)
        self.text_font = pygame.font.SysFont(None, 28)
        self.running = True
        self.selection = load_selection()

    def run(self) -> None:
        while self.running:
            action = self.show_main_menu()
            if action == "start":
                username = self.ask_username()
                if username and self.running:
                    score = self.play(username)
                    if score is not None and self.running:
                        save_score(username, score)
                        self.show_game_over(username, score)
            elif action == "items":
                self.show_item_menu()
            elif action == "ranking":
                self.show_ranking()
            elif action == "exit":
                self.running = False

        pygame.mouse.set_visible(True)
        pygame.quit()

    def draw_button(
        self,
        rect: pygame.Rect,
        label: str,
        *,
        color: tuple[int, int, int] = LIGHT_GRAY,
        text_color: tuple[int, int, int] = BLACK,
    ) -> None:
        if rect.collidepoint(pygame.mouse.get_pos()):
            color = tuple(max(0, channel - 20) for channel in color)
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        text = self.button_font.render(label, True, text_color)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def handle_window_close(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            self.running = False
            return True
        return False

    def show_main_menu(self) -> str:
        buttons = {
            "start": pygame.Rect(350, 210, 200, 55),
            "items": pygame.Rect(350, 300, 200, 55),
            "ranking": pygame.Rect(350, 390, 200, 55),
            "exit": pygame.Rect(350, 480, 200, 55),
        }

        while self.running:
            self.screen.fill(WHITE)
            title = self.title_font.render("Goalkeeper Game", True, BLACK)
            self.screen.blit(title, title.get_rect(center=(450, 105)))

            for action, rect in buttons.items():
                self.draw_button(rect, action.title())

            for event in pygame.event.get():
                if self.handle_window_close(event):
                    return "exit"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for action, rect in buttons.items():
                        if rect.collidepoint(event.pos):
                            return action

            pygame.display.flip()
            self.clock.tick(FPS)
        return "exit"

    def ask_username(self) -> str | None:
        input_box = pygame.Rect(300, 255, 300, 55)
        back_button = pygame.Rect(365, 470, 170, 50)
        username = ""
        active = True

        while self.running:
            for event in pygame.event.get():
                if self.handle_window_close(event):
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    if event.key == pygame.K_RETURN and username.strip():
                        return username.strip()
                    if not active:
                        continue
                    if event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    elif event.unicode.isprintable() and len(username) < 18:
                        username += event.unicode
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    active = input_box.collidepoint(event.pos)
                    if back_button.collidepoint(event.pos):
                        return None

            self.screen.fill(WHITE)
            heading = self.heading_font.render("Enter your name", True, BLACK)
            self.screen.blit(heading, heading.get_rect(center=(450, 150)))
            color = BLUE if active else (150, 150, 150)
            pygame.draw.rect(self.screen, color, input_box, width=3, border_radius=6)
            shown_text = username or "Player name"
            shown_color = BLACK if username else (160, 160, 160)
            text = self.button_font.render(shown_text, True, shown_color)
            self.screen.blit(text, (input_box.x + 12, input_box.y + 12))
            self.draw_button(back_button, "Back")

            pygame.display.flip()
            self.clock.tick(FPS)
        return None

    def show_item_menu(self) -> None:
        thumbnails = {
            "stadium": [
                pygame.image.load(asset_path(f"stadium{index}-1.png")).convert_alpha()
                for index in range(1, 4)
            ],
            "ball": [
                pygame.transform.smoothscale(
                    pygame.image.load(asset_path(f"ball{index}.png")).convert_alpha(),
                    (80, 80),
                )
                for index in range(1, 4)
            ],
            "glove": [
                pygame.transform.smoothscale(
                    pygame.image.load(
                        asset_path("gloves2.png" if index == 2 else f"gloves{index}.png")
                    ).convert_alpha(),
                    (120, 100),
                )
                for index in range(1, 4)
            ],
        }
        positions = {
            "stadium": [(200, 80), (425, 80), (650, 80)],
            "ball": [(260, 270), (450, 270), (640, 270)],
            "glove": [(240, 410), (440, 410), (640, 410)],
        }
        labels = {"stadium": "Stadium", "ball": "Ball", "glove": "Glove"}
        back_button = pygame.Rect(365, 540, 170, 45)

        while self.running:
            self.screen.fill(WHITE)
            heading = self.heading_font.render("Choose items", True, BLACK)
            self.screen.blit(heading, heading.get_rect(center=(450, 35)))

            option_rects: dict[tuple[str, int], pygame.Rect] = {}
            for category, images in thumbnails.items():
                label_y = positions[category][0][1] + images[0].get_height() // 2
                label = self.text_font.render(labels[category], True, BLACK)
                self.screen.blit(label, (70, label_y - label.get_height() // 2))
                for index, (image, position) in enumerate(zip(images, positions[category])):
                    rect = image.get_rect(center=position)
                    option_rects[(category, index)] = rect
                    self.screen.blit(image, rect)
                    if self.selection[category] == ITEM_OPTIONS[category][index]:
                        pygame.draw.rect(self.screen, GREEN, rect.inflate(12, 12), 4, 6)

            self.draw_button(back_button, "Back")

            for event in pygame.event.get():
                if self.handle_window_close(event):
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if back_button.collidepoint(event.pos):
                        return
                    for (category, index), rect in option_rects.items():
                        if rect.collidepoint(event.pos):
                            self.selection[category] = ITEM_OPTIONS[category][index]
                            save_selection(self.selection)

            pygame.display.flip()
            self.clock.tick(FPS)

    def show_ranking(self) -> None:
        back_button = pygame.Rect(365, 530, 170, 50)

        while self.running:
            self.screen.fill(WHITE)
            heading = self.heading_font.render("Top 10 Ranking", True, BLACK)
            self.screen.blit(heading, heading.get_rect(center=(450, 55)))

            ranking = load_ranking()
            if not ranking:
                empty = self.text_font.render("No scores yet. Play the first game!", True, BLACK)
                self.screen.blit(empty, empty.get_rect(center=(450, 250)))
            for index, (name, score) in enumerate(ranking, start=1):
                line = self.button_font.render(
                    f"{index:>2}. {name:<18} {score:>3} points", True, BLACK
                )
                self.screen.blit(line, (245, 85 + index * 38))

            self.draw_button(back_button, "Back")
            for event in pygame.event.get():
                if self.handle_window_close(event):
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return
                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and back_button.collidepoint(event.pos)
                ):
                    return

            pygame.display.flip()
            self.clock.tick(FPS)

    def play(self, username: str) -> int | None:
        background = pygame.image.load(
            asset_path(self.selection["stadium"])
        ).convert()
        ball_image = pygame.image.load(asset_path(self.selection["ball"])).convert_alpha()
        glove_image = pygame.image.load(asset_path(self.selection["glove"])).convert_alpha()
        kicker_images = [
            pygame.transform.smoothscale(
                pygame.image.load(asset_path(filename)).convert_alpha(), (85, 170)
            )
            for filename in ("kicker1.png", "kicker2.png")
        ]

        goal_rect = pygame.Rect(90, 130, 715, 450)
        start_position = pygame.Vector2(450, 315)
        score = 0
        saves = 4 if self.selection["glove"] == "gloves3.png" else 3
        phase = "kick"
        phase_started = pygame.time.get_ticks()
        ball_position = start_position.copy()
        ball_size = 30.0
        ball_angle = 0.0
        direction = pygame.Vector2(1, 0)
        exit_button = pygame.Rect(805, 10, 80, 32)

        def begin_shot() -> None:
            nonlocal phase, phase_started, ball_position, ball_size, direction
            target = pygame.Vector2(
                random.randint(goal_rect.left + 35, goal_rect.right - 35),
                random.randint(goal_rect.top + 35, goal_rect.bottom - 35),
            )
            direction = (target - start_position).normalize()
            ball_position = start_position.copy()
            ball_size = 30.0
            phase = "kick"
            phase_started = pygame.time.get_ticks()

        begin_shot()
        pygame.mouse.set_visible(False)

        while self.running and saves > 0:
            dt = self.clock.tick(FPS) / 1000.0
            now = pygame.time.get_ticks()
            mouse_position = pygame.Vector2(pygame.mouse.get_pos())

            for event in pygame.event.get():
                if self.handle_window_close(event):
                    pygame.mouse.set_visible(True)
                    return None
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.mouse.set_visible(True)
                    return score
                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and exit_button.collidepoint(event.pos)
                ):
                    pygame.mouse.set_visible(True)
                    return score

            if score >= 10:
                level, speed = "hard", 330.0
            elif score >= 5:
                level, speed = "normal", 275.0
            else:
                level, speed = "easy", 225.0
            if self.selection["glove"] == "gloves1.png":
                speed -= 35.0

            if phase == "kick" and now - phase_started >= 650:
                phase = "flying"
                phase_started = now
            elif phase == "flying":
                ball_position += direction * speed * dt
                ball_size = min(75.0, ball_size + 36.0 * dt)
                ball_angle += 260.0 * dt * (1 if direction.x * direction.y < 0 else -1)

                catch_padding = 70 if self.selection["glove"] == "gloves2-1.png" else 35
                if (
                    ball_size >= 68
                    and goal_rect.collidepoint(mouse_position)
                    and ball_position.distance_to(mouse_position) <= catch_padding
                ):
                    score += 1
                    phase = "saved"
                    phase_started = now
                elif not goal_rect.inflate(90, 90).collidepoint(ball_position):
                    saves -= 1
                    phase = "missed"
                    phase_started = now
            elif phase in {"saved", "missed"} and now - phase_started >= 650:
                begin_shot()

            self.screen.blit(background, (0, 0))
            self.draw_goal(goal_rect)

            if phase == "kick":
                kicker_index = 0 if now - phase_started < 325 else 1
                kicker_rect = kicker_images[kicker_index].get_rect(center=start_position)
                self.screen.blit(kicker_images[kicker_index], kicker_rect)
            else:
                resized_ball = pygame.transform.smoothscale(
                    ball_image, (int(ball_size), int(ball_size))
                )
                rotated_ball = pygame.transform.rotate(resized_ball, ball_angle)
                self.screen.blit(rotated_ball, rotated_ball.get_rect(center=ball_position))

            self.draw_scoreboard(username, score, level, saves, exit_button)
            if phase == "saved":
                self.draw_center_message("SAVED!", GREEN)
            elif phase == "missed":
                self.draw_center_message("MISS", RED)

            mouse_inside_goal = goal_rect.collidepoint(mouse_position)
            pygame.mouse.set_visible(not mouse_inside_goal)
            if mouse_inside_goal:
                glove_rect = glove_image.get_rect(center=mouse_position)
                self.screen.blit(glove_image, glove_rect)

            pygame.display.flip()

        pygame.mouse.set_visible(True)
        return score

    def draw_goal(self, goal_rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, WHITE, goal_rect, width=8)
        for x in range(goal_rect.left + 25, goal_rect.right, 25):
            pygame.draw.line(
                self.screen, (225, 225, 225), (x, goal_rect.top), (x, goal_rect.bottom), 1
            )
        for y in range(goal_rect.top + 25, goal_rect.bottom, 25):
            pygame.draw.line(
                self.screen, (225, 225, 225), (goal_rect.left, y), (goal_rect.right, y), 1
            )

    def draw_scoreboard(
        self,
        username: str,
        score: int,
        level: str,
        saves: int,
        exit_button: pygame.Rect,
    ) -> None:
        frame = pygame.Surface((900, 52))
        frame.fill(LIGHT_GRAY)
        self.screen.blit(frame, (0, 0))
        labels = [
            (f"Player: {username[:12]}", 12),
            (f"Score: {score}", 285),
            (f"Level: {level}", 435),
            (f"Lives: {saves}", 625),
        ]
        for label, x in labels:
            self.screen.blit(self.text_font.render(label, True, BLACK), (x, 15))
        pygame.draw.rect(self.screen, RED, exit_button, border_radius=5)
        exit_text = self.text_font.render("Exit", True, WHITE)
        self.screen.blit(exit_text, exit_text.get_rect(center=exit_button.center))

    def draw_center_message(self, message: str, color: tuple[int, int, int]) -> None:
        text = self.heading_font.render(message, True, color)
        panel = text.get_rect(center=(450, 105)).inflate(28, 15)
        pygame.draw.rect(self.screen, WHITE, panel, border_radius=8)
        self.screen.blit(text, text.get_rect(center=panel.center))

    def show_game_over(self, username: str, score: int) -> None:
        back_button = pygame.Rect(365, 470, 170, 50)
        while self.running:
            self.screen.fill(WHITE)
            heading = self.title_font.render("Game Over", True, BLACK)
            self.screen.blit(heading, heading.get_rect(center=(450, 115)))
            player_text = self.heading_font.render(f"Player: {username}", True, BLACK)
            score_text = self.heading_font.render(f"Score: {score}", True, BLACK)
            self.screen.blit(player_text, player_text.get_rect(center=(450, 230)))
            self.screen.blit(score_text, score_text.get_rect(center=(450, 295)))
            self.draw_button(back_button, "Main menu")

            for event in pygame.event.get():
                if self.handle_window_close(event):
                    return
                if event.type == pygame.KEYDOWN and event.key in {
                    pygame.K_ESCAPE,
                    pygame.K_RETURN,
                }:
                    return
                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and back_button.collidepoint(event.pos)
                ):
                    return

            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    GoalkeeperGame().run()
