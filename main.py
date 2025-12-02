import pygame
import pymunk
import pymunk.pygame_util
import json
import random
import math
import os

# --- Configuration ---
WIDTH, HEIGHT = 800, 600
FPS = 60
BALL_RADIUS = 15
SAVE_FILE = "save_data.json"

class Particle:
    """Simple particle for trail and explosion effects"""
    def __init__(self, x, y, vx, vy, color, lifetime=30):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = random.randint(2, 5)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3
        self.vx *= 0.98
        self.lifetime -= 1
    
    def draw(self, screen):
        if self.lifetime > 0:
            faded_color = tuple(int(c * (self.lifetime / self.max_lifetime)) for c in self.color[:3])
            pygame.draw.circle(screen, faded_color, (int(self.x), int(self.y)), self.size)
    
    def is_alive(self):
        return self.lifetime > 0

class Button:
    """Simple button class for menu"""
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
    
    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 3, border_radius=10)
        
        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class PhysicsGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Gravity Puzzle - Second-Order Mechanics")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        self.big_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        
        # Load Levels from JSON
        with open('levels.json', 'r') as f:
            self.levels_data = json.load(f)
        
        # Load or create save data
        self.load_save_data()
        
        # Game state
        self.state = "MAIN_MENU"  # MAIN_MENU, LEVEL_SELECT, PLAYING, PAUSED, STATS
        self.current_level_index = 0
        self.particles = []
        self.trail_counter = 0
        self.death_animation = False
        self.death_timer = 0
        self.lives = 3
        self.level_time = 0
        self.paused = False
        
        # Menu buttons
        self.create_menu_buttons()
        
        self.running = True

    def create_menu_buttons(self):
        """Create buttons for different menus"""
        # Main Menu
        self.main_menu_buttons = [
            Button(WIDTH//2 - 100, 200, 200, 50, "Play", (50, 100, 200), (70, 120, 220)),
            Button(WIDTH//2 - 100, 270, 200, 50, "Level Select", (50, 150, 100), (70, 170, 120)),
            Button(WIDTH//2 - 100, 340, 200, 50, "Statistics", (150, 50, 150), (170, 70, 170)),
            Button(WIDTH//2 - 100, 410, 200, 50, "Quit", (200, 50, 50), (220, 70, 70)),
        ]
        
        # Pause Menu
        self.pause_menu_buttons = [
            Button(WIDTH//2 - 100, 200, 200, 50, "Resume", (50, 200, 50), (70, 220, 70)),
            Button(WIDTH//2 - 100, 270, 200, 50, "Restart", (200, 150, 50), (220, 170, 70)),
            Button(WIDTH//2 - 100, 340, 200, 50, "Main Menu", (100, 100, 200), (120, 120, 220)),
        ]

    def load_save_data(self):
        """Load save data or create new"""
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                self.save_data = json.load(f)
        else:
            self.save_data = {
                "unlocked_levels": 1,
                "level_scores": {},
                "total_time": 0,
                "total_deaths": 0
            }
            self.save_game()
    
    def save_game(self):
        """Save game progress"""
        with open(SAVE_FILE, 'w') as f:
            json.dump(self.save_data, f, indent=2)

    def load_level(self, index):
        """Wipes the physics space and builds the new level"""
        if index >= len(self.levels_data):
            self.state = "STATS"
            return

        # Reset game state
        self.particles = []
        self.death_animation = False
        self.death_timer = 0
        self.current_level_index = index
        
        # Get lives from level data or default to 3
        data = self.levels_data[index]
        self.lives = data.get('lives', 3)
        self.level_time = 0

        # Reset Physics Space
        self.space = pymunk.Space()
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        
        # Extract Data
        self.goal_rect = pygame.Rect(data['goal_rect'])
        
        # Apply Environment Settings
        self.space.gravity = tuple(data['gravity_start'])
        self.space.damping = data['damping_start']
        
        # Build Walls
        self.create_boundary()
        for w in data['walls']:
            rect_x, rect_y, rect_w, rect_h = w
            self.create_block(rect_x, rect_y, rect_w, rect_h)

        # Build Hazards
        self.hazard_rects = []
        if 'hazards' in data:
            for h in data['hazards']:
                rect_x, rect_y, rect_w, rect_h = h
                hazard_rect = pygame.Rect(rect_x, rect_y, rect_w, rect_h)
                self.hazard_rects.append(hazard_rect)

        # Create Player Ball
        start_x, start_y = data['start_pos']
        self.create_ball(start_x, start_y)
        
        self.state = "PLAYING"
        print(f"Loaded Level {data['level_id']} - {data['name']} ({data['difficulty']})")

    def create_boundary(self):
        """Creates the screen edges"""
        walls = [
            (0, 0, WIDTH, 10),
            (0, HEIGHT-10, WIDTH, 10),
            (0, 0, 10, HEIGHT),
            (WIDTH-10, 0, 10, HEIGHT)
        ]
        for x, y, w, h in walls:
            self.create_block(x, y, w, h)

    def create_block(self, x, y, w, h):
        """Helper to make a static wall"""
        center_x = x + w / 2
        center_y = y + h / 2
        
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = (center_x, center_y)
        shape = pymunk.Poly.create_box(body, (w, h))
        shape.elasticity = 0.8
        shape.friction = 0.5
        shape.color = (150, 150, 150, 255)
        self.space.add(body, shape)

    def create_ball(self, x, y):
        mass = 10
        inertia = pymunk.moment_for_circle(mass, 0, BALL_RADIUS)
        self.ball_body = pymunk.Body(mass, inertia)
        self.ball_body.position = x, y
        
        self.ball_shape = pymunk.Circle(self.ball_body, BALL_RADIUS)
        self.ball_shape.elasticity = 0.8
        self.ball_shape.friction = 0.5
        self.ball_shape.color = (255, 50, 50, 255)
        self.space.add(self.ball_body, self.ball_shape)

    def create_trail_particle(self):
        """Create a particle that follows the ball"""
        bx, by = self.ball_body.position
        vx, vy = self.ball_body.velocity
        
        offset_x = random.uniform(-3, 3)
        offset_y = random.uniform(-3, 3)
        
        particle_vx = vx * 0.3 + random.uniform(-1, 1)
        particle_vy = vy * 0.3 + random.uniform(-1, 1)
        
        damping = self.space.damping
        blue_amount = int(255 * damping)
        red_amount = int(255 * (1 - damping))
        color = (red_amount, 100, blue_amount)
        
        particle = Particle(bx + offset_x, by + offset_y, particle_vx, particle_vy, color, lifetime=20)
        self.particles.append(particle)

    def create_explosion(self, x, y):
        """Create explosion particles when hitting hazard"""
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            color = random.choice([
                (255, 50, 50),
                (255, 150, 0),
                (255, 255, 0),
            ])
            
            particle = Particle(x, y, vx, vy, color, lifetime=40)
            self.particles.append(particle)

    def check_hazards(self):
        """Check if ball touches any hazard"""
        if self.death_animation:
            return
            
        bx, by = self.ball_body.position
        ball_rect = pygame.Rect(bx - BALL_RADIUS, by - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2)
        
        for hazard in self.hazard_rects:
            if ball_rect.colliderect(hazard):
                self.lives -= 1
                self.save_data["total_deaths"] += 1
                
                if self.lives <= 0:
                    # Game Over
                    self.death_animation = True
                    self.death_timer = 90
                    self.create_explosion(bx, by)
                    self.space.remove(self.ball_body, self.ball_shape)
                else:
                    # Respawn
                    self.death_animation = True
                    self.death_timer = 30
                    self.create_explosion(bx, by)
                    self.space.remove(self.ball_body, self.ball_shape)
                return

    def check_win(self):
        """Check if ball reached goal"""
        if self.death_animation:
            return
            
        bx, by = self.ball_body.position
        if self.goal_rect.collidepoint(bx, by):
            # Create celebratory particles
            for _ in range(20):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(1, 5)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed - 2
                color = (0, 255, 100)
                particle = Particle(bx, by, vx, vy, color, lifetime=30)
                self.particles.append(particle)
            
            # Calculate score
            score = max(0, 10000 - self.level_time * 10)
            level_id = str(self.levels_data[self.current_level_index]['level_id'])
            
            # Save best score
            if level_id not in self.save_data["level_scores"] or score > self.save_data["level_scores"][level_id]:
                self.save_data["level_scores"][level_id] = score
            
            # Unlock next level
            if self.current_level_index + 1 > self.save_data["unlocked_levels"]:
                self.save_data["unlocked_levels"] = self.current_level_index + 1
            
            self.save_data["total_time"] += self.level_time / FPS
            self.save_game()
            
            pygame.time.wait(500)
            self.current_level_index += 1
            self.load_level(self.current_level_index)

    def handle_playing_input(self):
        """Handle input during gameplay"""
        keys = pygame.key.get_pressed()
        
        if not self.paused and not self.death_animation:
            # Gravity Controls
            force = 900
            if keys[pygame.K_UP]:    self.space.gravity = (0, -force)
            elif keys[pygame.K_DOWN]:  self.space.gravity = (0, force)
            elif keys[pygame.K_LEFT]:  self.space.gravity = (-force, 0)
            elif keys[pygame.K_RIGHT]: self.space.gravity = (force, 0)
            
            # Drag Controls
            if keys[pygame.K_w]: self.space.damping = min(1.0, self.space.damping + 0.01)
            if keys[pygame.K_s]: self.space.damping = max(0.1, self.space.damping - 0.01)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.load_level(self.current_level_index)
                elif event.key == pygame.K_ESCAPE:
                    self.paused = not self.paused
            
            if self.paused:
                for button in self.pause_menu_buttons:
                    if button.handle_event(event):
                        if button.text == "Resume":
                            self.paused = False
                        elif button.text == "Restart":
                            self.paused = False
                            self.load_level(self.current_level_index)
                        elif button.text == "Main Menu":
                            self.state = "MAIN_MENU"
                            self.paused = False

    def handle_menu_input(self):
        """Handle input in main menu"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            for button in self.main_menu_buttons:
                if button.handle_event(event):
                    if button.text == "Play":
                        self.load_level(0)
                    elif button.text == "Level Select":
                        self.state = "LEVEL_SELECT"
                    elif button.text == "Statistics":
                        self.state = "STATS"
                    elif button.text == "Quit":
                        self.running = False

    def handle_level_select_input(self):
        """Handle input in level select screen"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = "MAIN_MENU"
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Check level buttons
                for i, level in enumerate(self.levels_data):
                    if i < self.save_data["unlocked_levels"]:
                        row = i // 4
                        col = i % 4
                        x = 100 + col * 150
                        y = 150 + row * 100
                        button_rect = pygame.Rect(x, y, 120, 80)
                        
                        if button_rect.collidepoint(mouse_pos):
                            self.load_level(i)

    def handle_stats_input(self):
        """Handle input in stats screen"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = "MAIN_MENU"

    def update(self):
        if self.state == "PLAYING":
            if self.paused:
                return
            
            if self.death_animation:
                self.death_timer -= 1
                if self.death_timer <= 0:
                    if self.lives <= 0:
                        self.state = "MAIN_MENU"
                    else:
                        # Respawn
                        data = self.levels_data[self.current_level_index]
                        start_x, start_y = data['start_pos']
                        self.create_ball(start_x, start_y)
                        self.death_animation = False
            else:
                self.space.step(1/60.0)
                self.level_time += 1
                self.check_hazards()
                self.check_win()
                
                self.trail_counter += 1
                if self.trail_counter >= 3:
                    self.create_trail_particle()
                    self.trail_counter = 0
            
            # Update particles
            for particle in self.particles[:]:
                particle.update()
                if not particle.is_alive():
                    self.particles.remove(particle)

    def draw_main_menu(self):
        """Draw main menu"""
        self.screen.fill((20, 20, 30))
        
        # Title
        title = self.title_font.render("GRAVITY PUZZLE", True, (100, 200, 255))
        title_rect = title.get_rect(center=(WIDTH//2, 100))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.font.render("Control the Laws of Physics", True, (150, 150, 150))
        subtitle_rect = subtitle.get_rect(center=(WIDTH//2, 150))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Buttons
        for button in self.main_menu_buttons:
            button.draw(self.screen, self.font)

    def draw_level_select(self):
        """Draw level select screen"""
        self.screen.fill((20, 20, 30))
        
        # Title
        title = self.big_font.render("SELECT LEVEL", True, (255, 255, 255))
        title_rect = title.get_rect(center=(WIDTH//2, 50))
        self.screen.blit(title, title_rect)
        
        # Instructions
        inst = self.font.render("Press ESC to go back", True, (150, 150, 150))
        self.screen.blit(inst, (20, 100))
        
        # Level buttons
        for i, level in enumerate(self.levels_data):
            row = i // 4
            col = i % 4
            x = 100 + col * 150
            y = 150 + row * 100
            
            # Check if unlocked
            is_unlocked = i < self.save_data["unlocked_levels"]
            
            # Draw button
            if is_unlocked:
                color = self.get_difficulty_color(level['difficulty'])
            else:
                color = (50, 50, 50)
            
            button_rect = pygame.Rect(x, y, 120, 80)
            pygame.draw.rect(self.screen, color, button_rect, border_radius=10)
            pygame.draw.rect(self.screen, (255, 255, 255), button_rect, 2, border_radius=10)
            
            # Level number
            if is_unlocked:
                level_text = self.font.render(f"Level {level['level_id']}", True, (255, 255, 255))
                name_text = self.font.render(level['name'][:8], True, (200, 200, 200))
                
                # Best score
                level_id = str(level['level_id'])
                if level_id in self.save_data["level_scores"]:
                    score = self.save_data["level_scores"][level_id]
                    score_text = self.font.render(f"{score}", True, (255, 215, 0))
                    self.screen.blit(score_text, (x + 10, y + 55))
            else:
                level_text = self.font.render("LOCKED", True, (100, 100, 100))
                name_text = self.font.render("???", True, (100, 100, 100))
            
            self.screen.blit(level_text, (x + 10, y + 10))
            self.screen.blit(name_text, (x + 10, y + 35))

    def draw_stats(self):
        """Draw statistics screen"""
        self.screen.fill((20, 20, 30))
        
        # Title
        title = self.big_font.render("STATISTICS", True, (255, 255, 255))
        title_rect = title.get_rect(center=(WIDTH//2, 50))
        self.screen.blit(title, title_rect)
        
        # Stats
        stats = [
            f"Levels Unlocked: {self.save_data['unlocked_levels']} / {len(self.levels_data)}",
            f"Total Time Played: {int(self.save_data['total_time'])}s",
            f"Total Deaths: {self.save_data['total_deaths']}",
            f"Levels Completed: {len(self.save_data['level_scores'])}",
        ]
        
        y = 150
        for stat in stats:
            text = self.font.render(stat, True, (255, 255, 255))
            self.screen.blit(text, (WIDTH//2 - 150, y))
            y += 40
        
        # Instructions
        inst = self.font.render("Press ESC to go back", True, (150, 150, 150))
        self.screen.blit(inst, (WIDTH//2 - 100, HEIGHT - 50))

    def draw_playing(self):
        """Draw gameplay screen"""
        self.screen.fill((20, 20, 30))
        
        # Draw Hazards
        pulse = abs(math.sin(pygame.time.get_ticks() / 200))
        hazard_color = (int(150 + 105 * pulse), 0, 0)
        for hazard in self.hazard_rects:
            pygame.draw.rect(self.screen, hazard_color, hazard)
            self.draw_spikes(hazard)
        
        # Draw Goal
        goal_pulse = abs(math.sin(pygame.time.get_ticks() / 300))
        goal_color = (0, int(150 + 105 * goal_pulse), 0)
        pygame.draw.rect(self.screen, goal_color, self.goal_rect)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Draw Physics
        if not self.death_animation:
            self.space.debug_draw(self.draw_options)
        
        # Draw HUD
        level_data = self.levels_data[self.current_level_index]
        ui_text = f"Level {level_data['level_id']}: {level_data['name']} | Time: {self.level_time//FPS}s | Lives: {self.lives}"
        self.screen.blit(self.font.render(ui_text, True, (255, 255, 255)), (20, 20))
        
        controls_text = "Arrows: Gravity | W/S: Density | R: Restart | ESC: Pause"
        self.screen.blit(self.font.render(controls_text, True, (200, 200, 200)), (20, 45))
        
        # Draw death messages
        if self.death_animation:
            if self.lives <= 0:
                death_text = self.big_font.render("GAME OVER!", True, (255, 50, 50))
            else:
                death_text = self.big_font.render(f"RESPAWNING... ({self.lives} lives left)", True, (255, 150, 50))
            text_rect = death_text.get_rect(center=(WIDTH//2, HEIGHT//2))
            self.screen.blit(death_text, text_rect)
        
        # Draw pause menu
        if self.paused:
            # Semi-transparent overlay
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            # Pause title
            pause_text = self.big_font.render("PAUSED", True, (255, 255, 255))
            pause_rect = pause_text.get_rect(center=(WIDTH//2, 120))
            self.screen.blit(pause_text, pause_rect)
            
            # Pause buttons
            for button in self.pause_menu_buttons:
                button.draw(self.screen, self.font)

    def draw_spikes(self, rect):
        """Draw triangular spikes on hazard edges"""
        spike_size = 10
        num_spikes_w = rect.width // spike_size
        num_spikes_h = rect.height // spike_size
        spike_color = (100, 0, 0)
        
        # Top spikes
        for i in range(num_spikes_w):
            x = rect.left + i * spike_size
            points = [(x, rect.top), (x + spike_size, rect.top), (x + spike_size // 2, rect.top - spike_size // 2)]
            pygame.draw.polygon(self.screen, spike_color, points)
        
        # Bottom spikes
        for i in range(num_spikes_w):
            x = rect.left + i * spike_size
            points = [(x, rect.bottom), (x + spike_size, rect.bottom), (x + spike_size // 2, rect.bottom + spike_size // 2)]
            pygame.draw.polygon(self.screen, spike_color, points)

    def get_difficulty_color(self, difficulty):
        """Get color based on difficulty"""
        colors = {
            "easy": (50, 200, 50),
            "medium": (200, 150, 50),
            "hard": (200, 50, 50),
            "insane": (150, 0, 150)
        }
        return colors.get(difficulty.lower(), (100, 100, 100))

    def run(self):
        while self.running:
            # Handle input based on state
            if self.state == "MAIN_MENU":
                self.handle_menu_input()
            elif self.state == "LEVEL_SELECT":
                self.handle_level_select_input()
            elif self.state == "PLAYING":
                self.handle_playing_input()
            elif self.state == "STATS":
                self.handle_stats_input()
            
            # Update
            self.update()
            
            # Draw based on state
            if self.state == "MAIN_MENU":
                self.draw_main_menu()
            elif self.state == "LEVEL_SELECT":
                self.draw_level_select()
            elif self.state == "PLAYING":
                self.draw_playing()
            elif self.state == "STATS":
                self.draw_stats()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = PhysicsGame()
    game.run()