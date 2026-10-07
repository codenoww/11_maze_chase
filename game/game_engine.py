import random
import pygame
from game.maze import generate_maze, CELL
from game.entities import Player, Enemy

COLS, ROWS = 13, 11
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + 50
FPS = 60
HUD_TEXT = "Reach EXIT before the enemy catches you!  R=Restart"
FREEZE_FRAMES = 300
PELLET_RADIUS = 8

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze Chase")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 22)
        self.big_font = pygame.font.SysFont("monospace", 38, bold=True)
        # HUD font: shrink until the text fits the window width
        size = 22
        self.hud_font = pygame.font.SysFont("monospace", size)
        while size > 8 and self.hud_font.size(HUD_TEXT)[0] > WIDTH - 16:
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
        hud=pygame.Rect(0,ROWS*CELL,WIDTH,50)
        pygame.draw.rect(self.screen,(30,30,50),hud)
        info=self.hud_font.render(HUD_TEXT,True,(200,200,200))
        self.screen.blit(info,(8,ROWS*CELL+(50-info.get_height())//2))
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
        sub=self.font.render("Press R to Restart",True,(200,200,200))
        self.screen.blit(msg,(WIDTH//2-msg.get_width()//2,ROWS*CELL//2-30))
        self.screen.blit(sub,(WIDTH//2-sub.get_width()//2,ROWS*CELL//2+20))

    def run(self):
        running=True
        while running:
            running=self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()