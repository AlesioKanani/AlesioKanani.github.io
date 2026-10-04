# [AlesioKanani.github.io](https://alesiokanani.github.io)

**DRIFT**: press start and your cursor becomes a starship. Steer through deep space, blast asteroids, chain combos, collect energy orbs and follow the signal through wormholes into new sectors, each with its own colors and music.

| Input | Action |
| --- | --- |
| Mouse / finger (or arrows, WASD) | steer: push toward the edge to fly faster |
| Click / hold (or F, Enter) | fire |
| Space (or the WARP button on touch) | warp: drains energy, smashes through asteroids |
| M | sound on/off |
| Esc | land (your best score is saved in your browser) |

The home screen has a **Skip to level** row: pick any of the seven sectors to start there. The ✓ Game completed badge is only awarded for a run that starts at level 1.

When a **signal** is detected, an arrow orbits your ship pointing toward it, the screen edge on that side glows, a beacon shows the distance, and sonar pings come from its direction (faster and higher as you close in). The HUD shows its bearing, distance and whether you're closing. Get close and a **Guardian** warps in: the wormhole stays sealed until you destroy it. Each sector has its own: the spiked **Thornlord**, the staring **Oculus** eye, the spider-like **Widow** that lunges, the swooping scythe-winged **Reaper**, and the **Leviathan** serpent whose armoured body soaks up shots (hit the head for full damage). It circles you firing slow red bolts (dodge them, hide behind asteroids or shoot them down) and every few seconds charges a ring volley, telegraphed by its glowing core. Beat it, then fly into the wormhole to jump to the next sector.

**Sector 6, The Maw**: a blood-red sky with an eclipsed sun, lightning and a heartbeat. Here **every Guardian comes out at once** (the Convergence): each one is weaker and fires less often, but they surround you.

**Sector 7, the Silver Dimension**: cross over into a world of chrome planets, drifting mirror shards and silver haze, where the final boss rises: **the Sovereign**, a colossal crowned mask with a third eye, a burning maw and a halo of blades. It fights in three phases (eye volleys, then spiralling fire from its maw, then claw bursts as its cracks glow). Destroy it and the journey is complete: you get the ending screen with your stats, and can **Play Again** from sector 1.

No build step. `index.html` holds the game (canvas + Web Audio). `gfx.js` renders the realistic graphics with WebGL shaders: a tileable noise nebula with dark dust lanes, lit 3D planets (gas giants with storms and shadowed rings, ocean worlds with clouds and city lights, cratered moons, ice, desert, lava and mirror-chrome worlds), ray-marched tumbling asteroids, and gravitational lensing around the wormhole. If WebGL isn't available, the game falls back to simpler canvas drawing. `og.jpg` is the link-preview image.
The previous site lives at [`puzzle.html`](https://alesiokanani.github.io/puzzle.html).


## Deivin's World Cup

[Play Deivin's World Cup](https://alesiokanani.github.io/deivins-world-cup/): a Unity 3D 6v6 soccer game on a larger field, with AI goalkeepers, automatic control of the home ball carrier, English and Albanian, and landscape touch controls for iPad and phones. Shoot from either half with stronger charged shots, tap the contextual Tackle button to slide while defending, and use assisted passes to reach teammates. The compiled browser game lives in `deivins-world-cup/`.
