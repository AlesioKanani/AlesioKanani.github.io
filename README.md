# [AlesioKanani.github.io](https://alesiokanani.github.io)

**DRIFT**: press start and your cursor becomes a starship. Steer through deep space, blast asteroids, chain combos, collect energy orbs and follow the signal through wormholes into new sectors, each with its own colors and music.

| Input | Action |
| --- | --- |
| Mouse / finger (or arrows, WASD) | steer: push toward the edge to fly faster |
| Click / hold (or F, Enter) | fire |
| Space (or the WARP button on touch) | warp: drains energy, smashes through asteroids |
| M | sound on/off |
| Esc | land (your best score is saved in your browser) |

When a **signal** is detected, an arrow orbits your ship pointing toward it, the screen edge on that side glows, a beacon shows the distance, and sonar pings come from its direction (faster and higher as you close in). The HUD shows its bearing, distance and whether you're closing. Fly into the wormhole to jump to the next sector.

No build step. `index.html` holds the game (canvas + Web Audio). `gfx.js` renders the realistic graphics with WebGL shaders: a tileable noise nebula with dark dust lanes, lit 3D planets (gas giants with storms and shadowed rings, ocean worlds with clouds and city lights, cratered moons, ice, desert and lava worlds), ray-marched tumbling asteroids, and gravitational lensing around the wormhole. If WebGL isn't available, the game falls back to simpler canvas drawing. `og.jpg` is the link-preview image.
The previous site lives at [`puzzle.html`](https://alesiokanani.github.io/puzzle.html).
