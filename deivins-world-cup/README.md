# Deivin's World Cup

[Play the game](https://alesiokanani.github.io/deivins-world-cup/)

A Unity 6 3D arcade soccer game. Deivin's squad plays Messi's crew in three-minute 6v6 matches on a larger 44 × 72 pitch with AI teammates and opponents. Single player; no multiplayer server or account required.

Play in landscape on iPad, iPhone, Android phones, or a computer. Tap **Enter the Stadium**, choose your outfield player, then **Kick Off**.

- Bottom-left joystick: move relative to the screen.
- Pass: pass and switch to the receiver; switch players while defending.
- Through: lead a teammate into space; tackle while defending.
- Shoot: always available in either half. Hold to charge and release to kick. Shots travel through normal physics; long-range attempts can miss, fall short, or be saved.
- Sprint & Skill: hold to sprint; touch with the ball to perform a juke.
- Camera and Pause: top corners.

Keyboard: WASD/arrows to move, Shift to sprint, hold/release Space to shoot, J to pass, K to tackle, Q/Tab to switch, P for player selection, C for camera, Esc to pause, M for sound.

## Teams and player selection

Home: Deivin #7, Max #13, Alesio #10, John #5, Aaron #9, and goalkeeper Emi Martinez #1.

Away: Messi #10, Lamine Yamal #19, Mbappe #7, tall Haaland #9, defender Bellingham #5, and goalkeeper Courtois #1.

Tap any home outfield player on the starting screen. You can also use Pause > Choose your player during a match. Goalkeepers are controlled by AI and cannot be selected. The joystick and action buttons are enlarged and spaced, and the left name/stamina bar has been removed.

## Languages

Choose **English** or **Albanian** under **Language / Gjuha** on the starting screen. Albanian translates the menus, instructions, touch buttons, match announcements, player-selection labels, stadium signs, results, and browser loading screen. The choice is remembered on the device. Proper personal names and physical keyboard keys keep their original names.

## Deployment

This folder contains the compiled Unity 6000.6.3f1 Web build. The existing website publishes the main branch through GitHub Pages. All game URLs are relative so the build works in this subfolder. Build files are uncompressed; no custom compression headers or backend are required.

All 90 built-game checks passed, covering both squads and numbers, pitch boundaries, player selection and goalkeeper exclusion, goalkeeper AI, match rules, enlarged touch layouts and spacing, simultaneous fingers, canceled touches, own-half shooting, charged shots, passing, skills, language persistence, and live stadium text updates. Actual mobile hardware remains to be tested.
