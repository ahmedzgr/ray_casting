"""
Logic module for the 2D ray tracing introduction project.
Contains map loading, player movement, rotation, and view area calculations.
"""

import math
import random
from typing import List, Tuple


# Map tile constants
EMPTY = 0
WALL = 1


def load_map(filepath: str) -> List[List[int]]:
    """Load a grid map from a text file.
    
    Args:
        filepath: Path to the map file.
        
    Returns:
        2D list of integers (0=empty, 1=wall).
    """
    grid = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                row = [int(char) for char in line]
                grid.append(row)
    return grid


class Player:
    """Player entity with position, angle, and movement capabilities."""
    
    def __init__(self, x: float, y: float, angle: float = 0.0):
        """Initialize player at position (x, y) with facing angle in radians.
        
        Args:
            x: Initial x coordinate (world space).
            y: Initial y coordinate (world space).
            angle: Initial facing angle in radians (0 = right, pi/2 = down).
        """
        self.x = x
        self.y = y
        self.angle = angle  # radians
        
        # Movement settings
        self.move_speed = 0.05
        self.rot_speed = 0.05
        
        # Field of view settings
        self.fov = math.pi / 2.5  # ~72 degrees
        self.num_rays = 180
        
        # Ray casting settings
        self.ray_max_dist = 50.0
        
    def rotate(self, direction: int):
        """Rotate the player's view.
        
        Args:
            direction: -1 for left, +1 for right.
        """
        self.angle += direction * self.rot_speed
        
    def move(self, dx: float, dy: float, grid: List[List[int]], tile_size: float):
        """Attempt to move player by (dx, dy) with collision detection.
        
        Args:
            dx: Delta x movement.
            dy: Delta y movement.
            grid: The game map grid.
            tile_size: Size of each grid tile in world units.
        """
        # Try moving on x axis
        new_x = self.x + dx
        if not self._check_collision(new_x, self.y, grid, tile_size):
            self.x = new_x
            
        # Try moving on y axis
        new_y = self.y + dy
        if not self._check_collision(self.x, new_y, grid, tile_size):
            self.y = new_y
            
    def _check_collision(self, x: float, y: float, grid: List[List[int]], tile_size: float) -> bool:
        """Check if position collides with a wall.
        
        Args:
            x: X coordinate to check.
            y: Y coordinate to check.
            grid: The game map grid.
            tile_size: Size of each grid tile in world units.
            
        Returns:
            True if collision detected.
        """
        # Check with a small collision radius around player
        radius = tile_size * 0.2
        
        for offset_x in [-radius, 0, radius]:
            for offset_y in [-radius, 0, radius]:
                check_x = x + offset_x
                check_y = y + offset_y
                
                tile_x = int(check_x / tile_size)
                tile_y = int(check_y / tile_size)
                
                if 0 <= tile_y < len(grid) and 0 <= tile_x < len(grid[0]):
                    if grid[tile_y][tile_x] == WALL:
                        return True
                else:
                    # Out of bounds = collision
                    return True
        return False
        
    def cast_rays(self, grid: List[List[int]], tile_size: float) -> List[Tuple[float, float, float, int]]:
        """Cast rays from player to determine visible area.
        
        Args:
            grid: The game map grid.
            tile_size: Size of each grid tile in world units.
            
        Returns:
            List of (end_x, end_y, distance, side) tuples for each ray.
                end_x, end_y: Ray endpoint in world coordinates.
                distance: Perpendicular distance to wall (for 3D rendering).
                side: 0 for x-side hit, 1 for y-side hit (for wall shading).
        """
        rays = []
        half_fov = self.fov / 2
        
        for ray_idx in range(self.num_rays):
            # Calculate ray angle
            ray_offset = (ray_idx / (self.num_rays - 1) - 0.5) * self.fov
            ray_angle = self.angle + ray_offset
            
            # Cast ray
            end_x, end_y, distance, side = self._cast_single_ray(ray_angle, grid, tile_size)
            rays.append((end_x, end_y, distance, side))
            
        return rays
        
    def _cast_single_ray(self, angle: float, grid: List[List[int]], tile_size: float) -> Tuple[float, float, float, int]:
        """Cast a single ray and return its endpoint with distance info.
        
        Args:
            angle: Ray direction angle in radians.
            grid: The game map grid.
            tile_size: Size of each grid tile in world units.
            
        Returns:
            (end_x, end_y, distance, side) tuple.
        """
        # DDA ray casting algorithm
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)
        
        # Starting tile
        map_x = int(self.x / tile_size)
        map_y = int(self.y / tile_size)
        
        # Step direction
        step_x = 1 if cos_a > 0 else -1
        step_y = 1 if sin_a > 0 else -1
        
        # Length of ray from current position to next x or y-side
        if cos_a != 0:
            delta_dist_x = abs(1 / cos_a)
        else:
            delta_dist_x = float('inf')
        if sin_a != 0:
            delta_dist_y = abs(1 / sin_a)
        else:
            delta_dist_y = float('inf')
        
        # Calculate initial side distances
        if cos_a > 0:
            side_dist_x = (map_x + 1 - self.x / tile_size) * delta_dist_x
        else:
            side_dist_x = (self.x / tile_size - map_x) * delta_dist_x
        if sin_a > 0:
            side_dist_y = (map_y + 1 - self.y / tile_size) * delta_dist_y
        else:
            side_dist_y = (self.y / tile_size - map_y) * delta_dist_y
        
        # DDA loop
        hit = False
        side = 0  # 0 for x-side hit, 1 for y-side hit
        
        while not hit:
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1
                
            # Check bounds and collision
            if map_y < 0 or map_y >= len(grid) or map_x < 0 or map_x >= len(grid[0]):
                hit = True
            elif grid[map_y][map_x] == WALL:
                hit = True
                
        # Calculate exact hit position
        if side == 0:
            perp_dist = (map_x - self.x / tile_size + (1 - step_x) / 2) / cos_a if cos_a != 0 else 0
        else:
            perp_dist = (map_y - self.y / tile_size + (1 - step_y) / 2) / sin_a if sin_a != 0 else 0
            
        # Clamp distance
        perp_dist = max(0, min(perp_dist, self.ray_max_dist))
        
        end_x = self.x + cos_a * perp_dist * tile_size
        end_y = self.y + sin_a * perp_dist * tile_size
        
        return (end_x, end_y, perp_dist * tile_size, side)


class GameState:
    """Holds the overall game state including map and player."""
    
    def __init__(self, map_filepath: str, tile_size: float = 50.0):
        """Initialize game state.
        
        Args:
            map_filepath: Path to the map file.
            tile_size: Size of each tile in world units (pixels).
        """
        self.grid = load_map(map_filepath)
        self.tile_size = tile_size
        
        # Find starting position (first empty cell)
        start_found = False
        for y in range(len(self.grid)):
            for x in range(len(self.grid[0])):
                if self.grid[y][x] == EMPTY:
                    # Start in center of tile
                    self.player = Player(
                        x * tile_size + tile_size / 2,
                        y * tile_size + tile_size / 2,
                        -math.pi / 2  # Facing up initially
                    )
                    start_found = True
                    break
            if start_found:
                break
                
        if not start_found:
            # Default start position
            self.player = Player(tile_size * 1.5, tile_size * 1.5, -math.pi / 2)
            
        # Bullet marks (list of (x, y) world coordinates where bullets hit)
        self.bullet_marks = []
        
        # Dummies (list of (x, y) world coordinates)
        self.dummies = []
        self.num_dummies = 5  # Number of dummies to spawn
        self.spawn_dummies()
        
    def spawn_dummies(self):
        """Spawn dummies at random empty positions in the map."""
        self.dummies = []
        
        # Find all empty cells
        empty_cells = []
        for y in range(len(self.grid)):
            for x in range(len(self.grid[0])):
                if self.grid[y][x] == EMPTY:
                    empty_cells.append((x, y))
                    
        # Shuffle and take first N (avoiding player start area)
        random.shuffle(empty_cells)
        
        # Filter out cells too close to player start
        start_tile_x = int(self.player.x / self.tile_size)
        start_tile_y = int(self.player.y / self.tile_size)
        
        for tile_x, tile_y in empty_cells:
            if len(self.dummies) >= self.num_dummies:
                break
            # Don't spawn too close to start
            if abs(tile_x - start_tile_x) > 2 or abs(tile_y - start_tile_y) > 2:
                # Place in center of tile
                self.dummies.append((
                    tile_x * self.tile_size + self.tile_size / 2,
                    tile_y * self.tile_size + self.tile_size / 2
                ))
            
    def get_grid_width(self) -> int:
        """Get number of columns in grid."""
        return len(self.grid[0]) if self.grid else 0
        
    def get_grid_height(self) -> int:
        """Get number of rows in grid."""
        return len(self.grid)
        
    def update(self):
        """Update game state (called each frame)."""
        # Handle movement input
        pass  # Movement handled via process_input
        
    def process_input(self, keys_pressed: dict):
        """Process keyboard input for player movement/rotation.
        
        Args:
            keys_pressed: Dict mapping key names to bool pressed state.
        """
        # Rotation
        if keys_pressed.get('left', False):
            self.player.rotate(-1)
        if keys_pressed.get('right', False):
            self.player.rotate(1)
            
        # Calculate movement direction based on angle
        dx = 0
        dy = 0
        
        if keys_pressed.get('w', False):
            dx += math.cos(self.player.angle) * self.player.move_speed * self.tile_size
            dy += math.sin(self.player.angle) * self.player.move_speed * self.tile_size
        if keys_pressed.get('s', False):
            dx -= math.cos(self.player.angle) * self.player.move_speed * self.tile_size
            dy -= math.sin(self.player.angle) * self.player.move_speed * self.tile_size
        if keys_pressed.get('a', False):
            # Strafe left
            dx += math.cos(self.player.angle - math.pi / 2) * self.player.move_speed * self.tile_size
            dy += math.sin(self.player.angle - math.pi / 2) * self.player.move_speed * self.tile_size
        if keys_pressed.get('d', False):
            # Strafe right
            dx += math.cos(self.player.angle + math.pi / 2) * self.player.move_speed * self.tile_size
            dy += math.sin(self.player.angle + math.pi / 2) * self.player.move_speed * self.tile_size
            
        if dx != 0 or dy != 0:
            self.player.move(dx, dy, self.grid, self.tile_size)
            
    def get_view_rays(self) -> List[Tuple[float, float, float, int]]:
        """Get the current view rays from the player.
        
        Returns:
            List of (end_x, end_y, distance, side) tuples for each ray.
        """
        return self.player.cast_rays(self.grid, self.tile_size)
        
    def is_point_visible(self, px: float, py: float, tolerance: float = 10.0) -> bool:
        """Check if a world point is visible from the player (not blocked by walls).
        
        Args:
            px: X coordinate of point to check.
            py: Y coordinate of point to check.
            tolerance: Distance tolerance for matching hit point.
            
        Returns:
            True if the point is visible (no wall between player and point).
        """
        # Calculate angle and distance from player to point
        dx = px - self.player.x
        dy = py - self.player.y
        angle_to_point = math.atan2(dy, dx)
        target_dist = math.sqrt(dx * dx + dy * dy)
        
        # Cast ray in that direction
        end_x, end_y, hit_dist, side = self.player._cast_single_ray(
            angle_to_point, self.grid, self.tile_size
        )
        
        # Point is visible if the ray hit at or beyond the target distance
        # (meaning no wall was hit before reaching the target)
        # We allow some tolerance for the hit being slightly before the target
        return hit_dist >= target_dist - tolerance
        
    def fire(self) -> bool:
        """Fire using the center ray. Check dummies first, then walls.
        
        Returns:
            True if something was hit, False otherwise.
        """
        # Cast center ray to get wall distance
        wall_end_x, wall_end_y, wall_dist, wall_side = self.player._cast_single_ray(
            self.player.angle, self.grid, self.tile_size
        )
        
        # Check for dummy hits - use angular hitbox
        dummy_hitbox_radius = self.tile_size * 0.4  # 40% of tile size hitbox
        
        for i, (dx_pos, dy_pos) in enumerate(self.dummies):
            # Calculate vector to dummy
            dx = dx_pos - self.player.x
            dy = dy_pos - self.player.y
            dummy_dist = math.sqrt(dx * dx + dy * dy)
            
            # Skip if dummy is behind a wall
            if not self.is_point_visible(dx_pos, dy_pos, tolerance=dummy_hitbox_radius):
                continue
            
            # Calculate angle to dummy
            angle_to_dummy = math.atan2(dy, dx)
            
            # Calculate angular difference between player facing and dummy
            angle_diff = angle_to_dummy - self.player.angle
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            
            # Calculate angular radius of dummy hitbox
            angular_radius = math.atan2(dummy_hitbox_radius, dummy_dist)
            
            # Check if center ray hits within dummy's angular hitbox
            if abs(angle_diff) <= angular_radius:
                # Hit! Remove dummy
                self.dummies.pop(i)
                return True
                    
        # Check if we hit a wall (not just max distance)
        max_dist = self.player.ray_max_dist * self.tile_size
        if wall_dist < max_dist * 0.99:  # Hit wall before max range
            self.bullet_marks.append((wall_end_x, wall_end_y))
            return True
        return False
        
    def reset_bullets(self):
        """Clear all bullet marks."""
        self.bullet_marks = []
        
    def reset_dummies(self):
        """Respawn all dummies."""
        self.spawn_dummies()
        
    def reset_all(self):
        """Reset bullets and dummies (for R key)."""
        self.reset_bullets()
        self.reset_dummies()
