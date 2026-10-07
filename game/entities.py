import pygame
from game.maze import CELL

SPEED = 2
WALL_T = 3  # wall thickness in px, matches the line width used when drawing


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
        if rect.left < 0 or rect.top < 0 or rect.right > cols*CELL or rect.bottom > rows*CELL:
            return False
        # check only the cells the rect touches (plus a small margin so
        # walls sitting exactly on a cell border are never missed)
        probe = rect.inflate(4, 4)
        r0 = max(0, probe.top // CELL)
        r1 = min(rows-1, (probe.bottom-1) // CELL)
        c0 = max(0, probe.left // CELL)
        c1 = min(cols-1, (probe.right-1) // CELL)
        h = WALL_T // 2
        for r in range(r0, r1+1):
            for c in range(c0, c1+1):
                x, y = c*CELL, r*CELL
                top, bottom, right, left = walls[r][c]
                if top and rect.colliderect(pygame.Rect(x-h, y-h, CELL+WALL_T, WALL_T)):
                    return False
                if bottom and rect.colliderect(pygame.Rect(x-h, y+CELL-h, CELL+WALL_T, WALL_T)):
                    return False
                if right and rect.colliderect(pygame.Rect(x+CELL-h, y-h, WALL_T, CELL+WALL_T)):
                    return False
                if left and rect.colliderect(pygame.Rect(x-h, y-h, WALL_T, CELL+WALL_T)):
                    return False
        return True

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, self.rect)


class Enemy:
    def __init__(self, r, c):
        self.r, self.c = r, c
        cx, cy = c*CELL+CELL//2, r*CELL+CELL//2
        self.rect = pygame.Rect(cx-12, cy-12, 24, 24)
        self.color = (220, 60, 60)
        self.timer = 0
        self.move_interval = 20  # frames between cell moves

    def update(self, walls, player, rows, cols):
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
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        # eyes
        for ex in [self.rect.x+4, self.rect.x+14]:
            pygame.draw.circle(screen, (255,255,255), (ex, self.rect.y+8), 4)
            pygame.draw.circle(screen, (0,0,0), (ex+1, self.rect.y+8), 2)