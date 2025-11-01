"""
Sprite generation script for 2D Musou Game
Generates pixel art style sprites using Pillow
"""

from PIL import Image, ImageDraw
import os

# Ensure assets directory exists
os.makedirs("assets/sprites", exist_ok=True)

def create_player_sprite():
    """Create a simple player character sprite"""
    size = 40
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Body (blue rectangle)
    draw.rectangle([10, 15, 30, 35], fill=(100, 200, 255))

    # Head (circle)
    draw.ellipse([12, 5, 28, 21], fill=(255, 220, 180))

    # Eyes
    draw.ellipse([15, 10, 18, 13], fill=(50, 50, 50))
    draw.ellipse([22, 10, 25, 13], fill=(50, 50, 50))

    # Legs
    draw.rectangle([13, 35, 18, 40], fill=(80, 80, 120))
    draw.rectangle([22, 35, 27, 40], fill=(80, 80, 120))

    img.save("assets/sprites/player.png")
    print("Created player.png")

def create_enemy_sprites():
    """Create different enemy type sprites"""
    enemy_types = {
        "basic": {"size": 30, "color": (255, 100, 100), "eye_color": (255, 255, 255)},
        "fast": {"size": 25, "color": (255, 150, 100), "eye_color": (255, 255, 255)},
        "tank": {"size": 40, "color": (150, 100, 255), "eye_color": (255, 255, 255)},
        "elite": {"size": 45, "color": (255, 200, 0), "eye_color": (255, 255, 255)}
    }

    for enemy_name, props in enemy_types.items():
        size = props["size"]
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Body (square/rectangle)
        draw.rectangle([0, 0, size-1, size-1], fill=props["color"])

        # Eyes
        eye_y = int(size * 0.4)
        eye_size = max(2, size // 10)
        draw.ellipse([int(size * 0.3), eye_y, int(size * 0.3) + eye_size, eye_y + eye_size],
                     fill=props["eye_color"])
        draw.ellipse([int(size * 0.6), eye_y, int(size * 0.6) + eye_size, eye_y + eye_size],
                     fill=props["eye_color"])

        # Add teeth for elite
        if enemy_name == "elite":
            teeth_y = int(size * 0.7)
            for i in range(0, size, 6):
                draw.rectangle([i, teeth_y, i+3, teeth_y+4], fill=(255, 255, 255))

        img.save(f"assets/sprites/enemy_{enemy_name}.png")
        print(f"Created enemy_{enemy_name}.png")

def create_projectile_sprite():
    """Create a projectile sprite"""
    size = 16
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Glowing projectile effect
    draw.ellipse([2, 2, 14, 14], fill=(255, 255, 100))
    draw.ellipse([4, 4, 12, 12], fill=(255, 255, 200))

    img.save("assets/sprites/projectile.png")
    print("Created projectile.png")

def create_terrain_tiles():
    """Create simple terrain tiles"""
    tile_size = 100

    # Grass tile
    grass = Image.new('RGB', (tile_size, tile_size), (40, 80, 40))
    draw = ImageDraw.Draw(grass)
    # Add some variation
    import random
    random.seed(42)
    for _ in range(50):
        x = random.randint(0, tile_size)
        y = random.randint(0, tile_size)
        shade = random.choice([(35, 75, 35), (45, 85, 45), (38, 78, 38)])
        draw.rectangle([x, y, x+3, y+3], fill=shade)
    grass.save("assets/sprites/tile_grass.png")
    print("Created tile_grass.png")

    # Stone tile
    stone = Image.new('RGB', (tile_size, tile_size), (100, 100, 120))
    draw = ImageDraw.Draw(stone)
    for _ in range(30):
        x = random.randint(0, tile_size)
        y = random.randint(0, tile_size)
        shade = random.choice([(90, 90, 110), (110, 110, 130), (95, 95, 115)])
        draw.rectangle([x, y, x+5, y+5], fill=shade)
    stone.save("assets/sprites/tile_stone.png")
    print("Created tile_stone.png")

def create_ui_elements():
    """Create UI element sprites"""
    # Health bar background
    health_bg = Image.new('RGB', (200, 20), (100, 100, 100))
    health_bg.save("assets/sprites/ui_health_bg.png")

    # Health bar fill
    health_fill = Image.new('RGB', (200, 20), (200, 50, 50))
    health_fill.save("assets/sprites/ui_health_fill.png")

    print("Created UI elements")

def main():
    print("Generating sprites for 2D Musou Game...")

    create_player_sprite()
    create_enemy_sprites()
    create_projectile_sprite()
    create_terrain_tiles()
    create_ui_elements()

    print("\nAll sprites generated successfully!")
    print("Sprites saved to: assets/sprites/")

if __name__ == "__main__":
    main()
