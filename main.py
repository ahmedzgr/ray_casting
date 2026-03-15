#!/usr/bin/env python3
"""
Main entry point for the 2D ray tracing introduction project.
Ties together the logic and UI modules.
"""

from logic import GameState
from ui import Renderer
import pygame


def main():
    """Main game loop."""
    # Configuration
    MAP_FILE = "map.txt"
    TILE_SIZE = 50
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    
    # Load game state
    game_state = GameState(MAP_FILE, TILE_SIZE)
    
    # Initialize renderer with fixed screen size for 3D view
    renderer = Renderer(SCREEN_WIDTH, SCREEN_HEIGHT, minimap_scale=0.2, 
                       title="Ray Tracing Intro - 3D First Person")
    
    # Input state tracking
    keys_pressed = {
        'w': False,
        's': False,
        'a': False,
        'd': False,
        'left': False,
        'right': False
    }
    
    # Main loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_w:
                    keys_pressed['w'] = True
                elif event.key == pygame.K_s:
                    keys_pressed['s'] = True
                elif event.key == pygame.K_a:
                    keys_pressed['a'] = True
                elif event.key == pygame.K_d:
                    keys_pressed['d'] = True
                elif event.key == pygame.K_LEFT:
                    keys_pressed['left'] = True
                elif event.key == pygame.K_RIGHT:
                    keys_pressed['right'] = True
                elif event.key == pygame.K_UP:
                    # Fire!
                    game_state.fire()
                elif event.key == pygame.K_r:
                    # Reset bullets and dummies
                    game_state.reset_all()
                    
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_w:
                    keys_pressed['w'] = False
                elif event.key == pygame.K_s:
                    keys_pressed['s'] = False
                elif event.key == pygame.K_a:
                    keys_pressed['a'] = False
                elif event.key == pygame.K_d:
                    keys_pressed['d'] = False
                elif event.key == pygame.K_LEFT:
                    keys_pressed['left'] = False
                elif event.key == pygame.K_RIGHT:
                    keys_pressed['right'] = False
                    
        # Process input (movement/rotation)
        game_state.process_input(keys_pressed)
        
        # Get view rays for rendering
        rays = game_state.get_view_rays()
        
        # Render frame
        renderer.clear()
        renderer.draw_3d_view(game_state, rays)
        renderer.draw_dummies(game_state)
        renderer.draw_bullet_marks(game_state, rays)
        renderer.draw_crosshair()
        renderer.draw_minimap(game_state, rays)
        renderer.draw_dummies_on_minimap(game_state)
        renderer.draw_bullet_marks_on_minimap(game_state)
        renderer.draw_hud(game_state, renderer.clock.get_fps())
        renderer.present()
        
        # Cap framerate
        renderer.clock.tick(60)
        
    # Cleanup
    renderer.close()


if __name__ == "__main__":
    main()
