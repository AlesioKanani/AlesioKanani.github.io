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

[Play Deivin's World Cup](https://alesiokanani.github.io/deivins-world-cup/): a Unity 3D 6v6 soccer game on a larger field, with AI goalkeepers that track and save shots, automatic control of the home ball carrier, English and Albanian, and landscape touch controls for iPad and phones. Shoot from either half with stronger charged shots, tap the contextual Tackle button to slide while defending, and use assisted passes to reach teammates. The compiled browser game lives in `deivins-world-cup/`.


## Glauk's World

[Play Glauk's World](https://alesiokanani.github.io/glauks-world/): a Three.js superhero game for Glauk. Collect stars, kick goals, fly, and use POW for a super kick. Camera follows him. Phone controls are FLY, JUMP, and POW.


## MSTR and ASST mNAV

[MSTR and ASST mNAV](https://alesiokanani.github.io/mnav/): a live version of the "Strategy mNAV (Multiple of Net Asset Value)" chart, for Strategy (MSTR) and Strive (ASST) on one page. Each company gets three multiples on top (equity premium, enterprise and basic), its share price underneath on a log scale, the dashed 1x to 3x reference levels with the 2x to 3x band, a live point for right now, and a breakdown of how much bitcoin is left for common shareholders once debt and preferred stock are paid.

- Equity premium = market cap / (BTC NAV - debt - preferred at par), cash left out
- Enterprise = (market cap + debt + preferred - cash and similar) / BTC NAV
- Basic = market cap / BTC NAV

How it stays up to date:

- `.github/workflows/mnav-data.yml` runs every hour, every 20 minutes through the US trading day, and whenever a push changes it or the script. It runs `.github/scripts/mnav_data.py` and force-pushes the result as `mnav.json` to the `mnav-data` branch.
- MSTR comes from Strategy's public dashboard API (api.strategy.com, the data behind strategy.com): every trading day since August 2020. Debt before 2025, when that API doesn't carry it, is a short list of note issues and repayments in the script.
- ASST comes from Strive's public dashboard API (strive.com/treasury): bitcoin purchases, weekly share counts, cash and debt, from September 15, 2025. That API only reports today's SATA preferred count, so the earlier counts come from Strive's 8-K and 10-Q filings (listed in the script) and each run adds the newest count to the published file. Days between filings are interpolated.
- The page reads the file from raw.githubusercontent.com, so `main` doesn't fill up with bot commits and Pages doesn't rebuild on every run. Don't commit to `mnav-data`; it's overwritten on every run.
- On every visit the page asks Strategy's API for the current bitcoin price and MSTR quote and adds a live point. Strive's API doesn't allow browser requests, so ASST's newest price is the one from the last run (at most about 20 minutes old during the trading day) combined with the live bitcoin price.
- If one company's source fails, the other still updates, the failed one keeps its last good figures, and the run shows as failed in the Actions tab. If both fail, nothing is published and the page keeps the last good file. To refresh by hand: Actions, then "mNAV data", then "Run workflow".
- The chart is drawn with [uPlot](https://github.com/leeoniya/uPlot) (MIT), kept in `mnav/vendor/`.
