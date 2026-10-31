# Train step-off: body motion research (2026-11-01)

**How this was done.** Each Short was played in Chrome (`yt_reference.py`), and each fall was then
stepped through **frame by frame** by seeking the player in 1/12 s steps (about 2.5 frames at 30 fps).
Nothing was downloaded. Times below are video seconds.

**Screenshots.** 35 key-phase screenshots were taken and kept **locally only**, in
`out/review/zack_motion/` (git-ignored); the file names are listed per fall. They were not committed to
`assets/review/` as the brief asked, because they are third-party YouTube frames. The project rule since
the first study is "describe in words, no YouTube images in the repo". The owner can open them on the
Mac.

Companion research: `shorts/tools/research/character_motion.md` (retargeting, foot locks, face capture,
video-to-mocap tools, licences).

## 1. Zack D Films: 8 falls

| # | Short (views) | Fall window | Loss of balance → impact | Slow motion? | Camera |
|---|---|---|---|---|---|
| Z1 | [The Slip-And-Fall Scammer](https://www.youtube.com/shorts/ghxXzW2A1E8) (14M) | 0.0–0.9; 22.3–25.0 (montage of 4 falls) | **0.45–0.5 s** each (e.g. 23.05 → 23.50) | No: real time with motion blur | static wide; a quick montage, each fall cut right after landing |
| Z2 | [He Walked Off A 120-Foot Cliff](https://www.youtube.com/shorts/Fc6cV_fW8rY) (12M) | 10.8–13.6 | steps off at 12.13; cut at 13.05 (**0.9 s**, impact never shown) | No | follows behind at shoulder height while he walks, then a hard cut to an extreme wide of the tiny falling figure |
| Z3 | [The Fan Who Fell From The Stage](https://www.youtube.com/shorts/KTZkq986eG4) (20M) | 5.8–7.6 (the push); 10.2–13.2 (the fall) | feet go at 10.87, back hits at about 12.6, head at 12.9: **1.8 s on screen for a 3 ft fall** | **Yes, about 4×.** The push is also held almost frozen for about 0.6 s (5.8–6.4), then the camera cranes up | low, frontal, slowly pushing and rolling with the body; **cuts on head impact to an X-ray of the brain** (12.95) |
| Z4 | [The Segway Owner Who Fell Off A Cliff](https://www.youtube.com/shorts/c3aRLh3SoAs) (6.2M) | 14.2–18.0 | wobble 14.3–15.5 (1.2 s); rigid tilt backward 15.5–16.45 (**0.9 s**) | smooth and slow; likely slowed during the tilt | frontal medium, static; cut to a high wide at 16.5 as he goes over |
| Z5 | [Pushed Off A 60-Foot Bridge](https://www.youtube.com/shorts/npFShzn7-Ds) (14M) | 0.0–2.6 | push at 0.33, airborne at 0.67 (**0.35 s**), then hangs in the air | **Yes:** from about 1.0 s she barely drops while the camera orbits | behind her, then a continuous **orbit to a side view** (1.5–2.6) |
| Z6 | [Why You Shouldn't Stand Near Trains](https://www.youtube.com/shorts/40j6qvMDVrE) (12M): the air blast | 3.8–5.4 | lifted at 4.30, on the ground at 4.80 (**0.5 s**) | No: heavy motion blur (4.47–4.72) | static side wide |
| Z7 | same Short: pulled toward the train | 20.4–24.6 | balance wobble 21.4–22.7 (1.2 s); tips and is down on his hands at 23.15 (**about 0.45 s**) | No | **top-down tracking**, then a cut to a low close-up of his face (24.07) |
| Z8 | [What To Do If You Fall Through Ice](https://www.youtube.com/shorts/Ppw2GE3fLpQ) (64M) | 1.8–6.2 | a deliberate plank-like tip forward, 4.55 → 5.3 (**0.75 s**) | No | crane up to overhead (2.4–3.0), slowly rotating |

### What the body does

**Arms: two phases, always.**
1. **Startle:** within about 0.1–0.2 s of the push or slip, both arms fly **up and out**.
   - Z5: push at 0.33, arms up and wide at 0.42–0.58.
   - Z3: arms thrown overhead at 11.03.
   - Z2: arms windmill out and up at 12.30–12.72.
   - Z7: arms out wide for balance at 21.4–22.6.
2. **Protective reach** toward where the body is going.
   - **Backward fall (Z3):** both arms swing **overhead and back toward the floor** (11.03–11.37). Then
     **one hand goes behind his head** (11.62–11.87), and the back lands before the head.
   - **Forward or sideways (Z7, Z8):** hands go out to the ground (23.07–23.15).
   - **Slip (Z1):** one arm braces toward the floor and the other flies up.

**Knees and legs**
- In the air, the knees **bend and the legs trail** behind the torso (Z2 12.80–12.97, Z5 0.92–1.25).
- In a slip, the **feet shoot out forward and one leg kicks up** (Z1 23.05–23.30).
- When thrown forward onto the ground, the **heels kick up behind** (Z6 4.80–5.38).
- In the Segway tilt, the body stays **rigid and locked** to the machine (Z4); the legs stay straight.

**Spine and head**
- Backward falls arch the back but keep the **head lifted and chin tucked**, so the head lands last (Z3
  12.37–12.9).
- Forward falls pitch the torso to horizontal with the face up and forward (Z2, Z5).
- No head whip is visible; the head follows the torso.

**Feet**
- Slips slide out (Z1).
- Walking off a ledge is a normal step into nothing (Z2 12.13).
- No toe detail is visible at Short resolution.

**Face**
- Shown only in front views (Z3, Z7, Z1).
- **Onset:** eyes wide and **mouth open** (fear or shock) as the fall starts (Z3 11.03–11.45). It holds
  for the whole slowed fall.
- **After impact:** a **pain grimace or shouting mouth**, with brows knotted (Z1 0.75–1.0 "suddenly
  scream", Z7 24.07–24.57 wide-eyed shout to camera).
- Eyes shutting just before impact could **not be confirmed** at this resolution.

**Clothes and hair:** mostly **rigid**. There is no visible cloth simulation on shirts and hair barely
moves (Z2, Z3, Z5). Low priority for us.

**Camera grammar**
- Follow from behind or the side **before** the fall.
- **Cut or orbit during** it.
- On impact, **cut to the consequence**: an X-ray (Z3), a top-down view, or the aftermath.

**Where the slow motion goes:** on the one fall that is the story's point (Z3, Z5), at about 3–4×. Side
falls in a montage play in real time with blur (Z1, Z6).

**Local screenshots** (`out/review/zack_motion/`):
- Z1: `1_slip_loss`, `1_slip_mid`, `1_slip_impact`
- Z2: `2_cliff_step`, `2_cliff_arms`, `2_cliff_tuck`
- Z3: `3_stage_loss`, `3_stage_reach`, `3_stage_handhead`, `3_stage_impact`
- Z4: `4_segway_wobble`, `4_segway_tilt`, `4_segway_flail`
- Z5: `5_bridge_push`, `5_bridge_startle`, `5_bridge_air`
- Z6: `6_train_lift`, `6_train_blur`, `6_train_land`
- Z7: `7_train_reach`, `7_train_face`
- Z8: `8_ice_arms`, `8_ice_tip`, `8_ice_down`

## 2. Real-world step-offs

| # | Clip | Window | What happens | Timing |
|---|---|---|---|---|
| R1 | [Why do people fall… (compilation)](https://www.youtube.com/shorts/RIRP9Me__CM), clip 1 (night, far camera) | 0.40–1.73 | steps off **facing the direction of travel** already running; 3 strides with the torso pitching further forward on each; then hands and knees, and a roll | first contact to hands on the ground **about 0.7 s**; lying flat by about 1.0 s |
| R2 | same, clip 3 (woman in red) | 12.07–14.2 | steps down holding the door, **sideways to the train**; her feet stop, the body is spun round, and she **sits down hard on her hip**; then she **slides along the platform toward the coach** | step to sitting **about 0.5 s**; slides about 1.2 s |
| R3 | same, clip 4 (man in red) | 14.40–17.1 | **facing forward**, he runs it out: 4–5 steps with the **arms out wide** for balance and the torso leaning further each step; the legs can't keep up, so he reaches out with both hands, lands on his knees, slides on his chest and his legs flip up behind | run-out **about 1.0 s**; hands to knees **0.35 s**; tumble about 0.6 s |
| R4 | same, clip 5 (man with a backpack) | 17.27–18.77 | steps down **holding the handle, facing the coach**; the train swings him round, the **backpack swings out (overlap)**, and he is thrown back against the coach and **drops to a crouch at the platform edge**, beside the gap | about 0.9 s |
| R5 | [Man struggles to get off a Mumbai local](https://www.youtube.com/shorts/5oxk4ExVE7Y) (Asianet) | 6.6–8.4 | pushed out of a door crush (the train is barely moving); falls on his back or side, rolls to his knees, forehead down, arms tucked | ejection to the ground **about 0.3 s**; on hands and knees about 1 s |

**Local screenshots:**
- R1: `R1_night_land`, `R1_night_down`
- R2: `R2_red_step`, `R2_red_sit`
- R3: `R3_red_run`, `R3_red_pitch`, `R3_red_hands`
- R4: `R4_yellow_step`, `R4_yellow_drop`
- R5: `R5_crowd_eject`, `R5_crowd_knees`

**Real versus Zack:** real falls are **faster and less graceful**.
- From the moment of loss of balance, the body hits the ground in **0.3–0.5 s** (R2, R4, R5; CMU
  `90_18` 0.35 s).
- The forward case adds about **1 s of running steps** first (R1, R3).
- Real arms do the same two phases: out for balance, then hands to the ground.

## 3. What to use for our three cases

All timings are at 30 fps. The table shows real-time timing; for the hero fall, slow it about 3× on
screen as Zack does (Z3), and cut on contact.

| Case | Body | Arms | Face | Timing (real) | Base clip |
|---|---|---|---|---|---|
| **Facing forward** (with the train) | the feet hit and the upper body keeps going; 3–4 run-out steps, the torso leaning more on each; then the legs fail | out wide for balance on the steps, then both hands forward to the ground | surprise at foot contact (+3–4 frames), then a gritted effort face on the steps, eyes wide | steps 25–30 f; hands at about 40 f; knees about 44 f; slide to about 60 f | R3; CMU `16_08` / `127_05` for the run and braking, `90_16` for the fall onto the hands |
| **Sideways** | the feet stop and the hips are dragged round; he twists and sits down hard (R2), or is swung back against the coach (R4) | the trailing hand stays on the handle, then both hands go to the ground | startle, then a pain wince on landing | twist and sit-down **about 15 f** | R2 / R4; CMU `91_59` (small stumble with a turn) |
| **Facing backward** | the feet stop and the body keeps going **backward**; the knees buckle, the hips drop and the back hits; the head last, chin tucked | **startle up and out within 3–6 f, then sweep back toward the floor; one hand behind the head** (Z3) | wide eyes and open mouth from about 4 f; hold; a grimace after the impact | hips to the ground in **about 11 f (0.35 s)**; head about 16 f; show slowed 3× (about 1.2 s on screen) | CMU `90_18` RugPullFall, with arm and head acting from Z3 |

**General rules**
- Start the reaction **3–5 frames after** the push or slip (startle latency), never before.
- Bend the knees before impact.
- Overlap on any loose prop: the backpack and strap lag 2–4 frames (R4).
- The camera follows before the fall, cuts or orbits during it, and cuts on impact.

## 4. Motion-capture sources

### a) CMU Graphics Lab database: downloaded

`assets/mocap/cmu/` holds 10 BVH clips (7.8 MB) and a README with each subject/trial, its description,
the licence and notes:
- walk `02_01`;
- step-down off a stool `40_07` (trim it);
- stumbles `91_59`, `104_13`, `22_12`;
- falls forward `90_16` and backward `90_18`;
- run to a stop `16_08`, `127_05`, `104_56`.

**Source:** BVH by Bruce Hahne (cgspeed), via https://github.com/una-dinosauria/cmu-mocap.
**Licence:** free for research and commercial use.

The official site (mocap.cs.cmu.edu) only offers ASF/AMC and has no "curb" or "kerb" clip.

### b) Mixamo: needs the owner's sign-in to confirm names

- **Names not confirmed.** Mixamo's catalogue can only be browsed when signed in to Adobe, and no public
  list of names was found. So the names below are the usual Mixamo titles from memory and forum
  mentions. **Unverified**; check in Mixamo with the owner signed in:
  - "Stumble Backwards"
  - "Falling Back Death"
  - "Tripping"
  - "Fall Flat"
  - "Stumbling"
  - "Slipping"
  - "Stepping Down" / "Step Down"
  - "Falling Forward Death"
  - "Getting Up"
  - "Stand Up"
- **Licence:** Adobe's Mixamo FAQ says characters and animations are royalty-free for personal,
  commercial and non-profit projects. Don't redistribute the raw files on their own
  ([Adobe Mixamo FAQ](https://helpx.adobe.com/en/creative-cloud/faq/mixamo-faq.html)). Fine for
  monetised YouTube video.
- **This part stopped here:** it needs the owner to sign in to Mixamo.
