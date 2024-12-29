
import pygame
import cv2
import mediapipe as mp
import random
import math
import sys

# Initialize pygame and MediaPipe
pygame.init()
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Set screen size
screen_width, screen_height = 640, 480
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Stylish Hand Gesture Ball Escape')

# Colors
neon_colors = [(255, 50, 200), (50, 200, 255), (255, 255, 50)]
background_particles = []

def generate_background_particles():
    return [{"x": random.randint(0, screen_width), "y": random.randint(0, screen_height),
             "dx": random.uniform(-0.5, 0.5), "dy": random.uniform(-0.5, 0.5),
             "radius": random.randint(1, 4), "color": random.choice(neon_colors)}
            for _ in range(50)]

background_particles = generate_background_particles()

# Ball properties
ball_radius = 20
ball_color = (255, 50, 200)  # Neon pink
ball_trail = []
trail_length = 15

def draw_glowing_circle(surface, color, center, radius, glow_width=10):
    for i in range(glow_width, 0, -1):
        alpha = max(0, 255 * (i / glow_width))
        pygame.draw.circle(surface, (*color, int(alpha)), center, radius + i)

# Obstacle properties
obstacle_width, obstacle_height = 100, 20
obstacle_speed = 5
obstacle_glow_width = 8
obstacle_color = (50, 255, 100)  # Neon green

# Particle effect for collisions
def generate_particles(position, color, particle_count=30):
    return [
        {
            "x": position[0] + random.randint(-10, 10),
            "y": position[1] + random.randint(-10, 10),
            "dx": random.uniform(-2, 2),
            "dy": random.uniform(-2, 2),
            "life": random.randint(20, 50),
            "color": color,
        }
        for _ in range(particle_count)
    ]

particles = []

# Create the clock object to control the frame rate
clock = pygame.time.Clock()

# Initialize webcam
cap = cv2.VideoCapture(0)

# Game variables
obstacles = []  # List to store obstacle positions
spawn_interval = 30  # Frames between new obstacles
frame_count = 0  # Counter for frame-based events
score = 0  # Player's score
font = pygame.font.SysFont("Arial", 28)  # Font for score display
game_over = False  # Game over flag

# Function to reset the game
def reset_game():
    global obstacles, frame_count, score, game_over, ball_radius, particles, ball_trail
    obstacles = []
    frame_count = 0
    score = 0
    game_over = False
    ball_radius = 20
    particles = []
    ball_trail = []

# Function to calculate distance between landmarks
def calculate_distance(landmark1, landmark2, width, height):
    x1, y1 = int(landmark1.x * width), int(landmark1.y * height)
    x2, y2 = int(landmark2.x * width), int(landmark2.y * height)
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

while True:
    if game_over:
        # Display Game Over screen
        screen.fill((0, 0, 0))
        game_over_text = font.render("Game Over! Press R to Restart or Q to Quit", True, (255, 255, 255))
        final_score = font.render(f"Final Score: {score}", True, (255, 255, 0))
        screen.blit(game_over_text, (screen_width // 2 - game_over_text.get_width() // 2, screen_height // 2 - 50))
        screen.blit(final_score, (screen_width // 2 - final_score.get_width() // 2, screen_height // 2))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Restart
                    reset_game()
                elif event.key == pygame.K_q:  # Quit
                    cap.release()
                    pygame.quit()
                    sys.exit()
        continue

    # Read frame from webcam
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # Clear screen with a gradient background
    screen.fill((0, 0, 0))
    for i, particle in enumerate(background_particles):
        particle["x"] += particle["dx"]
        particle["y"] += particle["dy"]
        if particle["x"] < 0 or particle["x"] > screen_width:
            particle["dx"] *= -1
        if particle["y"] < 0 or particle["y"] > screen_height:
            particle["dy"] *= -1
        pygame.draw.circle(screen, particle["color"], (int(particle["x"]), int(particle["y"])), particle["radius"])

    # Update particle effects
    for particle in particles[:]:
        particle["x"] += particle["dx"]
        particle["y"] += particle["dy"]
        particle["life"] -= 1
        pygame.draw.circle(screen, particle["color"], (int(particle["x"]), int(particle["y"])), 3)
        if particle["life"] <= 0:
            particles.remove(particle)

    # Draw the ball controlled by hand
    ball_x, ball_y = None, None
    if results.multi_hand_landmarks:
        for landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)

            wrist_landmark = landmarks.landmark[mp_hands.HandLandmark.WRIST]
            ball_x = int(wrist_landmark.x * screen_width)
            ball_y = int(wrist_landmark.y * screen_height)

            thumb_tip = landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            index_tip = landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            distance = calculate_distance(thumb_tip, index_tip, screen_width, screen_height)
            ball_radius = max(10, min(int(distance / 2), 50))

            ball_trail.append((ball_x, ball_y))
            if len(ball_trail) > trail_length:
                ball_trail.pop(0)

            if ball_x and ball_y:
                for pos in ball_trail:
                    pygame.draw.circle(screen, (255, 255, 255, 50), pos, ball_radius // 2, 1)
                draw_glowing_circle(screen, ball_color, (ball_x, ball_y), ball_radius)

    # Spawn and move obstacles
    if frame_count % spawn_interval == 0:
        obstacle_x = random.randint(0, screen_width - obstacle_width)
        obstacles.append([obstacle_x, 0])

    for obstacle in obstacles[:]:
        obstacle[1] += obstacle_speed
        pygame.draw.rect(screen, obstacle_color, (obstacle[0], obstacle[1], obstacle_width, obstacle_height))

        if ball_x and ball_y:
            ball_rect = pygame.Rect(ball_x - ball_radius, ball_y - ball_radius, ball_radius * 2, ball_radius * 2)
            obstacle_rect = pygame.Rect(obstacle[0], obstacle[1], obstacle_width, obstacle_height)
            if ball_rect.colliderect(obstacle_rect):
                particles.extend(generate_particles((ball_x, ball_y), ball_color))
                game_over = True

        if obstacle[1] > screen_height:
            obstacles.remove(obstacle)
            score += 1

    # Display score
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))

    pygame.display.update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            cap.release()
            pygame.quit()
            sys.exit()

    clock.tick(30)
    frame_count += 1
