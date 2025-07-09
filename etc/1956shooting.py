## 소스코드
import pygame
from pygame.locals import *
import random

# 게임 설정
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
FPS = 60

# 색상
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Pygame 초기화
pygame.init()
try:
    pygame.mixer.init()
    sound_enabled = True
except pygame.error:
    print("Warning: 사운드 장치를 찾을 수 없습니다. 소리 없이 실행됩니다.")
    sound_enabled = False
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('1945 Shooting Game')
clock = pygame.time.Clock()

# 게임 리소스 로드
player_img = pygame.image.load('assets/images/player.png')
player_img = pygame.transform.scale(player_img, (80, 80))

enemy_img = pygame.image.load('assets/images/enemy.png')
enemy_img = pygame.transform.scale(enemy_img, (50, 50))

boss_img = pygame.image.load('assets/images/boss.png')
boss_img = pygame.transform.scale(boss_img, (200, 200))

bullet_img = pygame.image.load('assets/images/bullet.png')
bullet_img = pygame.transform.scale(bullet_img, (20, 40))

if sound_enabled:
    laser_sound = pygame.mixer.Sound('assets/sounds/laser.wav')
else:
    laser_sound = None

# 플레이어 클래스
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect()
        self.rect.centerx = WINDOW_WIDTH // 2
        self.rect.bottom = WINDOW_HEIGHT - 10
        self.speed = 5
        self.score = 0
        self.health = 10

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[K_LEFT]:
            self.rect.x -= self.speed
        if keys[K_RIGHT]:
            self.rect.x += self.speed
        if keys[K_UP]:
            self.rect.y -= self.speed
        if keys[K_DOWN]:
            self.rect.y += self.speed

        # 화면 밖으로 나가지 않기
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WINDOW_WIDTH:
            self.rect.right = WINDOW_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > WINDOW_HEIGHT:
            self.rect.bottom = WINDOW_HEIGHT

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top)
        all_sprites.add(bullet)
        bullets.add(bullet)
        if laser_sound:
            laser_sound.play()

# 적 클래스
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = enemy_img
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WINDOW_WIDTH - self.rect.width)
        self.rect.y = random.randint(-100, -40)
        self.speedy = random.randint(1, 3)
        self.speedx = random.randint(-3, 3)

    def update(self):
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        if self.rect.top > WINDOW_HEIGHT + 10 or self.rect.left < -25 or self.rect.right > WINDOW_WIDTH + 20:
            self.rect.x = random.randint(0, WINDOW_WIDTH - self.rect.width)
            self.rect.y = random.randint(-100, -40)
            self.speedy = random.randint(1, 8)

# 보스 클래스
class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = boss_img
        self.rect = self.image.get_rect()
        self.rect.x = WINDOW_WIDTH // 2 - self.image.get_width() // 2
        self.rect.y = 50
        self.health = 20

    def update(self):
        pass

# 총알 클래스
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speedy = -10

    def update(self):
        self.rect.y += self.speedy
        if self.rect.bottom < 0:
            self.kill()

# 스프라이트 그룹
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()

player = Player()
all_sprites.add(player)

for _ in range(10):
    enemy = Enemy()
    all_sprites.add(enemy)
    enemies.add(enemy)

boss = Boss()
all_sprites.add(boss)

# 게임 루프
running = True
while running:
    # FPS 조정
    clock.tick(FPS)

    # 이벤트 처리
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.shoot()

    # 스프라이트 업데이트
    all_sprites.update()

    # 충돌 처리 (총알-적)
    hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
    for hit in hits:
        player.score += 10
        enemy = Enemy()
        all_sprites.add(enemy)
        enemies.add(enemy)

    # 충돌 처리 (보스-총알)
    boss_hits = pygame.sprite.spritecollide(boss, bullets, True)
    for hit in boss_hits:
        player.score += 100
        boss.health -= 1
        if boss.health <= 0:
            running = False

    # 충돌 처리 (적/보스-우주선)
    hits = pygame.sprite.spritecollide(player, enemies, True)
    for hit in hits:
        player.health -= 1
        if player.health <= 0:
            running = False

    if pygame.sprite.collide_rect(player, boss):
        player.health -= 3
        if player.health <= 0:
            running = False

    # 화면 그리기
    screen.fill(BLACK)
    all_sprites.draw(screen)
    draw_text = pygame.font.SysFont('comicsans', 36).render(f"Score: {player.score} HP: {player.health}", True, WHITE)
    screen.blit(draw_text, (10, 10))
    pygame.display.flip()

pygame.quit()