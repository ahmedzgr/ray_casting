"""
UI module for the 2D ray tracing introduction project.
Handles pygame initialization, rendering, and input events.
"""

import pygame
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logic import GameState


# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_DARK_GRAY = (40, 40, 40)
COLOR_LIGHT_GRAY = (150, 150, 150)
COLOR_RED = (200, 50, 50)
COLOR_YELLOW = (255, 255, 0)
COLOR_BLUE = (50, 150, 255)
COLOR_GREEN = (50, 200, 50)
COLOR_CEILING = (100, 100, 150)
COLOR_FLOOR = (80, 60, 40)
COLOR_WALL_LIGHT = (200, 200, 200)
COLOR_WALL_DARK = (150, 150, 150)
COLOR_BULLET_MARK = (50, 50, 50)  # Dark gray bullet holes
COLOR_CROSSHAIR = (0, 255, 0)  # Green crosshair
COLOR_DUMMY = (255, 100, 100)  # Red-orange dummy


class Renderer:
    """Handles all pygame rendering for the game."""
    
    def __init__(self, screen_width: int = 800, screen_height: int = 600, 
                 minimap_scale: float = 0.15, title: str = "Ray Tracing Intro - 3D"):
        """Initialize the pygame renderer.
        
        Args:
            screen_width: Width of the window in pixels.
            screen_height: Height of the window in pixels.
            minimap_scale: Scale factor for the minimap (0-1).
            title: Window title.
        """
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.minimap_scale = minimap_scale
        
    def clear(self):
        """Clear the screen to background color."""
        self.screen.fill(COLOR_BLACK)
        
    def draw_3d_view(self, game_state: "GameState", rays: list):
        """Draw the 3D first person view using ray casting distances.
        
        Args:
            game_state: The current game state.
            rays: List of (end_x, end_y, distance, side) tuples.
        """
        # Draw ceiling and floor
        ceiling_rect = pygame.Rect(0, 0, self.screen_width, self.screen_height // 2)
        floor_rect = pygame.Rect(0, self.screen_height // 2, self.screen_width, self.screen_height // 2)
        pygame.draw.rect(self.screen, COLOR_CEILING, ceiling_rect)
        pygame.draw.rect(self.screen, COLOR_FLOOR, floor_rect)
        
        player = game_state.player
        num_rays = len(rays)
        strip_width = self.screen_width / num_rays
        
        # Projection plane distance (for correct wall height calculation)
        proj_plane_dist = (self.screen_width / 2) / math.tan(player.fov / 2)
        
        for i, (end_x, end_y, distance, side) in enumerate(rays):
            # Fix fisheye effect by using perpendicular distance
            # Calculate ray angle relative to player angle
            ray_offset = (i / (num_rays - 1) - 0.5) * player.fov
            ray_angle = player.angle + ray_offset
            
            # Correct distance to remove fisheye
            angle_diff = ray_angle - player.angle
            perp_distance = distance * math.cos(angle_diff)
            
            # Avoid division by zero
            if perp_distance < 1:
                perp_distance = 1
                
            # Calculate wall strip height
            wall_height = (game_state.tile_size / perp_distance) * proj_plane_dist
            wall_height = min(wall_height, self.screen_height)
            
            # Wall position on screen
            wall_top = (self.screen_height - wall_height) // 2
            wall_bottom = wall_top + wall_height
            
            # Choose color based on side (x-side = lighter, y-side = darker)
            # This gives depth perception
            if side == 0:
                color = COLOR_WALL_LIGHT
            else:
                color = COLOR_WALL_DARK
                
            # Apply distance fog/darkening
            darkness = min(1.0, perp_distance / (game_state.tile_size * 15))
            color = (
                int(color[0] * (1 - darkness * 0.7)),
                int(color[1] * (1 - darkness * 0.7)),
                int(color[2] * (1 - darkness * 0.7))
            )
            
            # Draw wall strip
            x = i * strip_width
            pygame.draw.rect(
                self.screen,
                color,
                (x, wall_top, strip_width + 1, wall_height)
            )
            
    def draw_minimap(self, game_state: "GameState", rays: list):
        """Draw the 2D minimap in the top-right corner.
        
        Args:
            game_state: The current game state.
            rays: List of (end_x, end_y, distance, side) tuples.
        """
        grid = game_state.grid
        tile_size = game_state.tile_size
        
        # Calculate minimap dimensions
        map_width = len(grid[0]) * tile_size
        map_height = len(grid) * tile_size
        
        minimap_width = int(self.screen_width * self.minimap_scale)
        minimap_height = int(minimap_width * (map_height / map_width))
        
        # Scale factor for minimap
        scale_x = minimap_width / map_width
        scale_y = minimap_height / map_height
        
        # Minimap position (top-right corner with padding)
        padding = 10
        minimap_x = self.screen_width - minimap_width - padding
        minimap_y = padding
        
        # Draw minimap background
        bg_rect = pygame.Rect(minimap_x - 2, minimap_y - 2, minimap_width + 4, minimap_height + 4)
        pygame.draw.rect(self.screen, COLOR_BLACK, bg_rect)
        pygame.draw.rect(self.screen, COLOR_WHITE, bg_rect, 2)
        
        # Draw grid
        for y in range(len(grid)):
            for x in range(len(grid[0])):
                rect = pygame.Rect(
                    minimap_x + x * tile_size * scale_x,
                    minimap_y + y * tile_size * scale_y,
                    tile_size * scale_x,
                    tile_size * scale_y
                )
                
                if grid[y][x] == 1:  # Wall
                    pygame.draw.rect(self.screen, COLOR_DARK_GRAY, rect)
                else:  # Empty
                    pygame.draw.rect(self.screen, COLOR_WHITE, rect)
                    
        # Draw rays on minimap
        player = game_state.player
        player_minimap_x = minimap_x + player.x * scale_x
        player_minimap_y = minimap_y + player.y * scale_y
        
        for end_x, end_y, distance, side in rays:
            end_minimap_x = minimap_x + end_x * scale_x
            end_minimap_y = minimap_y + end_y * scale_y
            pygame.draw.line(
                self.screen,
                COLOR_YELLOW,
                (player_minimap_x, player_minimap_y),
                (end_minimap_x, end_minimap_y),
                1
            )
            
        # Draw player on minimap
        player_radius = max(3, int(8 * scale_x))
        pygame.draw.circle(
            self.screen,
            COLOR_RED,
            (int(player_minimap_x), int(player_minimap_y)),
            player_radius
        )
        
        # Draw player facing direction on minimap
        look_length = 15 * scale_x
        end_x = player_minimap_x + look_length * math.cos(player.angle)
        end_y = player_minimap_y + look_length * math.sin(player.angle)
        
        pygame.draw.line(
            self.screen,
            COLOR_GREEN,
            (player_minimap_x, player_minimap_y),
            (end_x, end_y),
            2
        )
        
    def draw_crosshair(self):
        """Draw a centered crosshair on screen."""
        cx = self.screen_width // 2
        cy = self.screen_height // 2
        size = 10
        thickness = 2
        
        # Horizontal line
        pygame.draw.line(
            self.screen,
            COLOR_CROSSHAIR,
            (cx - size, cy),
            (cx + size, cy),
            thickness
        )
        # Vertical line
        pygame.draw.line(
            self.screen,
            COLOR_CROSSHAIR,
            (cx, cy - size),
            (cx, cy + size),
            thickness
        )
        
    def draw_bullet_marks(self, game_state: "GameState", rays: list):
        """Draw bullet marks on walls in the 3D view (only if visible).
        
        Args:
            game_state: The current game state.
            rays: List of rays for calculating positions.
        """
        if not hasattr(game_state, 'bullet_marks') or not game_state.bullet_marks:
            return
            
        player = game_state.player
        proj_plane_dist = (self.screen_width / 2) / math.tan(player.fov / 2)
        
        for mark_x, mark_y in game_state.bullet_marks:
            # Check visibility: cast ray to mark, see if it hits near there
            if not game_state.is_point_visible(mark_x, mark_y):
                continue
                
            # Calculate angle to bullet mark from player
            dx = mark_x - player.x
            dy = mark_y - player.y
            mark_angle = math.atan2(dy, dx)
            
            # Normalize angle difference to [-pi, pi]
            angle_diff = mark_angle - player.angle
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi
                
            # Check if mark is within FOV
            if abs(angle_diff) > player.fov / 2:
                continue
                
            # Calculate distance to mark
            distance = math.sqrt(dx * dx + dy * dy)
            if distance < 1:
                continue
                
            # Calculate screen position
            perp_distance = distance * math.cos(angle_diff)
            if perp_distance < 1:
                continue
                
            # Calculate wall height at this distance
            wall_height = (game_state.tile_size / perp_distance) * proj_plane_dist
            if wall_height > self.screen_height:
                continue
                
            # Calculate screen X position
            screen_x = (angle_diff / player.fov + 0.5) * self.screen_width
            
            # Calculate screen Y position (center of wall)
            wall_top = (self.screen_height - wall_height) // 2
            wall_bottom = wall_top + wall_height
            screen_y = (wall_top + wall_bottom) // 2
            
            # Draw bullet mark (small dark circle)
            mark_size = max(2, int(4 * (proj_plane_dist / perp_distance)))
            pygame.draw.circle(
                self.screen,
                COLOR_BULLET_MARK,
                (int(screen_x), int(screen_y)),
                mark_size
            )
            
    def draw_dummies(self, game_state: "GameState"):
        """Draw dummies in the 3D first person view with visibility checking.
        
        Args:
            game_state: The current game state.
        """
        if not hasattr(game_state, 'dummies') or not game_state.dummies:
            return
            
        player = game_state.player
        proj_plane_dist = (self.screen_width / 2) / math.tan(player.fov / 2)
        dummy_radius = game_state.tile_size * 0.4  # Same as hitbox radius
        
        for dummy_x, dummy_y in game_state.dummies:
            # Calculate angle to dummy center from player
            dx = dummy_x - player.x
            dy = dummy_y - player.y
            dummy_angle = math.atan2(dy, dx)
            
            # Normalize angle difference to [-pi, pi]
            angle_diff = dummy_angle - player.angle
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi
                
            # Check if dummy is within FOV
            if abs(angle_diff) > player.fov / 2:
                continue
                
            # Calculate distance to dummy
            distance = math.sqrt(dx * dx + dy * dy)
            if distance < 1:
                continue
                
            # Calculate screen position
            perp_distance = distance * math.cos(angle_diff)
            if perp_distance < 1:
                continue
            
            # Check visibility by sampling points on the dummy
            # Sample: center, left edge, right edge
            angular_radius = math.atan2(dummy_radius, distance)
            
            visibility_samples = 0
            total_samples = 5  # Check multiple points across the dummy's width
            
            for i in range(total_samples):
                # Sample angle across dummy's visible width
                sample_angle_offset = (i / (total_samples - 1) - 0.5) * 2 * angular_radius
                sample_angle = dummy_angle + sample_angle_offset
                
                # Calculate world position of this sample point
                sample_x = dummy_x + math.cos(sample_angle) * dummy_radius * 0.5
                sample_y = dummy_y + math.sin(sample_angle) * dummy_radius * 0.5
                
                # Check if this point is visible
                if game_state.is_point_visible(sample_x, sample_y, tolerance=dummy_radius * 0.5):
                    visibility_samples += 1
            
            # Calculate visibility ratio (0.0 to 1.0)
            visibility_ratio = visibility_samples / total_samples
            
            # Skip if completely hidden
            if visibility_ratio < 0.1:
                continue
                
            # Calculate dummy height (same as wall tile)
            dummy_height = (game_state.tile_size / perp_distance) * proj_plane_dist
            if dummy_height > self.screen_height:
                continue
                
            # Calculate screen X position
            screen_x = (angle_diff / player.fov + 0.5) * self.screen_width
            
            # Calculate screen Y position
            wall_top = (self.screen_height - dummy_height) // 2
            
            # Draw dummy as a red rectangle
            dummy_width = dummy_height * 0.5  # Narrower than tall
            dummy_rect = pygame.Rect(
                screen_x - dummy_width / 2,
                wall_top,
                dummy_width,
                dummy_height
            )
            
            # Darken by distance
            darkness = min(1.0, perp_distance / (game_state.tile_size * 10))
            
            # Apply visibility fade (darker when partially hidden)
            visibility_fade = 0.3 + (0.7 * visibility_ratio)  # Min 30% visibility
            
            color = (
                int(COLOR_DUMMY[0] * (1 - darkness * 0.6) * visibility_fade),
                int(COLOR_DUMMY[1] * (1 - darkness * 0.6) * visibility_fade),
                int(COLOR_DUMMY[2] * (1 - darkness * 0.6) * visibility_fade)
            )
            
            pygame.draw.rect(self.screen, color, dummy_rect)
        
    def draw_bullet_marks_on_minimap(self, game_state: "GameState"):
        """Draw bullet marks on the minimap.
        
        Args:
            game_state: The current game state.
        """
        if not hasattr(game_state, 'bullet_marks') or not game_state.bullet_marks:
            return
            
        grid = game_state.grid
        tile_size = game_state.tile_size
        
        # Calculate minimap dimensions
        map_width = len(grid[0]) * tile_size
        map_height = len(grid) * tile_size
        
        minimap_width = int(self.screen_width * self.minimap_scale)
        minimap_height = int(minimap_width * (map_height / map_width))
        
        scale_x = minimap_width / map_width
        scale_y = minimap_height / map_height
        
        padding = 10
        minimap_x = self.screen_width - minimap_width - padding
        minimap_y = padding
        
        # Draw bullet marks
        for mark_x, mark_y in game_state.bullet_marks:
            mark_minimap_x = minimap_x + mark_x * scale_x
            mark_minimap_y = minimap_y + mark_y * scale_y
            
            mark_radius = max(2, int(3 * scale_x))
            pygame.draw.circle(
                self.screen,
                COLOR_BULLET_MARK,
                (int(mark_minimap_x), int(mark_minimap_y)),
                mark_radius
            )
            
    def draw_dummies_on_minimap(self, game_state: "GameState"):
        """Draw dummies on the minimap.
        
        Args:
            game_state: The current game state.
        """
        if not hasattr(game_state, 'dummies') or not game_state.dummies:
            return
            
        grid = game_state.grid
        tile_size = game_state.tile_size
        
        # Calculate minimap dimensions
        map_width = len(grid[0]) * tile_size
        map_height = len(grid) * tile_size
        
        minimap_width = int(self.screen_width * self.minimap_scale)
        minimap_height = int(minimap_width * (map_height / map_width))
        
        scale_x = minimap_width / map_width
        scale_y = minimap_height / map_height
        
        padding = 10
        minimap_x = self.screen_width - minimap_width - padding
        minimap_y = padding
        
        # Draw dummies as red squares
        for dummy_x, dummy_y in game_state.dummies:
            dummy_minimap_x = minimap_x + dummy_x * scale_x
            dummy_minimap_y = minimap_y + dummy_y * scale_y
            
            size = max(4, int(6 * scale_x))
            rect = pygame.Rect(
                dummy_minimap_x - size / 2,
                dummy_minimap_y - size / 2,
                size,
                size
            )
            pygame.draw.rect(self.screen, COLOR_DUMMY, rect)
        
    def draw_hud(self, game_state: "GameState", fps: float):
        """Draw HUD elements (FPS, controls info).
        
        Args:
            game_state: The current game state.
            fps: Current frames per second.
        """
        # FPS counter
        fps_text = self.font.render(f"FPS: {int(fps)}", True, COLOR_WHITE)
        self.screen.blit(fps_text, (10, 10))
        
        # Player position
        player = game_state.player
        pos_text = self.font.render(
            f"Pos: ({player.x:.1f}, {player.y:.1f}) Angle: {math.degrees(player.angle):.1f}°",
            True, COLOR_WHITE
        )
        self.screen.blit(pos_text, (10, 30))
        
        # Bullet count
        bullet_count = len(getattr(game_state, 'bullet_marks', []))
        bullet_text = self.font.render(f"Hits: {bullet_count} | UP: Fire | R: Reset", True, COLOR_WHITE)
        self.screen.blit(bullet_text, (10, 50))
        
        # Controls hint
        controls = "WASD: Move | Arrows: Rotate | ESC: Quit"
        ctrl_text = self.font.render(controls, True, COLOR_LIGHT_GRAY)
        self.screen.blit(ctrl_text, (10, self.screen_height - 25))
        
    def present(self):
        """Flip the display buffer."""
        pygame.display.flip()
        
    def close(self):
        """Clean up pygame resources."""
        pygame.quit()
