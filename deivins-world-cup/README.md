# Deivin's World Cup

[Play the game](https://alesiokanani.github.io/deivins-world-cup/)

A Unity 6 3D arcade soccer game. Deivin's squad plays Messi's crew in three-minute 6v6 matches on a larger 44 × 72 pitch with AI teammates and opponents. Single player; no multiplayer server or account required.

Play in landscape on iPad, iPhone, Android phones, or a computer. Tap **Enter the Stadium**, then **Kick Off**.

- Bottom-left joystick: move relative to the screen.
- Pass: a firmer pass with gentle assistance toward the receiver; opponents can still intercept. Switch players while defending.
- Through: lead a teammate into space; tackle while defending.
- Shoot / Tackle: Shoot from either half while attacking; hold to charge and release. Fully charged shots have more speed and airtime. While defending, tap Tackle to slide with a short speed boost. Shots and tackles can still miss.
- Sprint & Skill: hold to sprint; touch with the ball to perform a juke.
- Camera and Pause: top corners.

Keyboard: WASD/arrows to move, Shift to sprint, hold/release Space to shoot (press to slide when defending), J to pass, K to slide-tackle, Q/Tab to switch, C for camera, Esc to pause, M for sound.

## Teams and control

Home: Deivin #7, Max #13, Alesio #10, John #5, Aaron #9, and goalkeeper Emi Martinez #1.

Away: Messi #10, Lamine Yamal #19, Mbappe #7, tall Haaland #9, defender Bellingham #5, and goalkeeper Courtois #1.

Control automatically follows whichever home outfield player receives or wins the ball. Passing lets you steer the intended receiver; if another teammate collects the ball, control follows the actual receiver. There is no player picker or saved player choice. While defending, use Pass or Q/Tab to switch to another outfield player. Goalkeepers are controlled by AI and cannot be selected. The joystick keeps its large size with a simpler design, action buttons are about 15 percent smaller, and players are 30 percent larger.

## Languages

Choose **English** or **Albanian** under **Language / Gjuha** on the starting screen. Albanian translates the menus, instructions, touch buttons, match announcements, automatic-control instructions, stadium signs, results, and browser loading screen. The choice is remembered on the device. Proper personal names and physical keyboard keys keep their original names.

## Deployment

This folder contains the compiled Unity 6000.6.3f1 Web build. The existing website publishes the main branch through GitHub Pages. All game URLs are relative so the build works in this subfolder. Build files are uncompressed; no custom compression headers or backend are required.

All 116 built-game checks passed, covering both squads and numbers, pitch boundaries, automatic possession transfers and goalkeeper exclusion, goalkeeper AI, match rules, revised touch layouts and spacing, simultaneous fingers, canceled touches, own-half shooting, charged-shot flight, assisted passes, sliding tackles, passing, skills, language persistence, and live stadium text updates. Actual mobile hardware remains to be tested.
