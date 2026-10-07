import random
import pygame
from game.maze import generate_maze, CELL
from game.entities import Player, Enemy

COLS, ROWS = 13, 11
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + 50
FPS = 60
HUD_H = 50
HUD_TEXT = "Reach EXIT before the enemy catches you!  R=Restart"
HUD_STATS_WORST = "Speed: 9   Survived: 99999s"  # widest stats line, used for font fitting
FREEZE_FRAMES = 300
PELLET_RADIUS = 8

# difficulty ramp
BASE_INTERVAL = 20
MIN_INTERVAL = 5
RAMP_STEP = 2
RAMP_MS = 15000
MAX_REDUCTIONS = (BASE_INTERVAL - MIN_INTERVAL + RAMP_STEP - 1) // RAMP_STEP  # 8 -> tier 9

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze Chase")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 22)
        self.big_font = pygame.font.SysFont("monospace", 38, bold=True)
        # HUD font: shrink until both lines fit the window width and the bar height
        size = 22
        self.hud_font = pygame.font.SysFont("monospace", size)
        while size > 8 and (
            self.hud_font.size(HUD_TEXT)[0] > WIDTH - 16
            or self.hud_font.size(HUD_STATS_WORST)[0] > WIDTH - 16
            or self.hud_font.get_height() * 2 > HUD_H - 6
        ):
            size -= 1
            self.hud_font = pygame.font.SysFont("monospace", size)
        self.reset()

    def reset(self):
        self.walls = generate_maze(COLS, ROWS)
        self.player = Player(0, 0)
        self.enemies = [
            Enemy(ROWS-1, COLS-1),
            Enemy(0, COLS-1),
            Enemy(ROWS-1, 0),
        ]
        self.exit_rect = pygame.Rect((COLS//2)*CELL+5, (ROWS//2)*CELL+5, CELL-10, CELL-10)
        self.caught = False
        self.won = False
        self.freeze_timer = 0
        self.pellet_rect = self._spawn_pellet()
        # difficulty ramp + score
        self.start_ticks = pygame.time.get_ticks()
        self.speed_tier = 1
        self.score = 0
        for e in self.enemies:
            e.move_interval = BASE_INTERVAL

    def _spawn_pellet(self):
        # any cell except the player start, the enemy starts, and the exit
        blocked = {(self.player.r, self.player.c), (ROWS//2, COLS//2)}
        blocked |= {(e.r, e.c) for e in self.enemies}
        cells = [(r, c) for r in range(ROWS) for c in range(COLS) if (r, c) not in blocked]
        r, c = random.choice(cells)
        cx, cy = c*CELL + CELL//2, r*CELL + CELL//2
        return pygame.Rect(cx-PELLET_RADIUS, cy-PELLET_RADIUS, PELLET_RADIUS*2, PELLET_RADIUS*2)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: self.reset()
        return True

    def update(self):
        if self.caught or self.won: return

        # survival score: +1 per frame while alive
        self.score += 1

        # difficulty ramp: every RAMP_MS, enemies move RAMP_STEP frames faster (min MIN_INTERVAL)
        elapsed = pygame.time.get_ticks() - self.start_ticks
        reductions = min(elapsed // RAMP_MS, MAX_REDUCTIONS)
        interval = max(MIN_INTERVAL, BASE_INTERVAL - RAMP_STEP * reductions)
        self.speed_tier = 1 + reductions
        for e in self.enemies:
            e.move_interval = interval

        keys = pygame.key.get_pressed()
        self.player.move(keys, self.walls, ROWS, COLS)

        # power pellet pickup: freeze every enemy for FREEZE_FRAMES
        if self.pellet_rect and self.player.rect.colliderect(self.pellet_rect):
            self.pellet_rect = None
            self.freeze_timer = FREEZE_FRAMES
            for e in self.enemies:
                e.frozen = True

        # freeze countdown, then unfreeze
        if self.freeze_timer > 0:
            self.freeze_timer -= 1
            if self.freeze_timer == 0:
                for e in self.enemies:
                    e.frozen = False

        for enemy in self.enemies:
            enemy.update(self.walls, self.player, ROWS, COLS)
        if any(self.player.rect.colliderect(e.rect) for e in self.enemies):
            self.caught = True
        if self.player.rect.colliderect(self.exit_rect):
            self.won = True

    def draw(self):
        self.screen.fill((230, 220, 210))
        wc=(50,40,60)
        for r in range(ROWS):
            for c in range(COLS):
                x,y=c*CELL,r*CELL
                w=self.walls[r][c]
                if w[0]: pygame.draw.line(self.screen,wc,(x,y),(x+CELL,y),3)
                if w[1]: pygame.draw.line(self.screen,wc,(x,y+CELL),(x+CELL,y+CELL),3)
                if w[2]: pygame.draw.line(self.screen,wc,(x+CELL,y),(x+CELL,y+CELL),3)
                if w[3]: pygame.draw.line(self.screen,wc,(x,y),(x,y+CELL),3)
        pygame.draw.rect(self.screen,(80,200,80),self.exit_rect,border_radius=4)
        lbl=self.font.render("EXIT",True,(20,80,20))
        self.screen.blit(lbl,(self.exit_rect.x+2,self.exit_rect.y+6))
        if self.pellet_rect:
            pygame.draw.circle(self.screen, (255, 220, 40), self.pellet_rect.center, PELLET_RADIUS)
            pygame.draw.circle(self.screen, (180, 140, 0), self.pellet_rect.center, PELLET_RADIUS, 2)
        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # HUD: line 1 = instructions, line 2 = speed tier + survival time
        hud=pygame.Rect(0,ROWS*CELL,WIDTH,HUD_H)
        pygame.draw.rect(self.screen,(30,30,50),hud)
        line_h = self.hud_font.get_height()
        top = ROWS*CELL + (HUD_H - 2*line_h)//2
        info=self.hud_font.render(HUD_TEXT,True,(200,200,200))
        self.screen.blit(info,(8,top))
        stats_text = f"Speed: {self.speed_tier}   Survived: {self.score // 60}s"
        stats=self.hud_font.render(stats_text,True,(255,220,120))
        self.screen.blit(stats,(8,top+line_h))

        if self.caught:
            self._overlay("CAUGHT!", (220,60,60))
        if self.won:
            self._overlay("ESCAPED!", (80,220,80))
        pygame.display.flip()

    def _overlay(self, text, color):
        surf=pygame.Surface((WIDTH,ROWS*CELL),pygame.SRCALPHA)
        surf.fill((0,0,0,140))
        self.screen.blit(surf,(0,0))
        msg=self.big_font.render(text,True,color)
        score_txt=self.font.render(f"Score: {self.score}  ({self.score // 60}s survived)",True,(255,220,120))
        sub=self.font.render("Press R to Restart",True,(200,200,200))
        self.screen.blit(msg,(WIDTH//2-msg.get_width()//2,ROWS*CELL//2-40))
        self.screen.blit(score_txt,(WIDTH//2-score_txt.get_width()//2,ROWS*CELL//2+10))
        self.screen.blit(sub,(WIDTH//2-sub.get_width()//2,ROWS*CELL//2+40))

    def run(self):
        running=True
        while running:
            running=self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()