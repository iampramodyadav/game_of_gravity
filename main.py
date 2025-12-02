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
CUSTOM_LEVEL_FILE = "custom_level.json"

# --- Helper Classes ---

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
    def __init__(self, x, y, width, height, text, color, hover_color, text_col=(255,255,255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_col = text_col
        self.is_hovered = False
        self.is_pressed = False # For continuous press detection (touch controls)
    
    def draw(self, screen, font):
        color = self.hover_color if (self.is_hovered or self.is_pressed) else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 3, border_radius=10)
        
        if self.text:
            text_surf = font.render(self.text, True, self.text_col)
            text_rect = text_surf.get_rect(center=self.rect.center)
            screen.blit(text_surf, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.is_pressed = False
        return False

class TouchInterface:
    """Handles on-screen controls for mobile/touch"""
    def __init__(self):
        size = 50
        gap = 10
        # D-Pad positioning (Bottom Right)
        base_x = WIDTH - 150
        base_y = HEIGHT - 150
        
        self.btn_up = Button(base_x + size + gap, base_y, size, size, "U", (50, 50, 50), (100, 100, 100))
        self.btn_down = Button(base_x + size + gap, base_y + (size + gap)*2, size, size, "D", (50, 50, 50), (100, 100, 100))
        self.btn_left = Button(base_x, base_y + size + gap, size, size, "L", (50, 50, 50), (100, 100, 100))
        self.btn_right = Button(base_x + (size + gap)*2, base_y + size + gap, size, size, "R", (50, 50, 50), (100, 100, 100))
        
        # Action Buttons (Bottom Left)
        self.btn_w = Button(20, HEIGHT - 120, size, size, "W+", (50, 50, 150), (80, 80, 200)) # Increase density
        self.btn_s = Button(20, HEIGHT - 60, size, size, "S-", (150, 50, 50), (200, 80, 80))  # Decrease density
        
        self.pause_btn = Button(WIDTH - 60, 10, 50, 50, "||", (200, 100, 50), (255, 150, 100))

        self.buttons = [self.btn_up, self.btn_down, self.btn_left, self.btn_right, 
                        self.btn_w, self.btn_s, self.pause_btn]

    def draw(self, screen, font):
        for btn in self.buttons:
            btn.draw(screen, font)

    def handle_event(self, event):
        action = None
        for btn in self.buttons:
            if btn.handle_event(event):
                if btn == self.pause_btn:
                    action = "PAUSE"
        return action

    def get_input_state(self):
        """Returns dict of pressed states mimicking keyboard"""
        return {
            'UP': self.btn_up.is_pressed,
            'DOWN': self.btn_down.is_pressed,
            'LEFT': self.btn_left.is_pressed,
            'RIGHT': self.btn_right.is_pressed,
            'W': self.btn_w.is_pressed,
            'S': self.btn_s.is_pressed
        }

# --- Game Class ---

class PhysicsGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Gravity Puzzle - Enhanced")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        self.big_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        
        # Load Levels
        self.load_levels_from_disk()
        
        # Load save data
        self.load_save_data()
        
        # Game state
        self.state = "MAIN_MENU" 
        self.current_level_index = 0
        self.particles = []
        self.trail_counter = 0
        self.death_animation = False
        self.death_timer = 0
        self.lives = 3
        self.level_time = 0
        self.paused = False
        
        # Multi-ball support
        self.balls = [] # List of dicts: {'body': b, 'shape': s}
        
        # Systems
        self.touch_ui = TouchInterface()
        self.create_menu_buttons()
        
        # Editor State Variables
        self.editor_reset()
        
        self.running = True

    def load_levels_from_disk(self):
        try:
            with open('levels.json', 'r') as f:
                self.levels_data = json.load(f)
        except FileNotFoundError:
            self.levels_data = [] # Should handle gracefully
            print("levels.json not found.")

    def create_menu_buttons(self):
        """Create buttons for different menus"""
        cx = WIDTH // 2
        # Main Menu
        self.main_menu_buttons = [
            Button(cx - 100, 200, 200, 50, "Play", (50, 100, 200), (70, 120, 220)),
            Button(cx - 100, 260, 200, 50, "Level Select", (50, 150, 100), (70, 170, 120)),
            Button(cx - 100, 320, 200, 50, "Level Editor", (200, 100, 50), (220, 120, 70)), # NEW
            Button(cx - 100, 380, 200, 50, "Statistics", (150, 50, 150), (170, 70, 170)),
            Button(cx - 100, 440, 200, 50, "Quit", (200, 50, 50), (220, 70, 70)),
        ]
        
        # Pause Menu
        self.pause_menu_buttons = [
            Button(cx - 100, 200, 200, 50, "Resume", (50, 200, 50), (70, 220, 70)),
            Button(cx - 100, 270, 200, 50, "Restart", (200, 150, 50), (220, 170, 70)),
            Button(cx - 100, 340, 200, 50, "Main Menu", (100, 100, 200), (120, 120, 220)),
        ]
        self.main_menu_button = [
            Button(WIDTH-90, 10, 80, 40, "Main Menu", (150, 50, 50), (200, 80, 80))
        ]
        # Editor Buttons
        self.editor_buttons = [
            Button(10, 10, 80, 40, "Wall", (100, 100, 100), (150, 150, 150)),
            Button(100, 10, 80, 40, "Hazard", (150, 50, 50), (200, 80, 80)),
            Button(190, 10, 80, 40, "Start", (50, 50, 150), (80, 80, 200)),
            Button(280, 10, 80, 40, "Goal", (50, 150, 50), (80, 200, 80)),
            Button(WIDTH-180, 10, 80, 40, "Save", (50, 150, 150), (80, 200, 200)),
            Button(WIDTH-90, 10, 80, 40, "Exit", (150, 50, 50), (200, 80, 80)),
            Button(WIDTH-180, 60, 80, 40, "Load Custom", (100, 100, 150), (130, 130, 200)),
            Button(WIDTH-90, 60, 80, 40, "Clear", (100, 100, 100), (130, 130, 130))
        ]

    def load_save_data(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                self.save_data = json.load(f)
        else:
            self.save_data = {"unlocked_levels": 1, "level_scores": {}, "total_time": 0, "total_deaths": 0}
            self.save_game()
    
    def save_game(self):
        with open(SAVE_FILE, 'w') as f:
            json.dump(self.save_data, f, indent=2)

    def load_level(self, index, custom_data=None):
        """Loads a level. If custom_data is provided, uses that instead of index."""
        if index >= len(self.levels_data):
            self.state = "STATS"
            return

        if custom_data:
            data = custom_data
            self.current_level_index = -1 # Indicator for custom level
        elif index < len(self.levels_data):
            data = self.levels_data[index]
            self.current_level_index = index
        else:
            self.state = "STATS"
            return

        # Reset State
        self.particles = []
        self.death_animation = False
        self.death_timer = 0
        self.lives = data.get('lives', 3)
        self.level_time = 0
        self.balls = [] # Clear old balls

        # Physics Setup
        self.space = pymunk.Space()
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.space.gravity = tuple(data['gravity_start'])
        self.space.damping = data['damping_start']
        
        # Objects
        self.goal_rect = pygame.Rect(data['goal_rect'])
        self.create_boundary()
        
        for w in data['walls']:
            self.create_block(w[0], w[1], w[2], w[3])

        self.hazard_rects = []
        if 'hazards' in data:
            for h in data['hazards']:
                self.hazard_rects.append(pygame.Rect(h[0], h[1], h[2], h[3]))

        # Multi-Ball Spawning Logic
        start_pos = data['start_pos']
        # Check if it's a list of lists (Multiple balls) or just [x, y]
        if isinstance(start_pos[0], list):
            for pos in start_pos:
                self.create_ball(pos[0], pos[1])
        else:
            self.create_ball(start_pos[0], start_pos[1])
        
        self.state = "PLAYING"

    def create_boundary(self):
        walls = [(0, 0, WIDTH, 10), (0, HEIGHT-10, WIDTH, 10), (0, 0, 10, HEIGHT), (WIDTH-10, 0, 10, HEIGHT)]
        for x, y, w, h in walls:
            self.create_block(x, y, w, h)

    def create_block(self, x, y, w, h):
        center_x, center_y = x + w / 2, y + h / 2
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = (center_x, center_y)
        shape = pymunk.Poly.create_box(body, (w, h))
        shape.elasticity, shape.friction = 0.8, 0.5
        shape.color = (150, 150, 150, 255)
        self.space.add(body, shape)

    def create_ball(self, x, y):
        mass, radius = 10, BALL_RADIUS
        inertia = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, inertia)
        body.position = x, y
        shape = pymunk.Circle(body, radius)
        shape.elasticity, shape.friction = 0.8, 0.5
        shape.color = (255, 50, 50, 255)
        self.space.add(body, shape)
        self.balls.append({'body': body, 'shape': shape})

    # --- Particle Effects ---
    def create_trail_particle(self, body):
        bx, by = body.position
        vx, vy = body.velocity
        damping = self.space.damping
        color = (int(255*(1-damping)), 100, int(255*damping))
        p = Particle(bx + random.uniform(-3,3), by + random.uniform(-3,3), 
                     vx*0.3 + random.uniform(-1,1), vy*0.3 + random.uniform(-1,1), color, 20)
        self.particles.append(p)

    def create_explosion(self, x, y):
        for _ in range(20):
            angle = random.uniform(0, 6.28)
            speed = random.uniform(2, 8)
            p = Particle(x, y, math.cos(angle)*speed, math.sin(angle)*speed, (255, 100, 0), 40)
            self.particles.append(p)

    # --- Game Logic ---
    def check_hazards(self):
        if self.death_animation: return
        
        hit = False
        for ball in self.balls[:]:
            bx, by = ball['body'].position
            ball_rect = pygame.Rect(bx - BALL_RADIUS, by - BALL_RADIUS, BALL_RADIUS*2, BALL_RADIUS*2)
            
            for hazard in self.hazard_rects:
                if ball_rect.colliderect(hazard):
                    hit = True
                    self.create_explosion(bx, by)
                    self.space.remove(ball['body'], ball['shape'])
                    self.balls.remove(ball)
                    break 
        
        if hit:
            self.lives -= 1
            self.save_data["total_deaths"] += 1
            # If any ball dies, reset logic
            self.death_animation = True
            self.death_timer = 90 if self.lives <= 0 else 30

    def check_win(self):
        if self.death_animation or not self.balls: return

        all_in_goal = True
        for ball in self.balls:
            bx, by = ball['body'].position
            if not self.goal_rect.collidepoint(bx, by):
                all_in_goal = False
                break
        
        if all_in_goal:
            # Win!
            score = max(0, 10000 - self.level_time * 10)
            if self.current_level_index != -1: # Don't save stats for custom levels
                lvl_id = str(self.levels_data[self.current_level_index]['level_id'])
                if lvl_id not in self.save_data["level_scores"] or score > self.save_data["level_scores"][lvl_id]:
                    self.save_data["level_scores"][lvl_id] = score
                if self.current_level_index + 1 > self.save_data["unlocked_levels"]:
                    self.save_data["unlocked_levels"] = self.current_level_index + 1
                self.save_data["total_time"] += self.level_time / FPS
                self.save_game()
                self.current_level_index += 1
                print('WIN')
                self.load_level(self.current_level_index)
            else:
                # Custom level win -> just go to menu
                self.state = "MAIN_MENU"

    # --- Input Handling ---
    def handle_playing_input(self):
        keys = pygame.key.get_pressed()
        touch_state = self.touch_ui.get_input_state()
        
        if not self.paused and not self.death_animation:
            force = 900
            if keys[pygame.K_UP] or touch_state['UP']:    self.space.gravity = (0, -force)
            elif keys[pygame.K_DOWN] or touch_state['DOWN']:  self.space.gravity = (0, force)
            elif keys[pygame.K_LEFT] or touch_state['LEFT']:  self.space.gravity = (-force, 0)
            elif keys[pygame.K_RIGHT] or touch_state['RIGHT']: self.space.gravity = (force, 0)
            
            if keys[pygame.K_w] or touch_state['W']: self.space.damping = min(1.0, self.space.damping + 0.01)
            if keys[pygame.K_s] or touch_state['S']: self.space.damping = max(0.1, self.space.damping - 0.01)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            
            # Handle Touch UI events
            ui_action = self.touch_ui.handle_event(event)
            if ui_action == "PAUSE": self.paused = not self.paused

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r: 
                    if self.current_level_index == -1: self.load_level(-1, self.loaded_custom_data)
                    else: self.load_level(self.current_level_index)
                elif event.key == pygame.K_ESCAPE: self.paused = not self.paused
            
            if self.paused:
                for button in self.pause_menu_buttons:
                    if button.handle_event(event):
                        if button.text == "Resume": self.paused = False
                        elif button.text == "Restart": 
                            self.paused = False
                            if self.current_level_index == -1: self.load_level(-1, self.loaded_custom_data)
                            else: self.load_level(self.current_level_index)
                        elif button.text == "Main Menu": 
                            self.state = "MAIN_MENU"
                            self.paused = False

    # --- Editor Logic ---
    def editor_reset(self):
        self.editor_walls = []
        self.editor_hazards = []
        self.editor_start = [100, 100]
        self.editor_goal = [600, 400, 80, 80]
        self.editor_tool = "Wall" # Wall, Hazard, Start, Goal
        self.drag_start = None
        self.loaded_custom_data = None # Stores data for "Play Custom"

    def handle_editor_input(self):
        mouse_pos = pygame.mouse.get_pos()
        # Snap to grid
        grid_size = 10
        snapped_pos = (round(mouse_pos[0]/grid_size)*grid_size, round(mouse_pos[1]/grid_size)*grid_size)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            
            # Handle Toolbar
            if event.type == pygame.MOUSEBUTTONDOWN and mouse_pos[1] < 60: # UI Area
                for btn in self.editor_buttons:
                    if btn.handle_event(event):
                        if btn.text in ["Wall", "Hazard", "Start", "Goal"]:
                            self.editor_tool = btn.text
                        elif btn.text == "Exit": self.state = "MAIN_MENU"
                        elif btn.text == "Clear": self.editor_reset()
                        elif btn.text == "Save": self.save_custom_level()
                        elif btn.text == "Load Custom": self.load_custom_level()
                continue
            
            # Handle Drawing
            if event.type == pygame.MOUSEBUTTONDOWN and mouse_pos[1] > 60:
                if self.editor_tool == "Start":
                    self.editor_start = list(snapped_pos)
                else:
                    self.drag_start = snapped_pos

            elif event.type == pygame.MOUSEBUTTONUP and self.drag_start:
                x = min(self.drag_start[0], snapped_pos[0])
                y = min(self.drag_start[1], snapped_pos[1])
                w = abs(self.drag_start[0] - snapped_pos[0])
                h = abs(self.drag_start[1] - snapped_pos[1])
                
                if w > 0 and h > 0:
                    rect = [x, y, w, h]
                    if self.editor_tool == "Wall": self.editor_walls.append(rect)
                    elif self.editor_tool == "Hazard": self.editor_hazards.append(rect)
                    elif self.editor_tool == "Goal": self.editor_goal = rect
                
                self.drag_start = None

    def save_custom_level(self):
        level_data = {
            "level_id": 999,
            "name": "Custom Level",
            "difficulty": "custom",
            "lives": 3,
            "start_pos": self.editor_start,
            "gravity_start": [0, 900],
            "damping_start": 0.9,
            "goal_rect": self.editor_goal,
            "walls": self.editor_walls,
            "hazards": self.editor_hazards
        }
        with open(CUSTOM_LEVEL_FILE, 'w') as f:
            json.dump(level_data, f)
        print("Level Saved!")

    def load_custom_level(self):
        if os.path.exists(CUSTOM_LEVEL_FILE):
            with open(CUSTOM_LEVEL_FILE, 'r') as f:
                self.loaded_custom_data = json.load(f)
            self.load_level(-1, self.loaded_custom_data)

    def draw_editor(self):
        self.screen.fill((30, 30, 40))
        
        # Grid
        for x in range(0, WIDTH, 50): pygame.draw.line(self.screen, (40,40,50), (x,0), (x,HEIGHT))
        for y in range(0, HEIGHT, 50): pygame.draw.line(self.screen, (40,40,50), (0,y), (WIDTH,y))

        # Objects
        for w in self.editor_walls: pygame.draw.rect(self.screen, (150, 150, 150), w)
        for h in self.editor_hazards: pygame.draw.rect(self.screen, (150, 50, 50), h)
        pygame.draw.rect(self.screen, (50, 150, 50), self.editor_goal)
        pygame.draw.circle(self.screen, (50, 50, 200), self.editor_start, 15)

        # Drag Preview
        if self.drag_start:
            mp = pygame.mouse.get_pos()
            gp = (round(mp[0]/10)*10, round(mp[1]/10)*10)
            x = min(self.drag_start[0], gp[0])
            y = min(self.drag_start[1], gp[1])
            w = abs(self.drag_start[0] - gp[0])
            h = abs(self.drag_start[1] - gp[1])
            color = (255,255,255)
            if self.editor_tool == "Hazard": color = (255, 100, 100)
            elif self.editor_tool == "Goal": color = (100, 255, 100)
            pygame.draw.rect(self.screen, color, (x,y,w,h), 2)

        # UI Bar
        pygame.draw.rect(self.screen, (20,20,30), (0,0,WIDTH,60))
        for btn in self.editor_buttons:
            # Highlight selected tool
            if btn.text == self.editor_tool:
                pygame.draw.rect(self.screen, (255,255,0), btn.rect, 3)
            btn.draw(self.screen, self.font)

    # --- Main Loop Integration ---

    def update(self):
        if self.state == "PLAYING":
            if self.paused: return
            
            if self.death_animation:
                self.death_timer -= 1
                if self.death_timer <= 0:
                    if self.lives <= 0:
                        self.state = "MAIN_MENU"
                    else:
                        # Respawn
                        if self.current_level_index == -1:
                            self.load_level(-1, self.loaded_custom_data)
                        else:
                            self.load_level(self.current_level_index)
            else:
                self.space.step(1/60.0)
                self.level_time += 1
                self.check_hazards()
                self.check_win()
                
                self.trail_counter += 1
                if self.trail_counter >= 3:
                    for ball in self.balls:
                        self.create_trail_particle(ball['body'])
                    self.trail_counter = 0
            
            for particle in self.particles[:]:
                particle.update()
                if not particle.is_alive():
                    self.particles.remove(particle)

    def draw_playing(self):
        self.screen.fill((20, 20, 30))
        
        # Visuals
        pulse = abs(math.sin(pygame.time.get_ticks() / 200))
        hazard_color = (int(150 + 105 * pulse), 0, 0)
        for h in self.hazard_rects:
            pygame.draw.rect(self.screen, hazard_color, h)
            # Simple spikes
            for i in range(0, h.width, 10):
                pygame.draw.line(self.screen, (100,0,0), (h.left+i, h.top), (h.left+i+5, h.top-5))
                pygame.draw.line(self.screen, (100,0,0), (h.left+i+5, h.top-5), (h.left+i+10, h.top))
        
        pygame.draw.rect(self.screen, (0, int(150 + 105 * abs(math.sin(pygame.time.get_ticks()/300))), 0), self.goal_rect)
        
        for p in self.particles: p.draw(self.screen)
        if not self.death_animation: self.space.debug_draw(self.draw_options)
        
        # HUD
        if self.current_level_index >= len(self.levels_data):
            self.state = "STATS"
            return
        if self.current_level_index != -1:
            lvl_data = self.levels_data[self.current_level_index]
            name = lvl_data['name']
            lid = lvl_data['level_id']
        else:
            name = "Custom Level"
            lid = "?"
            
        ui_text = f"Level {lid}: {name} | Time: {self.level_time//FPS}s | Lives: {self.lives}"
        self.screen.blit(self.font.render(ui_text, True, (255, 255, 255)), (20, 20))
        
        # Draw Touch Controls
        self.touch_ui.draw(self.screen, self.font)

        # Pause/Death Overlay
        if self.death_animation:
            txt = "GAME OVER" if self.lives <= 0 else f"RESPAWNING... ({self.lives})"
            color = (255, 50, 50) if self.lives <= 0 else (255, 150, 50)
            surf = self.big_font.render(txt, True, color)
            self.screen.blit(surf, surf.get_rect(center=(WIDTH//2, HEIGHT//2)))

        if self.paused:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            self.screen.blit(self.big_font.render("PAUSED", True, (255,255,255)), (WIDTH//2 - 60, 120))
            for b in self.pause_menu_buttons: b.draw(self.screen, self.font)

    # --- State Management ---
    def handle_menu_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            for btn in self.main_menu_buttons:
                if btn.handle_event(event):
                    if btn.text == "Play": self.load_level(0)
                    elif btn.text == "Level Select": self.state = "LEVEL_SELECT"
                    elif btn.text == "Level Editor": self.state = "EDITOR"
                    elif btn.text == "Statistics": self.state = "STATS"
                    elif btn.text == "Quit": self.running = False

    def handle_level_select_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: self.state = "MAIN_MENU"
            if event.type == pygame.MOUSEBUTTONDOWN:
                mp = pygame.mouse.get_pos()
                for i in range(len(self.levels_data)):
                    if i < self.save_data["unlocked_levels"]:
                        row, col = i // 4, i % 4
                        rect = pygame.Rect(100 + col * 150, 150 + row * 100, 120, 80)
                        if rect.collidepoint(mp): self.load_level(i)

            for btn in self.main_menu_button:
                            if btn.handle_event(event):
                                if btn.text == "Main Menu":
                                    self.state = "MAIN_MENU"

    def draw_main_menu(self):
        self.screen.fill((20, 20, 30))
        t = self.title_font.render("GRAVITY PUZZLE", True, (100, 200, 255))
        self.screen.blit(t, t.get_rect(center=(WIDTH//2, 100)))
        for b in self.main_menu_buttons: b.draw(self.screen, self.font)

    def draw_level_select(self):
        self.screen.fill((20, 20, 30))
        self.screen.blit(self.big_font.render("SELECT LEVEL", True, (255,255,255)), (WIDTH//2-100, 50))
        for i, lvl in enumerate(self.levels_data):
            row, col = i // 4, i % 4
            x, y = 100 + col * 150, 150 + row * 100
            unlocked = i < self.save_data["unlocked_levels"]
            colr = (50, 200, 50) if unlocked else (50, 50, 50)
            pygame.draw.rect(self.screen, colr, (x, y, 120, 80), border_radius=10)
            if unlocked:
                self.screen.blit(self.font.render(str(lvl['level_id']), True, (255,255,255)), (x+10, y+10))

        for btn in self.main_menu_button:
            btn.draw(self.screen, self.font)

    def draw_stats(self):
        self.screen.fill((20, 20, 30))
        # Simple stats render
        self.screen.blit(self.big_font.render("STATS", True, (255,255,255)), (WIDTH//2-50, 50))
        lines = [f"Deaths: {self.save_data['total_deaths']}", f"Unlocked: {self.save_data['unlocked_levels']}"]
        for i, l in enumerate(lines):
            self.screen.blit(self.font.render(l, True, (255,255,255)), (WIDTH//2-50, 150+i*40))
        self.screen.blit(self.font.render("ESC to return", True, (150,150,150)), (WIDTH//2-50, HEIGHT-50))
        for btn in self.main_menu_button:
            btn.draw(self.screen, self.font)
    def handle_stats_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: self.state = "MAIN_MENU"
            for btn in self.main_menu_button:
                            if btn.handle_event(event):
                                if btn.text == "Main Menu":
                                    self.state = "MAIN_MENU"
    def run(self):
        while self.running:
            if self.state == "MAIN_MENU":
                self.handle_menu_input()
                self.draw_main_menu()
            elif self.state == "LEVEL_SELECT":
                self.handle_level_select_input()
                self.draw_level_select()
            elif self.state == "PLAYING":
                self.handle_playing_input()
                self.update()
                self.draw_playing()
            elif self.state == "EDITOR":
                self.handle_editor_input()
                self.draw_editor()
            elif self.state == "STATS":
                self.handle_stats_input()
                self.draw_stats()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    game = PhysicsGame()
    game.run()
