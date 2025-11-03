# mixmath_pygame.py
import pygame
import sys
import math

# ---------- CONFIG ----------
WINDOW_W, WINDOW_H = 1000, 600
FPS = 60
SLOT_COUNT = 9  # จำนวนช่องสำหรับวางสมการ (ปรับได้ per level)
FONT_NAME = None
BG_COLOR = (245, 245, 250)
SLOT_COLOR = (230, 230, 235)
TILE_COLOR = (255, 255, 255)
TILE_BORDER = (40, 40, 40)
GOOD_COLOR = (180, 245, 180)
BAD_COLOR = (255, 200, 200)

# ---------- LEVELS: define tiles per level ----------
LEVELS = [
    # level 1 - easy (8 ตัว)
    ["1", "2", "3", "+", "-", "=", "4", "5"],
    # level 2 - medium (9 ตัว)
    ["10", "+", "2", "=", "5", "*", "1", "0", "-"],
    # level 3 - harder (9 ตัว)
    ["3", "5", "=", "*", "2", "7", "+", "1", "/"],
    # level 4 - custom mix
    ["12", "=", "3", "*", "4", "+", "6", "-", "2"],
]

# ---------- SAFE EXPRESSION PARSE & EVAL ----------
# We'll implement tokenization, shunting-yard to RPN, then evaluate RPN.
# Supported tokens: integers (multi-digit), + - * /
# Division uses true division; compare LHS and RHS with tolerance.

def tokenize(expr):
    tokens = []
    i = 0
    s = expr.replace(" ", "")
    while i < len(s):
        c = s[i]
        if c.isdigit():
            j = i+1
            while j < len(s) and s[j].isdigit():
                j += 1
            tokens.append(s[i:j])
            i = j
        elif c in "+-*/()":
            tokens.append(c)
            i += 1
        else:
            # invalid char
            return None
    return tokens

_prec = {"+":1, "-":1, "*":2, "/":2}

def to_rpn(tokens):
    out = []
    stack = []
    for t in tokens:
        if t.isdigit():
            out.append(t)
        elif t in _prec:
            while stack and stack[-1] in _prec and _prec[stack[-1]] >= _prec[t]:
                out.append(stack.pop())
            stack.append(t)
        elif t == "(":
            stack.append(t)
        elif t == ")":
            while stack and stack[-1] != "(":
                out.append(stack.pop())
            if not stack:
                return None
            stack.pop()
        else:
            return None
    while stack:
        if stack[-1] in "()":
            return None
        out.append(stack.pop())
    return out

def eval_rpn(rpn):
    try:
        st = []
        for t in rpn:
            if t.isdigit():
                st.append(float(t))
            else:
                if len(st) < 2:
                    return None
                b = st.pop()
                a = st.pop()
                if t == "+":
                    st.append(a + b)
                elif t == "-":
                    st.append(a - b)
                elif t == "*":
                    st.append(a * b)
                elif t == "/":
                    if abs(b) < 1e-9:
                        return None
                    st.append(a / b)
                else:
                    return None
        if len(st) != 1:
            return None
        return st[0]
    except Exception:
        return None

def safe_eval(expr):
    # returns float or None on invalid
    tokens = tokenize(expr)
    if tokens is None:
        return None
    rpn = to_rpn(tokens)
    if rpn is None:
        return None
    return eval_rpn(rpn)

def check_equation(expr):
    # expr string must contain exactly one '='
    if expr.count("=") != 1:
        return False, "สมการต้องมีเครื่องหมาย '=' เพียงตัวเดียว"
    left, right = expr.split("=", 1)
    if left.strip() == "" or right.strip() == "":
        return False, "ฝั่งซ้ายหรือขวาว่าง"
    lv = safe_eval(left)
    rv = safe_eval(right)
    if lv is None or rv is None:
        return False, "รูปแบบสมการไม่ถูกต้อง"
    if math.isclose(lv, rv, rel_tol=1e-9, abs_tol=1e-6):
        return True, f"ถูกต้อง: {left} = {right} -> {lv:.6g}"
    else:
        return False, f"ไม่เท่ากัน: {lv} ≠ {rv}"

# ---------- PYGAME UI CLASSES ----------
class Tile:
    def __init__(self, text, pos):
        self.text = str(text)
        self.rect = pygame.Rect(pos[0], pos[1], 76, 76)
        self.dragging = False
        self.offset = (0,0)
        self.origin = pos
        self.in_slot = None  # index of slot if placed

    def draw(self, surf, font, border_color=TILE_BORDER):
        pygame.draw.rect(surf, TILE_COLOR, self.rect, border_radius=8)
        pygame.draw.rect(surf, border_color, self.rect, 2, border_radius=8)
        txt = font.render(self.text, True, (10,10,10))
        tx = txt.get_width()
        ty = txt.get_height()
        surf.blit(txt, (self.rect.centerx - tx//2, self.rect.centery - ty//2))

    def update_position(self, pos):
        self.rect.topleft = (pos[0] - self.offset[0], pos[1] - self.offset[1])

    def reset_origin(self):
        self.rect.topleft = self.origin

class Slot:
    def __init__(self, idx, rect):
        self.idx = idx
        self.rect = rect
        self.tile = None  # Tile assigned

    def draw(self, surf, font, highlight=False, good=None):
        color = SLOT_COLOR
        pygame.draw.rect(surf, color, self.rect, border_radius=6)
        pygame.draw.rect(surf, (120,120,120), self.rect, 2, border_radius=6)
        if highlight:
            pygame.draw.rect(surf, (80,160,240), self.rect, 4, border_radius=6)
        if good is not None:
            # pass True/False to show green/red overlay
            overlay = GOOD_COLOR if good else BAD_COLOR
            s = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            s.fill((*overlay, 70))
            surf.blit(s, self.rect.topleft)
        if self.tile:
            # draw tile centered in slot
            trect = self.tile.rect
            # draw tile with same size as slot for neatness:
            temp = pygame.Rect(self.rect.left + 6, self.rect.top + 6, self.rect.w - 12, self.rect.h - 12)
            pygame.draw.rect(surf, TILE_COLOR, temp, border_radius=6)
            pygame.draw.rect(surf, TILE_BORDER, temp, 2, border_radius=6)
            txt = font.render(self.tile.text, True, (10,10,10))
            surf.blit(txt, (temp.centerx - txt.get_width()//2, temp.centery - txt.get_height()//2))

# ---------- GAME ----------
class MixMathGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("MIXMATH - ท้าคิดเลขไว")
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(FONT_NAME, 28)
        self.bigfont = pygame.font.SysFont(FONT_NAME, 36, bold=True)

        self.level_idx = 0
        self.load_level(self.level_idx)

        self.msg = ""
        self.msg_color = (20,20,20)
        self.last_check_result = None  # True/False/None

    def load_level(self, idx):
        self.tiles = []
        self.slots = []
        self.last_check_result = None
        self.msg = f"ด่าน {idx+1}"
        tile_texts = LEVELS[idx % len(LEVELS)]
        # create tile objects in tile bank area
        start_x = 60
        start_y = 120
        gap = 90
        for i, t in enumerate(tile_texts):
            x = start_x + (i % 6) * gap
            y = start_y + (i // 6) * gap
            tile = Tile(t, (x, y))
            self.tiles.append(tile)

        # create slots centered near bottom
        total_w = SLOT_COUNT * 88
        base_x = (WINDOW_W - total_w) // 2
        y = WINDOW_H - 160
        for i in range(SLOT_COUNT):
            r = pygame.Rect(base_x + i*88, y, 80, 80)
            self.slots.append(Slot(i, r))

        # clear tiles assignment
        for t in self.tiles:
            t.in_slot = None
            t.origin = t.rect.topleft

    def get_tile_at_pos(self, pos):
        # iterate from top (last drawn) to bottom
        for t in reversed(self.tiles):
            if t.rect.collidepoint(pos):
                return t
        return None

    def get_slot_at_pos(self, pos):
        for s in self.slots:
            if s.rect.collidepoint(pos):
                return s
        return None

    def all_slots_text(self):
        # join tile texts in slot order (empty slots as '')
        parts = []
        for s in self.slots:
            if s.tile:
                parts.append(s.tile.text)
            else:
                parts.append("")
        # create expression by concatenating non-empty sequentially (we'll treat empty slots as separators)
        expr = "".join([p for p in parts if p != ""])
        return expr, parts

    def handle_check(self):
        expr, parts = self.all_slots_text()
        ok, message = check_equation(expr)
        self.msg = message
        self.last_check_result = ok
        self.msg_color = (0,120,0) if ok else (180,20,20)

    def place_tile_in_slot(self, tile, slot):
        # if slot has tile, swap positions
        if slot.tile:
            other = slot.tile
            # put other back to tile's origin (or to tile's prior slot)
            if tile.in_slot is not None:
                # swap positions: tile goes to this slot, other to tile.in_slot
                prev_slot = self.slots[tile.in_slot]
                prev_slot.tile = other
                other.in_slot = prev_slot.idx
                # set tile to new slot
                slot.tile = tile
                tile.in_slot = slot.idx
            else:
                # tile came from bank: move other to bank origin
                other.in_slot = None
                other.reset_origin()
                slot.tile = tile
                tile.in_slot = slot.idx
        else:
            # empty slot
            if tile.in_slot is not None:
                prev_slot = self.slots[tile.in_slot]
                prev_slot.tile = None
            slot.tile = tile
            tile.in_slot = slot.idx
        # snap tile rect to slot
        if tile.in_slot is not None:
            tile.rect.topleft = (slot.rect.left + 6, slot.rect.top + 6)
            tile.origin = tile.rect.topleft
        else:
            tile.reset_origin()

    def run(self):
        selected_tile = None
        running = True
        drag_offset = (0,0)
        while running:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    tile = self.get_tile_at_pos(pos)
                    if tile:
                        # start dragging
                        selected_tile = tile
                        tile.dragging = True
                        tile.offset = (pos[0] - tile.rect.left, pos[1] - tile.rect.top)
                        # if it was in a slot, remove from slot temporarily
                        if tile.in_slot is not None:
                            s = self.slots[tile.in_slot]
                            s.tile = None
                            tile.in_slot = None
                    else:
                        # click on slot to do click-swap (if no drag)
                        s = self.get_slot_at_pos(pos)
                        if s:
                            # find currently selected via previous click? We'll implement click-select: if no tile selected, pick tile from bank by clicking on it (tile-click is above). So here nothing.
                            pass
                elif event.type == pygame.MOUSEBUTTONUP:
                    pos = pygame.mouse.get_pos()
                    if selected_tile:
                        selected_tile.dragging = False
                        # snap to slot if releasing over slot
                        s = self.get_slot_at_pos(pos)
                        if s:
                            self.place_tile_in_slot(selected_tile, s)
                        else:
                            # not over a slot: return to origin (bank)
                            selected_tile.reset_origin()
                            selected_tile.in_slot = None
                        selected_tile = None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.handle_check()
                    elif event.key == pygame.K_n:
                        # next level
                        self.level_idx = (self.level_idx + 1) % len(LEVELS)
                        self.load_level(self.level_idx)

            # handle mouse clicks as swap when not dragging:
            if pygame.mouse.get_pressed()[0]:
                # if clicked but not dragging a tile, implement click-select-swap:
                # We'll allow quick-click: click a tile to pick up, then click a slot to place/swap. For simplicity, above MOUSEBUTTONDOWN handled picks.
                pass

            # update drag movement
            for t in self.tiles:
                if t.dragging:
                    t.update_position(pygame.mouse.get_pos())

            # DRAW
            self.screen.fill(BG_COLOR)
            # Title
            title = self.bigfont.render("MIXMATH - ท้าคิดเลขไว (drag / click เพื่อวาง)", True, (20,20,20))
            self.screen.blit(title, (30, 20))

            # draw tile bank label
            bank_label = self.font.render("Tile bank", True, (30,30,30))
            self.screen.blit(bank_label, (60, 90))

            # draw tiles (bank)
            for t in self.tiles:
                # if tile is placed in slot we don't draw it here (slot draws tile)
                if t.in_slot is None:
                    t.draw(self.screen, self.font)
            # draw slots
            mouse_pos = pygame.mouse.get_pos()
            for s in self.slots:
                highlight = s.rect.collidepoint(mouse_pos)
                good = None
                if self.last_check_result is not None:
                    good = self.last_check_result
                s.draw(self.screen, self.font, highlight=highlight, good=good)

            # draw tiles that are in slots (so they appear above slot)
            for s in self.slots:
                if s.tile:
                    # ensure tile rect aligns with slot
                    s.tile.rect.topleft = (s.rect.left + 6, s.rect.top + 6)
                    s.tile.draw(self.screen, self.font)

            # draw UI buttons (simple rectangles)
            # Check button
            check_rect = pygame.Rect(WINDOW_W - 220, 90, 180, 48)
            pygame.draw.rect(self.screen, (220,220,240), check_rect, border_radius=8)
            pygame.draw.rect(self.screen, (100,100,160), check_rect, 2, border_radius=8)
            check_txt = self.font.render("ตรวจสอบ (Enter)", True, (10,10,10))
            self.screen.blit(check_txt, (check_rect.left + 14, check_rect.top + 10))

            # Next level button
            next_rect = pygame.Rect(WINDOW_W - 220, 150, 180, 48)
            pygame.draw.rect(self.screen, (220,240,220), next_rect, border_radius=8)
            pygame.draw.rect(self.screen, (80,130,80), next_rect, 2, border_radius=8)
            next_txt = self.font.render("ด่านถัดไป (N)", True, (10,10,10))
            self.screen.blit(next_txt, (next_rect.left + 18, next_rect.top + 10))

            # instructions
            ins1 = self.font.render("ลากหรือต้องคลิกเพื่อย้ายตัวเบี้ยไปที่ช่อง แล้วกด Enter เพื่อตรวจสอบ", True, (40,40,40))
            self.screen.blit(ins1, (30, WINDOW_H - 40))

            # status message
            msg_surf = self.font.render(self.msg, True, self.msg_color)
            self.screen.blit(msg_surf, (30, 70))

            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = MixMathGame()
    game.run()