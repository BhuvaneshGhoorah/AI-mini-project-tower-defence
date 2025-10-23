

###########################################
#
# COMP 1551
# Core Programming
#
# Coursework 2 - Mini Project
#
# George Loines
# 200836065
#
# 02 Feb 2015
#
###########################################


import random
import pygame
import time
from core.level import Level
from core.collision import Collision
from core.defence import Defence
from core.enemy import Enemy
from core.wave import Wave
from core.menu import Menu
from core.prefab import Prefab


class Game:
    """ 
    Contains the main control code and the game loop.
    """
    def __init__(self, window):
        """ 
        Constructor. 
        
        Args:
            window (Window): The window instance to render to.
        """
        self.show_path_debug = False
        self._logged_towers = None

        self.window = window
        self.clock = pygame.time.Clock()
        self.defences = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()
        self.load_level("basic")
        self.defence_type = 0
        self.defence_prototypes = [
            Defence(self, "defence_" + name, -100, -100)
            for name in ["pillbox", "wall", "mines", "artillery"]
        ]

        # --- NEW LOGGING INITIALIZATION ---
        self._start_time = time.time()
        self.game_started = False
        # reset the log file each run
        #with open("tower_log.csv", "w") as f:
        #    f.write("time,action,tile_x,tile_y\n")

        #Choose default algorithm to run when playing
        self.pathfinding_algo = "astar"  #possible values {greedy, astar, dijkstra}
        self.distance_metric = "manhattan"  #possible values {manhattan, euclidean, chebyshev}
        #We determined that these combinations of algo + distance measure are the best:
        #{astar with manhattan, greedy with euclidean, dijkstra with euclidean} {and the overall BEST algo is astar with manhattan}

    def load_level(self, name):
        """
        Loads a new level.

        Args:
            name (str): The name of the level (case sensitive).

        """
        self.defences.empty()
        self.bullets.empty()
        self.explosions.empty()
        self.level = Level(self, name)
        self.wave = Wave(self, 1)
        self.menu = Menu(self)

    def run(self):
        """ 
        Runs the main game loop. 
        """
        self.running = True

        while self.running:
            delta = self.clock.tick(60) / 1000.0
            
            # Look for a quit event
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.menu.visible:
                        self.place_defence(pygame.mouse.get_pos())
                    self.menu.clicked()
                elif event.type == pygame.KEYDOWN:
                    self.menu.key_pressed(event.key)
                    if event.key == pygame.K_v:
                        print(f"Key pressed: {event.key}")
                        self.show_path_debug = not self.show_path_debug
                    

            if not self.menu.visible:
                if not self.game_started:
                    self._start_time = time.time()
                    self.game_started = True
                    print("Game timer started!")

            elapsed = time.time() - self._start_time
            self.replay_tower_placements(elapsed)

            # Call update functions
            self.menu.update()
            self.level.pathfinding.update()

            if not self.menu.visible:
                self.level.time += delta
                self.defences.update(delta)
                self.bullets.update(delta)
                self.explosions.update(delta)

                self.wave.update(delta)
                if self.wave.done:
                    self.wave = Wave(self, self.wave.number + 1)

            # Redraw graphics
            self.window.clear()
            self.level.prefabs.draw(self.window.screen)
            self.defences.draw(self.window.screen)
            self.bullets.draw(self.window.screen)
            self.wave.enemies.draw(self.window.screen)
            self.explosions.draw(self.window.screen)
            self.menu.draw(self.window.screen)

            # --- PATHFINDING DEBUG VISUALIZATION ---
            if self.show_path_debug:
                for path in self.level.pathfinding.pool:
                    if hasattr(path, "draw_debug"):
                        path.draw_debug()

            # Menu and HUD last (on top)
            self.menu.draw(self.window.screen)

    def quit(self):
        """
        Quits and closes the game.
        """
        # --- LOG METRICS ---
        if hasattr(self.level, "pathfinding"):
            self.level.pathfinding.log_metrics()
        self.running = False

    def select_defence(self, type):
        """
        Picks a defence type for placement.

        Args:
            type (int): The index of the selcted defence type.

        """
        self.defence_type = type

    def place_defence(self, position):
        """
        Attempts to place a defence at the given position.

        Args:
            position (int, int): The intended coordinates of the defence.
        """
        if self.defence_type < 0:
            return

        defence = self.defence_prototypes[self.defence_type]

        if self.level.money < defence.cost:
            return

        x = position[0] - position[0] % 32
        y = position[1] - position[1] % 32

        # Stop if the defence would intersect with the level.
        if self.level.collision.rect_blocked(x, y, defence.rect.width - 2, defence.rect.height - 2):
            return

        # Stop if the defence may lead no path for enemies.
        if hasattr(defence, "block") and self.level.pathfinding.is_critical((x, y)):
            return

        self.defences.add(Defence(self, defence.name, x, y))
        self.level.money -= defence.cost

        # --- NEW LOGGING ---
        tile_x = x // 32
        tile_y = y // 32
        #self.log_tower_event(defence.name, tile_x, tile_y)

    def log_tower_event(self, action, tile_x, tile_y):
        """Logs tower placement/removal events with timestamp."""
        import time
        t = round(time.time() - self._start_time, 3)
        with open("tower_log.csv", "a") as f:
            f.write(f"{t},{action},{tile_x},{tile_y}\n")
    
    def replay_tower_placements(self, elapsed_time):
        """
        Reads tower_log.csv and automatically places logged defences at the recorded time.
        Only places towers whose timestamps are <= elapsed_time and not yet placed.
        """
        import csv

        # Load file only once
        if self._logged_towers is None:
            print("[Replay] Loading tower_log.csv...")
            self._logged_towers = []
            try:
                with open("tower_log.csv", "r") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            t = float(row["time"])
                            name = row["action"]
                            x = int(row["tile_x"])
                            y = int(row["tile_y"])
                            self._logged_towers.append({"time": t, "name": name, "x": x, "y": y, "done": False})
                        except Exception as e:
                            print("Error reading log line:", e)
            except FileNotFoundError:
                print("No tower_log.csv found; skipping replay.")
                self._logged_towers = []

        # Only process if timer has started
        if not self.game_started or self._start_time is None:
            return

        # Check which towers to place
        for tower in self._logged_towers:
            if not tower["done"] and elapsed_time >= tower["time"]:
                px = tower["x"] * 32
                py = tower["y"] * 32
                self.defences.add(Defence(self, tower["name"], px, py))
                tower["done"] = True
                print(f"[Replay] Replayed {tower['name']} at ({tower['x']}, {tower['y']})")
