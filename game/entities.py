import pygame
from game.maze import CELL

SPEED = 2
WALL_T = 4  # collision thickness of a wall line (drawn at 3px)

class Player:
    def __init__(self, r, c):
        self.r, self.c = r, c
        cx, cy = c*CELL+CELL//2, r*CELL+CELL//2
        self.rect = pygame.Rect(cx-10, cy-10, 20, 20)
        self.color = (60, 120, 220)

    def move(self, keys, walls, rows, cols):
        dx=dy=0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx=-SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx=SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy=-SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy=SPEED
        nr = self.rect.move(dx,0)
        if self._valid(nr, walls, rows, cols): self.rect=nr
        nr = self.rect.move(0,dy)
        if self._valid(nr, walls, rows, cols): self.rect=nr

    def _valid(self, rect, walls, rows, cols):
        # stay inside the grid
        for px,py in [(rect.left,rect.top),(rect.right-1,rect.top),(rect.left,rect.bottom-1),(rect.right-1,rect.bottom-1)]:
            cr,cc=py//CELL,px//CELL
            if not(0<=cr<rows and 0<=cc<cols): return False
        # collide with the wall segments of every cell the rect touches (+1 cell margin)
        r0 = max(0, rect.top//CELL - 1)
        r1 = min(rows-1, rect.bottom//CELL + 1)
        c0 = max(0, rect.left//CELL - 1)
        c1 = min(cols-1, rect.right//CELL + 1)
        h = WALL_T // 2
        for r in range(r0, r1+1):
            for c in range(c0, c1+1):
                top, bottom, right, left = walls[r][c]
                x, y = c*CELL, r*CELL
                if top and rect.colliderect(pygame.Rect(x-h, y-h, CELL+WALL_T, WALL_T)): return False
                if bottom and rect.colliderect(pygame.Rect(x-h, y+CELL-h, CELL+WALL_T, WALL_T)): return False
                if left and rect.colliderect(pygame.Rect(x-h, y-h, WALL_T, CELL+WALL_T)): return False
                if right and rect.colliderect(pygame.Rect(x+CELL-h, y-h, WALL_T, CELL+WALL_T)): return False
        return True

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, self.rect)

class Enemy:
    def __init__(self, r, c):
        self.r, self.c = r, c
        cx, cy = c*CELL+CELL//2, r*CELL+CELL//2
        self.rect = pygame.Rect(cx-12, cy-12, 24, 24)
        self.color = (220, 60, 60)
        self.frozen_color = (110, 160, 255)
        self.frozen = False
        self.timer = 0
        self.move_interval = 20  # frames between cell moves

    def update(self, walls, player, rows, cols):
        if self.frozen:
            return
        from game.maze import bfs
        self.timer += 1
        if self.timer >= self.move_interval:
            self.timer = 0
            pr, pc = player.rect.centery//CELL, player.rect.centerx//CELL
            step = bfs(walls, (self.r, self.c), (pr, pc), rows, cols)
            if step:
                dr, dc = step
                self.r += dr; self.c += dc
                cx, cy = self.c*CELL+CELL//2, self.r*CELL+CELL//2
                self.rect.center = (cx, cy)

    def draw(self, screen):
        color = self.frozen_color if self.frozen else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        if self.frozen:
            # icy outline so the frozen state is obvious
            pygame.draw.rect(screen, (200, 230, 255), self.rect, width=2, border_radius=5)
        # eyes
        for ex in [self.rect.x+4, self.rect.x+14]:
            pygame.draw.circle(screen, (255,255,255), (ex, self.rect.y+8), 4)
            pygame.draw.circle(screen, (0,0,0), (ex+1, self.rect.y+8), 2)