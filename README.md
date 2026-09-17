# Overlord

Overlord is starting as a browser-based first-person MMO prototype. The immediate goal is a high-quality playable forest vertical slice before adding combat, towns, multiplayer, and MMO backend systems.

## Current vertical slice

- First-person mouse look
- WASD movement
- Sprint with Shift
- Jump with Space
- Terrain-following movement and gravity
- Basic tree collision
- Procedural rolling terrain
- Dense instanced forest
- Instanced grass and rocks
- Lake basin and water
- Dynamic sunlight and soft shadows
- Atmospheric fog and floating motes
- ACES tone mapping
- Sprint FOV and head bob
- FPS counter

## Run locally

```bash
npm install
npm run dev
```

Then open the Vite URL, click **Enter World**, and use:

- **WASD** — move
- **Shift** — sprint
- **Space** — jump
- **Mouse** — look
- **Esc** — release mouse

## Visual-quality roadmap

The procedural geometry is the fast playable foundation. To reach reference-quality photorealism, the next pass will replace placeholder trees, foliage, rocks, and ground surfaces with PBR/photogrammetry assets while preserving the movement, world, collision, instancing, and rendering systems already built here.

Next milestones:

1. Photoreal PBR forest asset pipeline
2. Better terrain materials and ground scatter
3. GLTF/GLB tree and foliage loading with LODs
4. Improved water, sky, volumetrics, and sun shafts
5. Footsteps, ambience, and movement audio
6. World streaming/chunking
7. Character model + third-person option
8. Multiplayer networking
9. MMO services and persistence
