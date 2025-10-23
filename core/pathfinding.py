

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
import csv
import os

class Pathfinding:
    """
    Manages pathfinding and path selection for enemies.

    Keeps a pool of paths for use by enemies. A path is randomly
    selected for each enemy that is spawned. If a path becomes blocked,
    it will be repaired or recalculated. Enemies can switch between 
    paths to continue moving if their current path is being recalculated.
    """

    def __init__(self, game, collision):
        """
        Constructor.

        Args:
            game (Game): The game instance.
            collision (Collision): The collision manager instance.

        """
        
        self.game = game
        self.collision = collision
        self.pool = []
        self.partials = 0
        # Add after self.partials = 0
        self.metrics = {
            "astar": {
                "paths_completed": 0,
                "total_nodes_expanded": 0,
                "total_path_length": 0,
                "paths_attempted": 0
            },
            "greedy": {
                "paths_completed": 0,
                "total_nodes_expanded": 0,
                "total_path_length": 0,
                "paths_attempted": 0
            },
            "dijkstra": {
                "paths_completed": 0,
                "total_nodes_expanded": 0,
                "total_path_length": 0,
                "paths_attempted": 0
            }
        }

    def log_metrics(self):
        """
        Logs current run metrics to a CSV file (tower_metrics.csv)
        """
        algo = getattr(self.game, "pathfinding_algo", "astar")
        metrics = self.metrics[algo]

        # Make file if not exists
        file_exists = os.path.isfile("tower_metrics.csv")
        
        with open("tower_metrics.csv", "a", newline="") as f:
            writer = csv.writer(f)
            # Write header if new file
            if not file_exists:
                writer.writerow([
                    "algorithm",
                    "paths_completed",
                    "nodes_expanded",
                    "total_path_length",
                    "paths_attempted"
                ])
            writer.writerow([
                algo,
                metrics["paths_completed"],
                metrics["total_nodes_expanded"],
                metrics["total_path_length"],
                metrics["paths_attempted"]
            ])

    def precompute(self, count):
        """
        Starts precomputing a given number of paths.

        Args:
            count (int): The number of paths to precompute.

        """
        for i in range(count):
            self.pool.append(Path(self, self.find_start()))

    def find_start(self):
        """
        Finds a start point for a full length path.
        Randomly picked, taking collision into account.

        Returns:
            (int, int): The start position.

        """
        cells = self.collision.height
        x = self.game.window.resolution[0]
        attempts = 100
        
        while attempts > 0:
            attempts -= 1

            y = random.randint(0, cells - 1) * self.collision.tile_size
            if not self.collision.point_blocked(x - 32, y):
                return (x, y)

        # No start found, supply a default.
        return (x, random.randint(0, cells - 1) * self.collision.tile_size)

    def get_point_usage(self, point):
        """
        Returns the number of existing paths that use the given point.

        Args:
            point (int, int): The point to check.

        Returns:
            (int): The number of paths using the given point.

        """
        total = 0

        for path in self.pool:
            if path.done and point in path.points:
                total += 1

        return total
    
    def update(self):
        """
        Continues generating paths.
        Run each frame.
        """
        for path in self.pool:
            if not path.done:
                path.search()
                return

    def get_path(self):
        """
        Picks a path for an enemy to follow.

        Returns:
            A random path (may still be generating).

        """
        attempts = 500
        while attempts > 0:
            attempts -= 1

            path = self.pool[random.randint(self.partials, len(self.pool) - 1)] 
            
            if path.done and path.start[0] >= self.game.window.resolution[0]:
                return path

        return self.get_partial_path(self.find_start())[0]

    def repair(self, point):
        """
        Called when a point has been blocked by a turret.
        Triggers path repair and regeneration (if needed).

        Args:
            point (int, int): The point that is now blocked.

        """
        for path in self.pool:
            # Repair paths that contain the point.
            if path.done and point in path.points:
                path.repair(point)

            # Restart calculations of paths that may include the point.
            if not path.done and (point in path.open_set or point in path.closed_set):
                path.start_search()

    def get_partial_path(self, point):
        """
        Gets or creates a path that starts or passes through the given point.
        Used for enemies that are stuck due to a new turret placement.

        Args:
            start (int, int): The point that the path must include.

        Returns:
            (Path), (int, int): The requested path and the point to move to whilst waiting.

        """
        # Try intersecting paths.
        for path in self.pool:
            if (path.done and point in path.points) or path.start == point:
                return path, point

        # Try paths that intersect with neighbours.
        for neighbour in self.pool[0].get_neighbours(point):
            for path in self.pool:
                if path.done and neighbour in path.points:
                    return path, neighbour

        # No suitable path, make a new one.
        path = Path(self, point)
        self.pool.insert(0, path)
        self.partials += 1
        return path, point

    def is_critical(self, point):
        """
        Works out if blocking the given point may make reaching the finish impossible.
       
        Args:
            point (int, int): The point to check.

        Returns:
            True if the point must be kept clear, otherwise returns False.

        """
        for path in self.pool:
            if path.done and path.start[0] >= self.game.window.resolution[0] and point not in path.points:
                return False

        return True


class Path:
    """
    A single path across the level.
    Calculated using the A* pathfinding algorithm across multiple frames.
    Can be repaired if one of its points becomes blocked.
    """
    def draw_debug(self):
        """
        Draws the A* open and closed sets for debugging.
        Displays open nodes in green, closed nodes in red,
        and the current final path in blue.
        """
        
        if not hasattr(self.pathfinding.game, "window") or not hasattr(self.pathfinding.game.window, "screen"):
            return

        surface = self.pathfinding.game.window.screen
        res = self.res
        
        # Draw open set
        for (x, y) in self.open_set:
            pygame.draw.rect(surface, (0, 255, 0), (x, y, res, res), 1)

        # Draw closed set
        for (x, y) in self.closed_set:
            pygame.draw.rect(surface, (255, 0, 0), (x, y, res, res), 1)

        # Draw path if available
        if self.points:
            for (x, y) in self.points:
                pygame.draw.rect(surface, (0, 0, 255), (x, y, res, res), 1)

    def __init__(self, pathfinding, start):
        """ 
        Constructor. 
        
        Args:
            pathfinding (Pathfinding): The pathfinding manager instance.
            start (int, int): The start position of the path.
        
        """
        self.start = start
        self.pathfinding = pathfinding
        self.collision = self.pathfinding.collision
        self.res = self.collision.tile_size
        self.points = None
        self.start_search()

    def next(self, current):
        """
        Attempts to gets the next point in the path.
        
        Args:
            current (int, int): The current point.

        Returns:
            (int, int) if successful, False if there are no more points in the path.

        """
        if  current not in self.points:
            return False

        index = self.points.index(current)
        length = len(self.points)

        if index + 1 == length:
            return False

        return self.points[index + 1]

    def start_search(self):
        """
        (Re)starts the pathfinding search.
        """
        self.done = False
        self.closed_set = set()
        self.open_set = {self.start}
        self.scores = {self.start: 0}
        self.came_from = { }
    
    def search(self):
        """
        Chooses algorithm based on game setting.
        """
        algo = getattr(self.pathfinding.game, "pathfinding_algo", "astar")
        if algo == "greedy":
            return self.search_greedy()
        elif algo == "dijkstra":
            return self.search_dijkstra()
        else:
            return self.search_astar()
    
    def search_greedy(self):
        """
        Greedy Best First Search implementation.
        Uses only heuristic (no path cost).
        """
        iterations = 25
        nodes_expanded = 0
        while len(self.open_set) > 0 and iterations > 0:
            iterations -= 1
            nodes_expanded += 1

            # Select node with smallest heuristic
            current = min(self.open_set, key=lambda p: self.heuristic(p))

            # Check if goal reached
            if current[0] < 0:
                self.points = self.trace_path(current, self.came_from)
                self.done = True
                # --- ADD METRICS UPDATE ---
                algo = getattr(self.pathfinding.game, "pathfinding_algo", "greedy")
                self.pathfinding.metrics[algo]["paths_completed"] += 1
                self.pathfinding.metrics[algo]["total_nodes_expanded"] += nodes_expanded
                self.pathfinding.metrics[algo]["total_path_length"] += len(self.points)
                self.pathfinding.metrics[algo]["paths_attempted"] += 1
                return

            self.open_set.remove(current)
            self.closed_set.add(current)

            # Explore neighbours
            for neighbour in self.get_neighbours(current):
                if neighbour in self.closed_set:
                    continue

                if neighbour not in self.open_set:
                    self.came_from[neighbour] = current
                    self.open_set.add(neighbour)

        # Optional: visualize each frame
        if hasattr(self.pathfinding, "game") and hasattr(self.pathfinding.game, "window"):
            if self.pathfinding.game.show_path_debug:
                self.draw_debug()

    def search_astar(self):
        """
        Starts or continues an A* search for an appropriate path.
        Draws debug visualization if enabled.
        """
        iterations = 25
        nodes_expanded = 0
        while len(self.open_set) > 0 and iterations > 0:
            iterations -= 1
            nodes_expanded += 1

            # Find the next node to evaluate.
            current, current_score = self.get_lowest_score(self.open_set, self.scores)

            # Check if it is a destination
            if current[0] < 0:
                self.points = self.trace_path(current, self.came_from)
                self.done = True
                # --- ADD METRICS UPDATE ---
                algo = getattr(self.pathfinding.game, "pathfinding_algo", "astar")
                self.pathfinding.metrics[algo]["paths_completed"] += 1
                self.pathfinding.metrics[algo]["total_nodes_expanded"] += nodes_expanded
                self.pathfinding.metrics[algo]["total_path_length"] += len(self.points)
                self.pathfinding.metrics[algo]["paths_attempted"] += 1
                return

            # Remove from the open set and move to closed
            self.open_set.remove(current)
            self.closed_set.add(current)

            # Consider each neighbour
            for neighbour in self.get_neighbours(current):

                # Skip if already in closed set
                if neighbour in self.closed_set:
                    continue

                g = current_score + self.get_cost(current, neighbour)
                h = self.heuristic(neighbour)
                score = g + h
                exists = (neighbour in self.open_set)

                if not exists or self.scores[neighbour] > score:
                    self.scores[neighbour] = score
                    self.came_from[neighbour] = current

                if not exists:
                    self.open_set.add(neighbour)

        #visualize every frame
        if hasattr(self.pathfinding, "game") and hasattr(self.pathfinding.game, "window"):
            if self.pathfinding.game.show_path_debug:
                self.draw_debug()

    def search_dijkstra(self):
        """
        Dijkstra's Algorithm (Uniform Cost Search)
        Finds the shortest path without using a heuristic.
        """
        iterations = 25
        nodes_expanded = 0

        while len(self.open_set) > 0 and iterations > 0:
            iterations -= 1
            nodes_expanded += 1

            # Select node with lowest cost so far (no heuristic)
            current, current_cost = self.get_lowest_score(self.open_set, self.scores)

            # Check if goal reached (left edge)
            if current[0] < 0:
                self.points = self.trace_path(current, self.came_from)
                self.done = True
                algo = "dijkstra"
                self.pathfinding.metrics[algo]["paths_completed"] += 1
                self.pathfinding.metrics[algo]["total_nodes_expanded"] += nodes_expanded
                self.pathfinding.metrics[algo]["total_path_length"] += len(self.points)
                self.pathfinding.metrics[algo]["paths_attempted"] += 1
                return

            # Move from open to closed
            self.open_set.remove(current)
            self.closed_set.add(current)

            # Explore neighbours
            for neighbour in self.get_neighbours(current):
                if neighbour in self.closed_set:
                    continue

                # Dijkstra cost = distance so far + move cost
                new_cost = current_cost + self.get_cost(current, neighbour)
                exists = neighbour in self.open_set

                # If new or cheaper path found
                if not exists or new_cost < self.scores.get(neighbour, float("inf")):
                    self.scores[neighbour] = new_cost
                    self.came_from[neighbour] = current
                    if not exists:
                        self.open_set.add(neighbour)

            #draw visual debug
            if hasattr(self.pathfinding.game, "show_path_debug") and self.pathfinding.game.show_path_debug:
                self.draw_debug()

    
    def heuristic(self, position):
        """
        Heuristic for Greedy Best First Search and A*.
        Uses one of the 3 distance measures from the current position to the left edge (goal area).
        """
        goal = (0, position[1])  
        metric = getattr(self.pathfinding.game, "distance_metric", "manhattan")

        dx = abs(position[0] - goal[0])
        dy = abs(position[1] - goal[1])

        if metric == "euclidean":
            return (dx ** 2 + dy ** 2) ** 0.5
        elif metric == "chebyshev":
            return max(dx, dy)
        else:  # default to full Manhattan
            return dx + dy

    def get_lowest_score(self, open_set, scores):
        """
        Finds the point with the lowest score.
       
        Args:
            open_set (set(int, int)): A set of possible points
            scores (list(int)): A list with the score of each position.

        Returns:
           ((int, int), int) The lowest scoring point and its score.

        """
        lowest_score = 999999999
        lowest_point = (0, 0)

        for p in open_set:
            score = scores[p]

            if lowest_score > score:
                lowest_score = score
                lowest_point = p

        return lowest_point, lowest_score

    def get_neighbours(self, position):
        """
        Finds a list of neighbouring tiles for the given position.

        Args:
            position (int, int): The start position.

        Returns:
            A list of (int, int) tuples.

        """
        if position[0] >=  self.pathfinding.game.window.resolution[0]:
            return [(position[0] - self.res, position[1])]

        x_diff = range(position[0] - self.res, position[0] + self.res + 1, self.res)
        y_diff = range(position[1] - self.res, position[1] + self.res + 1, self.res)

        return [(x, y) for x in x_diff for y in y_diff if (x, y) != position and (x == position[0] or y == position[1] or self.can_use_diagonal(position, (x, y))) and not self.collision.point_blocked(x, y)]
        
    def can_use_diagonal(self, a, b):
        """
        Returns true if the diagonal between a and b is clear.

        Args:
            a (int, int): Position a.
            b (int, int): Position b.

        Returns:
            (bool) True if the diagonal is clear, otherwise False.

        """
        return not self.collision.point_blocked(b[0], a[1]) and not self.collision.point_blocked(a[0], b[1])

    def get_cost(self, a, b):
        """
        Calculates the cost of moving between the given positions.
        
        Args:
            a (int, int): Position a.
            b (int, int): Position b.
            
        Returns:
            (int) The cost of moving from a to b.
          
        """
        base = 3 if a[0] == b[0] or a[1] == b[1] else 4
        crowding = self.pathfinding.get_point_usage(b)

        return base + crowding

    def trace_path(self, current, came_from):
        """
        Traces a finished path from finish to start.

        Args:
            current (int, int): The last position in the path.
            came_from (dict): The location each position was reached from.

        Returns:
            (list(int, int)): A list of points in the path.

        """
        path = [ current ]
        while current in came_from:
            current = came_from[current]
            path.insert(0, current)

        return path

    def repair(self, point):
        """
        Attempts to repair a path after a point is blocked.
        
        Args:
            point (int, int): The blocked point.

        """
        index = self.points.index(point)

        if index != 0 and index < len(self.points) - 1:
            previous = self.points[index - 1]
            next = self.points[index + 1]

            previous_neighbours = self.get_neighbours(previous)
            next_neighbours = self.get_neighbours(next)

            # If next and previous are adjacent, just remove the point.
            if next in previous_neighbours:
                self.points.remove(point)
                return

            # If not, check for a common neighbour.
            for neighbour in previous_neighbours:
                if neighbour in next_neighbours:
                    self.points[index] = neighbour
                    return

            # If not, check neighbours of neighbours.
            for neighbour in previous_neighbours:
                for neighbour_neighbour in self.get_neighbours(neighbour):
                    if neighbour_neighbour in next_neighbours:
                        self.points[index] = neighbour
                        self.points.insert(index + 1, neighbour_neighbour)
                        return

        # No solution, remake path.
        self.start_search()
