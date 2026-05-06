import pygame
import math
import heapq

WIDTH, HEIGHT = 1100, 750
BOTTOM_BAR = 70
RADIUS = 6

# ⭐ Distance scale (MAIN FEATURE)
SCALE = 0.1   # 1 pixel = 0.1 TSPLIB distance unit

BG = (25, 25, 25)
WHITE = (230, 230, 230)
GRAY = (160, 160, 160)
YELLOW = (255, 220, 0)
GREEN = (0, 220, 0)
BLUE = (110, 170, 255)

FONT_SMALL = 12
FONT_MED = 15


def scaled_distance(a, b):
    pixel_dist = math.hypot(a[0] - b[0], a[1] - b[1])
    return pixel_dist * SCALE


# ---------- BUTTON ----------
class Button:

    def __init__(self, x, y, w, h, text, action):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action

    def draw(self, screen, font):
        pygame.draw.rect(screen, GRAY, self.rect, border_radius=8)
        txt = font.render(self.text, True, (0, 0, 0))
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def click(self, pos):
        if self.rect.collidepoint(pos):
            self.action()
            return True
        return False


# ---------- BUILDER ----------
class Builder:

    def __init__(self):
        self.coords = []  # stored as screen coordinates
        self.selected = None
        self.show_all_distances = False
        self.dragging = False

    def find_vertex(self, pos):
        for i, p in enumerate(self.coords):
            if math.hypot(p[0] - pos[0], p[1] - pos[1]) <= RADIUS + 3:
                return i
        return None

    def shortest(self, src):

        n = len(self.coords)
        dist = [float("inf")] * n
        parent = [-1] * n

        dist[src] = 0
        pq = [(0, src)]

        while pq:
            d, u = heapq.heappop(pq)

            if d > dist[u]:
                continue

            for v in range(n):
                if v == u:
                    continue

                w = scaled_distance(self.coords[u], self.coords[v])
                nd = d + w

                if nd < dist[v]:
                    dist[v] = nd
                    parent[v] = u
                    heapq.heappush(pq, (nd, v))

        return dist, parent

    # ⭐ Export scaled coordinates
    def save_tsplib(self):

        if not self.coords:
            return

        with open("custom_instance.tsp", "w") as f:
            f.write("NAME: custom_instance\n")
            f.write("TYPE: TSP\n")
            f.write(f"DIMENSION: {len(self.coords)}\n")
            f.write("EDGE_WEIGHT_TYPE: EUC_2D\n")
            f.write("NODE_COORD_SECTION\n")

            for i, (x, y) in enumerate(self.coords, start=1):
                sx = x * SCALE
                sy = y * SCALE
                f.write(f"{i} {sx:.2f} {sy:.2f}\n")

            f.write("EOF\n")

        print("Saved → custom_instance.tsp")

    def clear(self):
        self.coords.clear()
        self.selected = None


# ---------- MAIN ----------
def main():

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TSPLIB Builder v6 (Scaled)")

    font = pygame.font.SysFont(None, FONT_MED)
    small_font = pygame.font.SysFont(None, FONT_SMALL)

    clock = pygame.time.Clock()
    B = Builder()

    buttons = [
        Button(20, HEIGHT - 55, 120, 35, "SAVE", B.save_tsplib),
        Button(160, HEIGHT - 55, 120, 35, "CLEAR", B.clear),
        Button(300, HEIGHT - 55, 200, 35, "TOGGLE DISTANCES",
               lambda: setattr(B, "show_all_distances", not B.show_all_distances))
    ]

    running = True
    while running:

        for e in pygame.event.get():

            if e.type == pygame.QUIT:
                running = False

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:

                pos = e.pos

                if pos[1] >= HEIGHT - BOTTOM_BAR:
                    for btn in buttons:
                        if btn.click(pos):
                            break
                    continue

                v = B.find_vertex(pos)

                if v is None:
                    B.coords.append(pos)
                    B.selected = None
                else:
                    B.selected = v
                    B.dragging = True

            if e.type == pygame.MOUSEBUTTONUP:
                B.dragging = False

            if e.type == pygame.MOUSEMOTION and B.dragging:
                if B.selected is not None:
                    B.coords[B.selected] = e.pos

        # ---------- DRAW ----------
        screen.fill(BG)

        # All distances overlay
        if B.show_all_distances:
            for i in range(len(B.coords)):
                for j in range(i + 1, len(B.coords)):
                    a, b = B.coords[i], B.coords[j]
                    d = scaled_distance(a, b)

                    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                    pygame.draw.line(screen, BLUE, a, b, 1)
                    screen.blit(
                        small_font.render(f"{d:.1f}", True, BLUE),
                        (mx, my)
                    )

        # Shortest path tree
        elif B.selected is not None:
            dist, parent = B.shortest(B.selected)

            for v, p in enumerate(parent):
                if p != -1:
                    pygame.draw.line(screen, GREEN,
                                     B.coords[v], B.coords[p], 3)

        # Vertices
        for i, (x, y) in enumerate(B.coords):

            color = WHITE
            if not B.show_all_distances and i == B.selected:
                color = YELLOW

            pygame.draw.circle(screen, color, (x, y), RADIUS)

            label = f"{i} ({x*SCALE:.1f},{y*SCALE:.1f})"

            if not B.show_all_distances and B.selected is not None:
                dist, _ = B.shortest(B.selected)
                if dist[i] < float("inf"):
                    label += f" d={dist[i]:.1f}"

            screen.blit(small_font.render(label, True, WHITE),
                        (x + 6, y - 6))

        # Bottom bar
        pygame.draw.rect(screen, (40, 40, 40),
                         (0, HEIGHT - BOTTOM_BAR, WIDTH, BOTTOM_BAR))

        for btn in buttons:
            btn.draw(screen, font)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
