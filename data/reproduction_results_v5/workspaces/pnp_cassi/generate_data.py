"""
Generate synthetic hyperspectral test data for SD-CASSI simulation.
Creates realistic-looking spectral images with spatial structure.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, zoom


def generate_spectral_scene(H, W, B, seed=0):
    """
    Generate a synthetic hyperspectral image.
    H, W: spatial dimensions
    B: number of spectral bands
    seed: random seed
    """
    rng = np.random.RandomState(seed)
    
    # Create base image with multiple materials/regions
    scene = np.zeros((H, W, B))
    wavelengths = np.linspace(0, 1, B)
    
    # Number of distinct materials/objects
    n_objects = rng.randint(5, 15)
    
    # Background with smooth spectral profile
    bg_spectrum = 0.15 + 0.1 * np.sin(2 * np.pi * wavelengths * 2 + rng.rand() * np.pi)
    bg_spectrum = np.clip(bg_spectrum, 0.05, 0.3)
    for b in range(B):
        scene[:, :, b] = bg_spectrum[b]
    
    # Add objects with different spectral signatures
    for obj in range(n_objects):
        # Object shape: rectangle, circle, or irregular
        shape_type = rng.randint(3)
        
        if shape_type == 0:  # Rectangle
            x1, y1 = rng.randint(0, W-10), rng.randint(0, H-10)
            w, h = rng.randint(10, max(11, W//3)), rng.randint(10, max(11, H//3))
            x2, y2 = min(x1 + w, W), min(y1 + h, H)
            spatial_mask = np.zeros((H, W))
            spatial_mask[y1:y2, x1:x2] = 1.0
        elif shape_type == 1:  # Circle/ellipse
            cx, cy = rng.randint(0, W), rng.randint(0, H)
            rx, ry = rng.randint(5, max(6, W//4)), rng.randint(5, max(6, H//4))
            yy, xx = np.ogrid[:H, :W]
            spatial_mask = ((xx - cx)**2 / max(rx**2, 1) + (yy - cy)**2 / max(ry**2, 1)) <= 1
            spatial_mask = spatial_mask.astype(float)
        else:  # Smooth blob
            cx, cy = rng.rand() * W, rng.rand() * H
            sigma_x = rng.rand() * W * 0.15 + W * 0.05
            sigma_y = rng.rand() * H * 0.15 + H * 0.05
            yy, xx = np.meshgrid(np.arange(H), np.arange(W), indexing='ij')
            spatial_mask = np.exp(-((xx - cx)**2 / (2*sigma_x**2) + 
                                   (yy - cy)**2 / (2*sigma_y**2)))
        
        # Smooth the mask edges
        spatial_mask = gaussian_filter(spatial_mask, sigma=2)
        
        # Spectral signature for this object
        # Use mixture of Gaussian peaks
        n_peaks = rng.randint(1, 4)
        spectrum = np.zeros(B)
        for p in range(n_peaks):
            center = rng.rand()
            width = rng.rand() * 0.2 + 0.05
            amplitude = rng.rand() * 0.6 + 0.2
            spectrum += amplitude * np.exp(-(wavelengths - center)**2 / (2 * width**2))
        
        # Add to scene
        for b in range(B):
            scene[:, :, b] += spatial_mask * spectrum[b]
    
    # Add some texture
    for b in range(B):
        texture = rng.randn(H // 8, W // 8) * 0.02
        texture = zoom(texture, [H / (H//8), W / (W//8)], order=1)
        texture = texture[:H, :W]
        scene[:, :, b] += texture
    
    # Smooth spatially and spectrally
    scene = gaussian_filter(scene, sigma=[1.5, 1.5, 0.3])
    
    # Normalize to [0, 1]
    scene = np.clip(scene, 0, None)
    if scene.max() > 0:
        scene = scene / scene.max()
    
    return scene


def generate_test_scenes(n_scenes, H, W, B, base_seed=100):
    """Generate multiple test scenes."""
    scenes = []
    for i in range(n_scenes):
        scene = generate_spectral_scene(H, W, B, seed=base_seed + i)
        scenes.append(scene)
    return scenes


if __name__ == "__main__":
    # Generate and verify test scenes
    H, W, B = 64, 64, 31
    scenes = generate_test_scenes(4, H, W, B)
    
    for i, scene in enumerate(scenes):
        print(f"Scene {i}: shape={scene.shape}, range=[{scene.min():.3f}, {scene.max():.3f}], "
              f"mean={scene.mean():.3f}, std={scene.std():.3f}")
    
    print("Scene generation test passed!")
