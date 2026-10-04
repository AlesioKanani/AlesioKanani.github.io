# Deivin's World Cup

[Play the game](https://alesiokanani.github.io/deivins-world-cup/)

A Unity 6 3D arcade soccer game. Deivin's squad plays Messi's crew in three-minute 5v5 matches with AI teammates and opponents. Single player; no multiplayer server or account required.

Play in landscape on iPad, iPhone, Android phones, or a computer. Tap **Enter the Stadium**, then **Kick Off**.

- Bottom-left joystick: move relative to the screen.
- Pass: pass and switch to the receiver; switch players while defending.
- Through: lead a teammate into space; tackle while defending.
- Clear / Shoot: Clear in your own half; Shoot in the opponent's half. Hold Shoot to charge and release to kick.
- Sprint & Skill: hold to sprint; touch with the ball to perform a juke.
- Camera and Pause: top corners.

Keyboard: WASD/arrows to move, Shift to sprint, hold/release Space to shoot, J to pass, K to tackle, Q/Tab to switch, C for camera, Esc to pause, M for sound.

## Deployment

This folder contains the compiled Unity 6000.6.3f1 Web build. The existing website publishes the main branch through GitHub Pages. All game URLs are relative so the build works in this subfolder. Build files are uncompressed; no custom compression headers or backend are required.

55 built-game checks passed, covering match rules, touch layouts, simultaneous fingers, canceled touches, Clear/Shoot switching, charged shots, passing, and skills. The Web player was loaded and played in a browser. Actual mobile hardware remains to be tested.
