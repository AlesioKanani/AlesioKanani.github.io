# Deivin's World Cup

[Play the game](https://alesiokanani.github.io/deivins-world-cup/)

A Unity 6 3D arcade soccer game. Deivin's squad plays Messi's crew in three-minute 6v6 matches on a larger 44 × 72 pitch with AI teammates and opponents. Single player; no multiplayer server or account required.

Play in landscape on iPad, iPhone, Android phones, or a computer. Tap **Enter the Stadium**, then **Start**.

Both teams wait in a spread kickoff formation in their own halves, with the goalkeepers in goal. Move or kick the ball to start play and the clock. Matches start in the normal sideline view. Camera switches between this view and a forward-facing view looking toward the opponent goal; there is no zoomed-out option. Goal restarts keep your chosen camera and use the same formation; the opposing team starts automatically after a short pause.

- Bottom-left joystick: move relative to the screen. Pass sits left of Sprint & Skill and slightly lower, Shoot above it and slightly to the right, and Through diagonally above-left, with separate touch areas.
- Pass / Switch: hold to charge more ball speed, then release. A tap gives a normal assisted pass. Aim backward to pass to the AI goalkeeper, who automatically chooses an outfield outlet. Without possession, the button reads Switch and switches outfield players immediately.
- Through: hold to charge a farther lead into fixed space ahead of a teammate's run, then release and move the receiver to collect it; tackle immediately while defending.
- Shoot / Tackle: Shoot from either half while attacking; hold to charge and release. Fully charged shots have more speed and airtime. While defending, tap Tackle to slide with a short speed boost. Goalkeepers track shots and make saves, fast balls use swept contact checks, and goals only count between the posts below the crossbar. Shots and tackles can still miss.
- Sprint & Skill: hold to sprint. Rainbow is the only skill move. Two quick taps rainbow-flick the ball from behind your body into forward space, releasing it for you to chase. Its launch follows your current running direction and speed so the descending ball stays ahead even while sprinting.
- Camera and Pause: top corners. Camera switches between sideline and forward-facing views. Movement follows the screen: attack right in sideline view, up in forward view.

A horizontal power bar fills at the bottom center for shots, pass speed, and through distance. Shoot while chasing a loose ball queues an immediate medium-power first-touch shot on the next home outfield reception. When an opponent has possession, Shoot becomes Tackle. After a slide animation finishes, you can immediately slide again with no extra cooldown.

Keyboard: WASD/arrows to move, Shift to sprint, hold/release Space to shoot (press to queue a first-touch shot for a loose ball or slide against an opponent in possession), hold/release J to charge pass speed, hold/release L to charge through distance, K to slide-tackle, F for a rainbow, Q/Tab to switch, C for camera, Esc to pause, M for sound.

## Teams and control

Home: Deivin #7, Max #13, Alesio #10, John #5, Aaron #9, and goalkeeper Emi Martinez #1.

Away: Messi #10, Lamine Yamal #19, Mbappe #7, tall Haaland #9, defender Bellingham #5, and goalkeeper Courtois #1.

Control automatically follows whichever home outfield player receives or wins the ball. Passing lets you steer the intended receiver; if another teammate collects the ball, control follows the actual receiver. There is no player picker or saved player choice. Without possession, the Pass button becomes Switch; use it or Q/Tab to switch to another outfield player. Goalkeepers are controlled by AI and cannot be selected. The joystick keeps its large size with a simpler design, action buttons are about 15 percent smaller, and players are 30 percent larger.

## Languages

Choose **English** or **Albanian** under **Language / Gjuha** on the starting screen. Albanian translates the menus, instructions, touch buttons, match announcements, automatic-control instructions, stadium signs, results, and browser loading screen. The choice is remembered on the device. Proper personal names and physical keyboard keys keep their original names.

## Deployment

This folder contains the compiled Unity 6000.6.3f1 Web build. The existing website publishes the main branch through GitHub Pages. All game URLs are relative so the build works in this subfolder. Build files are uncompressed; no custom compression headers or backend are required.

All 269 built-game checks passed, covering both squads and numbers, pitch boundaries, automatic possession transfers and goalkeeper exclusion, goalkeeper AI and saves, shot tracking, swept ball contacts, valid goal geometry, match rules, revised touch layouts and spacing, simultaneous fingers, canceled touches, own-half shooting, charged-shot flight, assisted passes, immediate repeat sliding tackles, through balls into fixed space, charged passing, goalkeeper back-passes, rainbow recovery during continuous running and sprinting, contextual Pass/Switch labels, spread kickoff formations and restarts, sideline/forward camera switching and framing, rainbow-only skill input, first-touch shooting, complete simulated matches, language persistence, and live stadium text updates. Actual mobile hardware remains to be tested.

Difficulty: Easy uses slower opponents with less frequent tackles and weaker shots; Normal provides balanced opposition; Hard uses full-speed opponents, more aggressive tackling, and stronger shots. Your team keeps the same abilities across all three settings.

A small yellow downward triangle identifies your controlled player. To steal without sliding, move toward the exposed ball in front of an opponent and get within about 1.25 metres of the ball. Running into their back alone will not win it. A successful steal immediately attaches the ball to your player and displays Ball won; newly won possession has a brief protection against instant steal-backs. Slide tackling remains available.

On desktop, circular action buttons show their keyboard shortcuts beneath the action: Shoot/Tackle (SPACE), Pass/Switch (J), Through (L), Sprint & Skill (SHIFT / F). Shift sprints and F performs a rainbow. These key hints are hidden on phones and iPads.
