import pygame, sys, os, json
from logic import check_equation
from questions import QUESTIONS_LEVEL, get_questions_for_level

pygame.init()

WIDTH, HEIGHT = 850, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("A-Math Game")

FONT = pygame.font.Font("materials/myfont.ttf", 28)
SMALL = pygame.font.SysFont("Arial", 28)

background_img = pygame.image.load('materials/bg.jpg')

#sound fx
skip_sfx = pygame.mixer.Sound('materials/skip.mp3')
start_sfx = pygame.mixer.Sound('materials/start.wav')
gameover_sfx = pygame.mixer.Sound('materials/over.wav')
tiles_sfx = pygame.mixer.Sound('materials/tiles.wav')

WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY = (200,200,200)
BLUE = (80,150,255)
GREEN = (50,200,90)
RED = (220,50,50)

clock = pygame.time.Clock()
SCORES_FILE = "scores.json"

# - Scoreboard - 
def load_scores():
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE,"r") as f:
            return json.load(f)
    return []

def save_score(score):
    scores = load_scores()
    scores.append(score)
    scores = sorted(scores, reverse=True)[:10]
    with open(SCORES_FILE,"w") as f:
        json.dump(scores,f)

def reset_scores():
    if os.path.exists(SCORES_FILE):
        os.remove(SCORES_FILE)

# ---------------- Utilityของเกม ----------------
def draw_text(text,x,y,color=BLACK,center=False,font=FONT):
    surface = font.render(text,True,color)
    rect = surface.get_rect()
    if center:
        rect.center = (x,y)
    else:
        rect.topleft = (x,y)
    screen.blit(surface,rect)

class Button:
    def __init__(self,x,y,w,h,text):
        self.rect = pygame.Rect(x,y,w,h)
        self.text = text
    def draw(self,color=BLUE):
        pygame.draw.rect(screen,color,self.rect,border_radius=12)
        draw_text(self.text,self.rect.centerx,self.rect.centery,WHITE,center=True)
    def is_clicked(self,pos):
        return self.rect.collidepoint(pos)

class Tile:
    def __init__(self,text,x,y):
        self.text = text
        self.rect = pygame.Rect(x,y,70,70)
        self.original = (x,y)
        self.in_answer_slot = False
    def draw(self):
        pygame.draw.rect(screen,GRAY,self.rect,border_radius=10)
        draw_text(self.text,self.rect.centerx,self.rect.centery,BLACK,center=True)
    def reset(self):
        self.rect.topleft = self.original
        self.in_answer_slot = False

# ---------------- Game State ----------------
game_started = False
score = 0
time = 60
level = 1
level_index = 0
tiles = []
answers = []
answer_slots = []

START_BUTTON = Button(325, HEIGHT//2-120, 200, 60, "Start Game")
RESET_BUTTON = Button(675, 475, 120, 40, "Reset")
SKIP_BUTTON = Button(WIDTH-200, HEIGHT-500, 150, 50, "Skip")

# ---------------- สุ่มโจทย์ปัญหา ----------------
def start_button():
    LEVEL_QUESTIONS = {}
    for lvl in QUESTIONS_LEVEL:
        LEVEL_QUESTIONS[lvl] = get_questions_for_level(lvl)
    return LEVEL_QUESTIONS

    
def load_question(LEVEL_QUESTIONS):
    
    global tiles, answers, answer_slots, level_index
    a = LEVEL_QUESTIONS[level]
    if level_index >= len(a):
        level_index = 0
    eq = a[level_index]
    level_index += 1
    tiles.clear(); answers.clear(); answer_slots.clear()
    answers.extend([None]*len(eq))
    start_x = WIDTH//2 - (len(eq)*80)//2
    for i,t in enumerate(eq):
        tiles.append(Tile(t,start_x+i*80,450))
        answer_slots.append(pygame.Rect(start_x+i*80,250,70,70))

# ---------------- Game Over เกมจบ(เวลาหมด) ----------------
def show_game_over():
    gameover_sfx.play()     #เสียง
    save_score(score)
    waiting = True
    BACK_BUTTON = Button(WIDTH//2-100, HEIGHT//2+60, 200, 60, "Back to Menu")
    while waiting:
        screen.fill(WHITE)
        draw_text("Time's Up!", WIDTH//2, HEIGHT//2-60, RED, center=True, font=FONT)
        draw_text(f"Score: {score}", WIDTH//2, HEIGHT//2, BLACK, center=True, font=SMALL)
        BACK_BUTTON.draw()
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if BACK_BUTTON.is_clicked(event.pos):
                    waiting=False

# คะแนนเกิน 50 แสดง god of math

def show_god_of_math():
    save_score(score)
    waiting = True
    BACK_BUTTON = Button(WIDTH//2-100, HEIGHT//2+60, 200, 60, "Back to Menu")
    while waiting:
        screen.fill(WHITE)
        draw_text("GOD OF MATH", WIDTH/2, HEIGHT/2 - 40, (255,165,0), center=True)  # สีทอง
        draw_text(f"Final Score: {score}", WIDTH/2, HEIGHT/2 + 20, BLACK, center=True)
        BACK_BUTTON.draw()
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if BACK_BUTTON.is_clicked(event.pos):
                    waiting=False
    
# ---------------- Main Loop ----------------
while True:
    dt = clock.tick(60)/1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if not game_started:
                if START_BUTTON.is_clicked(pos):
                    start_sfx.play()    #เสียง
                    game_started=True
                    score=0; level=1; time_left = time; level_index=0
                    LEVEL_QUESTIONS = start_button()
                    load_question(LEVEL_QUESTIONS)
                if RESET_BUTTON.is_clicked(pos):
                    reset_scores()
                continue
            # คลิก Tile
            for tile in tiles:
                if tile.rect.collidepoint(pos) and not tile.in_answer_slot:
                    tiles_sfx.play()   #เสียง
                    for i in range(len(answer_slots)):
                        if answers[i] is None:
                            answers[i]=tile
                            tile.rect.topleft=answer_slots[i].topleft
                            tile.in_answer_slot=True
                            break
            # คลิก Tile ในคำตอบคืน
            for i,tile in enumerate(answers):
                if tile and tile.rect.collidepoint(pos):
                    tile.reset()
                    answers[i]=None
            # Skip
            if SKIP_BUTTON.is_clicked(pos):
                skip_sfx.play() #เสียง
                time_left -= 10
                load_question(LEVEL_QUESTIONS)

    # ---------------- Game Logic ----------------
    if game_started:
        if score >= 50:
            show_god_of_math()
            game_started=False
            
        time_left -= dt
        if time_left <=0:
            show_game_over()
            game_started=False
            
        if all(a is not None for a in answers):
            tokens = [a.text for a in answers]
            if check_equation(tokens):
                score +=1
                time_left +=3
                # เปลี่ยนเลเวล
                if score >=40: level=5
                elif score >=30: level=4
                elif score >=20: level=3
                elif score >=10: level=2
                else: level=1
                load_question(LEVEL_QUESTIONS)

    # ---------------- Render ----------------
    screen.fill(WHITE)
    
    screen.blit(background_img, (0, 0))
    
    if not game_started:
        draw_text("A-Math Game", WIDTH//2, 60, BLACK, center=True, font=FONT)
        START_BUTTON.draw()
        RESET_BUTTON.draw(color=RED)
        # Scoreboard ชิดขวา
        sb_rect = pygame.Rect(WIDTH-250, 100, 220, 350)
        pygame.draw.rect(screen, GRAY, sb_rect, border_radius=12)
        pygame.draw.rect(screen, BLACK, sb_rect, width=3, border_radius=12)
        draw_text("Scoreboard", sb_rect.left+20, sb_rect.top+10, BLACK, font=SMALL)
        scores = load_scores()
        for i,s in enumerate(scores):
            draw_text(f"{i+1}. {s}", sb_rect.centerx, sb_rect.top+50+i*30, BLACK, center=True, font=SMALL)
    else:
        draw_text(f"Score: {score}  Level: {level}", 50, 30)
        draw_text(f"Time: {int(time_left)}", WIDTH-190, 30)
        for slot in answer_slots:
            pygame.draw.rect(screen, (247 ,225 ,56), slot, width=3, border_radius=10)
        SKIP_BUTTON.draw(RED)
        for tile in tiles:
            tile.draw()
    pygame.display.update()