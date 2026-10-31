# Train step-off: research (2026-10-31)

How this was done:
- **Part 1:** YouTube searches in Chrome (`yt_reference.py`). The top competitors were played once and
  described from screenshots, with a local whisper transcript for each one's angle; nothing was kept.
- **Part 2:** frames sampled by seeking inside the player (no download). Timestamps are approximate,
  ±5–10 s. Where playback stalled, only the reliable span is listed.
- **Part 3:** web sources. Where a source is press rather than official, it is marked.

## 1. Differentiation check

View counts are as shown in YouTube search on 2026-10-31.

| # | Short | Channel | Views | Length | Angle | What's missing |
|---|---|---|---|---|---|---|
| 1 | [Why do people fall while getting off a moving train](https://www.youtube.com/shorts/RIRP9Me__CM) | @vsfactking5804 | 35M | 23 s | Hindi; a compilation of real Indian train clips. Vendors step off and run with the train; "feet stop, body keeps going". Ends on "Inertia of motion" | **The direct competitor.** No 3D, no slow-motion view of the body, no comparison of facing directions; presents running as the trick (borderline how-to); no "wait for the stop" |
| 2 | [Jumping Off Moving Trucks: The Physics Behind the Trick!](https://www.youtube.com/shorts/8AK4nHwfYT4) | @vt.physics | 39M | 33 s | English presenter on green screen, soldiers jumping back off a truck, a simple 2D velocity diagram: jump backward at the truck's speed and you land still | Trucks, not trains; no Indian setting; no falls compared |
| 3 | [Jumping against motion TOP demo](https://www.youtube.com/shorts/zllEVOn9NjM) | Prof. Paulo Flores | 32M | 11 s | Real stunt with an on-screen sum (+40 km/h − 40 km/h = 0); no narration | Explanation |
| 4 | [What happens if you jump backwards from a moving truck?](https://www.youtube.com/shorts/xOPa4MnP0M0) | @Slick3D | 30M | 20 s | **3D animation**: tumble forward, then the backward jump lands still | Closest in style; trucks only, one scenario, no human stakes |
| 5 | [What Happens If You Jump Against Motion?](https://www.youtube.com/shorts/OByRZGuh4AM) | @Unsolvedscience24 | 25M | 30 s | Compilation (soldiers, a truck, a ball, a Red Bull bike) with a "Galilean velocity" voice-over | Trains, a story, a safety ending |
| 6 | [She Outsmarted a Moving Train Using PURE Physics!](https://www.youtube.com/shorts/wUFqwY7_GIw) | VYAS EDIFICATION | 12M | 11 s | A real clip of a woman stepping off a moving Indian train and running; meme text; music only | No explanation; glamorises it |
| 7 | [What Happens When You Jump Inside a Moving Train?](https://www.youtube.com/shorts/R6gc-ejWCW4) | @abhashweb | 1.8M | 21 s | Hindi titles, 2D stick figures: jumping *inside* a train and on its roof | Not about getting off |
| 8 | [Jumping against motion at 80 km/h](https://www.youtube.com/shorts/4_W4BVERLP4) | Prof. Paulo Flores | 291k | 9 s | Stunt | Explanation |
| 9 | [How To Jump From Running Bus (3D Animation)](https://www.youtube.com/shorts/7bENLxhHLqs) | @Vikash_Toons | 41k | 10 s | Cheap 3D, how-to framing, and the physics is wrong ("you will fall straight down") | Correct physics, quality |
| 10 | [Bro Jumped Off A Moving Train… And Physics Saved Him](https://www.youtube.com/shorts/MwN_EKHfoqc) | VYAS EDIFICATION | 41k | 6 s | Real clip, meme text | Everything |

**Zack D Films:** searching "zack d films train" finds train Shorts (subway tunnel, asleep on the tracks,
standing near trains, shooting a gun on a moving train), but **none about stepping off a moving
train**.

**Gap for us.** Nobody combines:
- a polished 3D Mumbai local;
- the same step-off shown **facing backward, sideways and forward** (only #1 hints at the body's
  motion);
- an inertia "ghost" that shows the body keeps going while the feet stop;
- a non-how-to ending ("even the best way can fail, wait for the stop").

Truck "jump against motion" videos get the most views (25–39M), so a short nod to the counter-intuitive
"facing back is worse" idea could ride on that interest. Risk: #6 and #10 show the behaviour approvingly;
our framing must stay "why you fall", never "how to".

## 2. Reference footage (watch only)

| Need | Video | Use |
|---|---|---|
| Local arriving at a platform | [Mumbai Local Train Arriving to the Platform – 4K](https://www.youtube.com/watch?v=w0M8Yj2KQMc) (Train Enthusiast, 1:09) | **0:10–0:30** platform-level view across tracks: canopy, overhead wires, footbridge, platform edge. **0:30–0:45** a white/purple EMU rolls in on the far platform, with people at the open doors at 0:40 |
| Doors, people at the door, platform edge at feet level | [Mumbai Local Train Kurla Station](https://www.youtube.com/watch?v=rBMv_zVDsCw) (Mumbai Max, 2.7M views) | **0:15** an empty platform with a purple/white Central Railway EMU; **0:30** an EMU side-on with open doors and people at them; **1:00** a low camera on the platform edge with the yellow/maroon cab front and passengers' feet: **the edge and the gap**. Playback stalled after about 1:00 |
| Crowd inside the coach | [Local Train Crowd at 6 PM – Rush Hour](https://www.youtube.com/watch?v=s9LdDRpRvxg) (Sahastra, 8:28) | **0:00–0:30** packed interior, grab handles, people pressed towards the door; stalled after that |
| Drone over locals | [IRFCA: Stunning aerial drone footage](https://www.youtube.com/watch?v=cAsrzcDtKf4) (Dhawal Poladia, 1:50) | Mulund: **0:15–0:45** a wide track bed with an EMU running through, the high-rise skyline behind, a low pass at 0:35. A good template for the drone opener |
| Drone over locals (2) | [IRFCA: Indian Railways aerial drone view](https://www.youtube.com/watch?v=UsBaqflxfIo) (Dhawal Poladia, 1:46) | **0:10–0:55** an oblique aerial of parallel tracks with several EMU rakes moving; after 1:00 freight wagons |
| Motorman's cab and speedometer | [Inside view of the motorman cabin of a Mumbai local](https://www.youtube.com/watch?v=ejBpsPNeGzo) (Deepakkumar Yadav, 3:06) | **0:10** switch panel; **0:20** master controller; **1:00–1:10** close-up of the **analogue speedometer** (white dial, black needle, blue console) with the motorman's hand on the brake handle. Our dial reference |
| Speed while leaving a platform | [EMU Local Acceleration Sound + Speedometer](https://www.youtube.com/watch?v=mYOsuMiql_M) (Sam Trains, 1:20) | A GPS speed overlay while leaving a platform at night: **1 km/h at 0:05, 11 at 0:10, 19 at 0:15, 30 at 0:25, 47 at 0:35, 55 at 0:45**. Location not stated (signs suggest it may not be Mumbai). It shows how fast "slow" becomes 20 km/h |
| Cab-front view of a crowded platform | [Mumbai Local Cab View Part 1](https://www.youtube.com/watch?v=KaFUy2AIBCg) (Great Indian Central Railway PCD, 10:14) | **0:40** the view from the cab as it stands at a crowded platform: the platform edge line, crowds at the edge, the canopy. Stalled after that |

Also seen in search (not sampled): [Railfan Junction: departing CSMT 4K](https://www.youtube.com/watch?v=RihMBER-8zQ)
and [Rishad Ghiara: cab ride Churchgate–Virar](https://www.youtube.com/watch?v=-4u8JqZAAXE) (1:16:45, a
real-time cab view).

## 3. Facts and sources

### Speed entering or leaving a platform

No official "platform entry speed" was found for Mumbai locals; through stations have no standard
platform limit. What exists:
- **Approach limits (press):** 15 km/h at crossovers into some Central Railway platforms; 10–15 km/h
  near CSMT after derailments; Churchgate approach raised from 20 to 30 km/h; Dadar and Bhayander
  crossovers raised from 15 to 30 km/h ([FPJ: Harbour line restriction](https://www.freepressjournal.in/mumbai/speed-restriction-to-delay-trains-on-harbour-line),
  [FPJ: WR speed increases](https://www.freepressjournal.in/mumbai/mumbai-western-railway-to-enhance-and-increase-speed-in-train-operations-in-certain-sections-including-churchgate),
  [Lokmat Times: CSMT 10 km/h caution](https://www.lokmattimes.com/maharashtra/mumbai-local-train-update-harbour-line-trains-running-30-to-40-minutes-late-after-two-derailments-a517)).
- **Performance:** Mumbai AC locals accelerate and brake at about **0.54 m/s²**
  ([FPJ citing MRVC](https://www.freepressjournal.in/mumbai/mumbai-mrvc-to-procure-new-238-ac-locals-having-inbuilt-infotainment-and-cctv-system-with-better-performance-characteristics)).
  A three-phase EMU training note gives 0.84 m/s² braking below 50 km/h
  ([Scribd EMU notes, unofficial](https://www.scribd.com/document/806422767/Introduction-to-EMU-MEMU)).
- **Derived (ours, not a citation):** at 0.54–0.84 m/s², a train 2 s from stopping is doing about
  4–6 km/h, and 5 s from stopping about 10–15 km/h. Pulling away from rest, it reaches about 20 km/h
  within about 30 m (v = √(2ad)). So "slow" covers roughly 5–20 km/h at the doors: a brisk walk to a
  sprint. Footage check: the GPS clip above reaches 19 km/h about 10 s after starting to move.
- **Platform length:** a 12-car platform is about **270 m**, a 15-car one about 330 m
  ([FPJ, Sep 2026](https://www.freepressjournal.in/mumbai/dadar-station-platform-4-to-be-extended-for-15-coach-fast-locals-under-western-railway-expansion-plan)).

### Deaths and injuries (Government Railway Police data via press)

- **2025:** **2,287** deaths on the suburban network, 7 % fewer than 2024. About half (1,063) were
  track crossing ([Mumbai Live](https://www.mumbailive.com/en/civic/mumbai-local-train-fatality-falls-7-in-2025-track-crossing-and-overcrowding-main-reasons-for-death-91328)).
- **January–May 2025** (from a Right to Information request): 922 deaths, of which **210 fell from
  running trains** ([Free Press Journal](https://www.freepressjournal.in/mumbai/922-commuter-deaths-in-mumbai-locals-in-just-5-months-including-210-fell-from-running-trains)).
- **2014 to May 2025:** **6,760 died and 14,257 were injured falling from trains**; nearly 30,000
  deaths on the network in 11 years (police data via PTI:
  [The Print](https://theprint.in/india/nearly-30000-deaths-on-mumbai-suburban-train-network-in-11-years-police/2653246),
  [The Week](https://www.theweek.in/wire-updates/national/2025/06/10/bom29-mh-train-deaths.html)).
- **Caveat:** "fell from trains" mixes overcrowded doorways with falls while stepping off; no source
  splits out falls while getting off.
- **Script-safe line:** "In Mumbai, hundreds of people die every year falling from moving trains." That
  is about 500 a year on the 2014–2025 average.

### Law (Railways Act, 1989)

- **No section specifically bans getting on or off a moving train.**
- The closest is **s.156**: travelling on the roof, step or footboard after a railway servant's warning;
  up to 3 months' prison and/or a ₹500 fine
  ([s.156 text, AdvocateKhoj](https://www.advocatekhoj.com/library/bareacts/railways/156.php),
  [CourtBook](https://courtbook.in/railways-act-1989/section-156)). Official text:
  [India Code, Railways Act 1989](https://www.indiacode.nic.in/handle/123456789/1879) (not fetched,
  certificate error).
- Railways enforce s.156 in drives against footboard riding
  ([Pune division, 105 booked](https://www.mypunepulse.com/?p=154348)).
- Railway safety notices also warn against boarding or de-boarding moving trains, without citing a
  section ([Southern Railway PR notice](https://sr.indianrailways.gov.in/cris//uploads/files/1731913051552-No.PUB-MAS-2022-04-09.pdf)).
- **Script:** don't claim "it's illegal". Say "railways warn never to board or leave a moving train".

### Physics

- **Newton's first law:** "A body at rest remains at rest, or, if in motion, remains in motion at a
  constant velocity", unless a net external force acts
  ([OpenStax College Physics 2e §4.2](https://openstax.org/books/college-physics-2e/pages/4-2-newtons-first-law-of-motion-inertia)).
  Also [HyperPhysics, Georgia State University](https://hyperphysics.gsu.edu/hbase/Newt.html): "an
  object will remain at rest or in uniform motion in a straight line unless acted upon by an external
  force."
- **The getting-off case** is the standard NCERT Class 9 example (Force and Laws of Motion: the feet
  stop on touching the ground while the upper body keeps moving, so you fall forward). The official
  NCERT PDF could not be fetched (certificate error), so this rests on study-guide summaries
  ([Careers360](https://learn.careers360.com/school/question-a-person-trying-to-get-down-from-a-running-bus-falls-forward-this-is-an-example-of-30850/),
  [Vedantu](https://vedantu.com/question-answer/dangerous-to-jump-out-of-a-moving-bus-class-9-physics-cbse-60a344a4d4529b28fc911d55)).
  **To do:** check the wording in the NCERT book.
- **For our scenarios:**
  - **Facing forward:** the feet stop and the upper body pitches forward, but a step can catch it.
  - **Facing backward:** the feet stop and the body keeps going in the direction it isn't looking, so it
    falls backward with no step to save it. Worst.
  - **Sideways:** you fall sideways or twist; legs can't step that way fast.

  These are standard first-law reasoning; no source measures them. Have Codex check the claims at G1.
