# Zack D Films vs our ear-pop pilot (v11): frame-by-frame comparison (2026-10-31)

Written independently of Codex (its answer: `shorts/tools/codex/answers/008-zack-vs-ours.md`).

**Sources**
- Three @zackdfilms Shorts, each played once in Chrome (`shorts/tools/yt_reference.py`), with
  screenshots every 0.25 s and the player's own audio recorded:
  - **Z1** = Why Your Ears Pop On A Plane (33.1 s);
  - **Z2** = Why Eardrums Burst From Loud Noises (31.8 s);
  - **Z3** = How Eyewash Stations Work (29.0 s).
- **Ours** = `shorts/reference/ours/pilot_v11_sheet_*.jpg` (47.4 s), plus our mix rendered from
  `mix.py` at HEAD.

**Measuring.** Zack's frames are described in words only; their captures, transcripts and sheets stayed
local and are deleted. All four videos went through the same steps:
- voice split from the rest with demucs;
- word timings from faster-whisper (small.en);
- pitch from librosa pyin (60–400 Hz).

## 0. The numbers side by side

| | Z1 | Z2 | Z3 | **Ours** |
|---|---|---|---|---|
| Length | 33.1 s | 31.8 s | 29.0 s | **47.4 s** |
| Words | 85 | 83 | 81 | 108 |
| Sentences | 4 | 4 | 6 | 12 |
| Words per minute while speaking | 166 | 166 | 187 | 177 (the coordinating session's figure: 162) |
| Words per minute overall | 154 | 157 | 168 | **137** |
| Share of runtime with voice | 96 % | 96 % | 95 % | **81 %** |
| Median pitch | 189 Hz | 179 Hz | 151 Hz | 128 Hz |
| Pitch span p5–p95 (pyin) | 17.6 st | 18.7 st | 18.6 st | **7.4 st** |
| Per-syllable pitch span p5–p95 | 16.5 st | 19.2 st | 16.9 st | **6.3 st** |
| Pitch span per sentence (median, range) | 17 (15–19) | 18 (16–20) | 18 (13–21) | **5.4 (3.0–9.5)** |
| Pitch jump on stressed words | +4 to +12 st | +4 to +12 st | +5 to +18 st | **+2 to +4 st** |
| Gaps between sentences | 0.28 / 0.38 / 0.00 s | 0.24 / 0.52 / 0.00 s | 0.28–0.46 s | 0.38–0.80 s, one 1.5 s |
| Sound-effect onsets per 10 s | 7.6 | 10.4 | 6.2 | **1.9** |
| Cuts per 10 s | 3.9 | 1.25 | 3.8 | 4.4 |
| Ending | the payoff line, a loop into the opening | back on the face, a bookend | thumbs-up on the payoff line | **a "Follow" card** |

**Notes on the numbers**
- **Pitch** is a lower bound on the gap. Pyin finds few voiced frames in Zack's processed voice, and a
  few syllables may be tracked an octave off. But there are no frame-to-frame jumps, and the syllable
  medians spread smoothly from about -9 to +12 st. Even the most conservative cleaning gives 8–9 st for
  Zack against 6.4 st for ours.
- **Gaps:** a "0.00" gap means a sentence runs straight into the next with no breath. Our gaps measure
  wider than the script's 0.28 s because each TTS clip carries its own leading and trailing silence.
- **Sound effects:** the same detector counts only 9 onsets in our mix, against the 31 cues `mix.py`
  places. Ours sit too far under the beds to register as hits.
- **Clarity:** whisper transcribes our hook as "why your ears **poke** on a plane". It also heard line 4
  as "**That** as the plane climbs" instead of "But". The clone's plosives are soft.

## 1. Storytelling and writing

**Zack (Z1)**: four long sentences, each one link in a cause-and-effect chain.
1. **0–8 s, the situation and the felt stakes:** the plane climbs, air pushes on your eardrums "until it
   feels like they're about to burst".
2. **8–18 s, the cause** ("That's because…"): the outside pressure drops fast.
3. **18–26 s, the twist and the payoff** ("But before it does actually burst…"): a tube to your throat
   releases air "with a pop", at **26 s, 79 % of the way in**.
4. **26–32 s, the reverse case** (going down), ending on the tube popping air back in. That runs straight
   into the opening line, so the video loops.

**Zack's writing habits**
- Every sentence is second person ("your eardrum") and present tense.
- Every Short has a danger word: burst, rip, tear, blind, painfully.
- The connectors carry the story: "That's because", "But before", "And when".
- No question hook, no definitions, no call to action.
- Z2 has the same shape (danger → cause → damage → it heals); Z3 opens with an order ("Hold open your
  eyelids…") straight into the action.

**Ours**: 12 short sentences that read as a lesson.
1. A generic question hook ("Ever wondered why…?").
2. A definition ("Behind your eardrum sits a tiny pocket of air…").
3. The resting state ("On the ground…").
4. Then the climb, the bulge, the felt symptom (20 s), the tube, and the POP at **31 s (65 %)**.
5. Then a second act: descending, the remedies, and a follow card.

The stakes are never stated: nothing will burst or hurt. "Muffled, blocked feeling" is mild.

**The gap:**
- They reach the danger in about 6 s; we never state it.
- Our payoff lands earlier in percentage terms, but 31 s in absolute time is longer than any of Zack's
  Shorts.
- Our remedies line is genuinely useful; Zack's ear Short has nothing like it. That is a place to beat
  him if it is kept short.

## 2. The opening shot (first 1.5 s)

**Z1, 0.25 s steps**
- **0.00–0.44 s:** an airliner climbs left to right across a bright sky-blue frame, with a translucent
  blue arrow along its path. By 0.44 s it passes huge and close to the lens.
- **0.69 s:** a blurred whip past the fuselage windows.
- **0.94 s:** a cut inside the cabin. A passenger sits in a wide shot, already holding his ear and
  grimacing.
- **1.20 s:** a slight push in.
- **1.44 s:** a close-up of the pained face, brows knotted and teeth gritted, hand on his ear.
- **1.69–1.94 s:** the camera pushes into the side of his head. Skin, then skull, then tissue peel away
  in motion blur.
- **2.2 s:** we are in an anatomical cutaway of the ear.

So in 2.2 s: the situation, the person, the pain, and the inside of the body.

**Z2:** frame 0 is already mid-action. A man wincing with his hand on his head, and a translucent
sound-wave ring sweeping through his face, timed to sub-bass booms that are louder than the voice. At
1.95 s an extreme blurred close-up of his scrunched face (the push into the ear); at 2.4 s the
cutaway.

**Z3:** frame 0 is an extreme close-up of chemical-burned, bleeding eyes held open by two hands. The
camera pulls back continuously to 1.2 s; at 1.45 s a hard cut to the woman at the eyewash station, with
water already flowing.

**Ours**
- **0.0–0.6 s:** a close-up of Max with eyes shut, brows barely lowered, mouth slightly open. It reads
  as sleepy, not pained, and there is no hand on his ear.
- **1 s:** a jet engine close-up.
- **2 s:** the jet over clouds.
- **3 s:** Max calm, looking up, with no caption.
- **4 s:** a pink tunnel.

The pain is gone by 0.6 s, and the entry into the body has no outside-to-inside link the viewer can
follow.

## 3. Transitions

| | Hard cuts | Whip pans with blur | Push-through into the body | Pull back out | Dissolve | Slide wipe |
|---|---|---|---|---|---|---|
| Z1 (13 cuts) | about 9 | 2 (0.7 s, 8.4 s) | 1 (1.7–2.2 s) | – | 1 (26.6 s, cutaway → jet) | – |
| Z2 (4 cuts) | – | – | 2 (1.9 s, 13.5 s) | 1 (28.5 s) | – | 1 (6.9 s) |
| Z3 (11 cuts) | about 10 | – | – | pull-back opening | – | – |
| Ours (21 cuts) | about 19 | – | 1 (S02 into the ear opening, then a dip through black) | – | – | – |

**Outside → inside.** Zack always enters through the character's own head, with layers peeling in about
0.5 s, and lands in a side cutaway that shows where we are: the canal, the eardrum, the ossicles, the
cochlea. Z2 also pulls back out to the same face at the end.

We push into the ear opening, go through black, and come out in a tube with no landmarks. The viewer
loses track of where they are.

## 4. Camera movement

**Zack**
- Every shot moves slowly: a push-in or a slow orbit around the cutaway.
- No handheld shake, and no long fly-throughs.
- Fast motion appears only inside transitions.
- Each Short has one long anchor shot of the process (Z1: the cutaway at 2–8 s and 16–21 s; Z2: the
  eardrum at 13.7–28.5 s, one take).
- The camera **looks at** the process from outside, so you watch the eardrum bulge, tear and heal.

**Ours**
- The camera **travels through** tunnels (4–9 s, 14–17 s, 23–31 s, 35–37 s), so the process happens
  around the camera instead of in front of it.
- Our longest shot is 4.1 s.
- The diagram shots are static.

## 5. Voice

Pace while speaking is about the same: 166–187 words per minute for Zack against our 162–177. The
difference is melody and continuity.

**Zack's voice**
- Bright and high-pitched (150–190 Hz median).
- Sing-song: about 17–19 st of pitch span, with jumps of +4 to +12 st on the stressed word in nearly
  every phrase ("fast", "burst", "tube", "Suddenly", "blind").
- Sentences run into each other with gaps of 0–0.4 s, so the voice fills 95–96 % of the runtime.

**Ours**
- Lower (128 Hz) and even: 7.4 st overall, 5.4 st per sentence (3.0 on the remedies line), emphasis
  only +2 to +4 st.
- Gaps of 0.4–0.8 s, with a 1.5 s pause after the POP; the voice fills 81 % of the runtime.
- The hook's key word "pop" is misheard by speech recognition.

## 6. Sound effects and music

**Zack**
- No score in Z1 or Z2; only sound design. Z1 has low rumbles and whooshes plus a tonal drone under
  the "pressure difference" section. Z2 has sub-bass booms in the hook, then a low bed and a ringing
  tone after the rupture.
- Z3 has licensed music about 20 dB under the voice.
- A whoosh on nearly every cut, about 6–10 audible hits per 10 s.
- The payoff hit sits about 3 dB under the voice peak.
- A dip of about 10 dB in the background just before the payoff.
- No ducking.

**Ours**
- A score, room tones, a pressure drone with the muffle effect, and 31 cues.
- Only about 9 cues register as hits; the rest are buried. Our POP and the muffle → clear release is
  better designed than anything in Z1, but the routine hits are inaudible.

## 7. The ending shot

| Short | Last shot | Last line |
|---|---|---|
| Z1 | the cutaway, the tube puffing air back | runs straight into the opening line, a loop |
| Z2 | the same wincing man as at 0 s, a bookend | "…back to normal" |
| Z3 | the woman turns to camera with a thumbs-up | the payoff line ("…from going blind") |

None of the three has an on-screen call to action.

Ours ends on Max's thumbs-up plus a 1.9 s "Follow for more weird body facts" card after the last word.
That is silent dead air, and it breaks the loop.

## 8. Colour grading and look

**Zack**
- High-key and soft.
- Saturated sky-blue or teal backgrounds behind characters and cutaways.
- Anatomy like a medical model: cream porous bone, glossy pink and red tissue, yellow fat and nerves.
- Strong warm–cool separation (warm anatomy on cool backgrounds).
- Shallow depth of field on close-ups, motion blur on fast moves.
- One consistent look across every shot of a Short.

**Ours**
- **Four looks:** a neutral grey cabin; monochrome pink/red tunnels (low contrast, no colour
  separation); a flat navy diagram with text labels; a dark low-poly night city (33–34 s, the weakest
  frames).
- The jet-over-clouds frames are good. Max's skin is acceptable but slightly waxy.

## 9. How things are explained

**Zack**
- One cross-section, used repeatedly. The process is animated on it: the eardrum bulges outward, the
  tube glows as air rushes down it, the eardrum is pushed inward.
- One clear graphic metaphor: an "Air pressure" thermometer next to the ear, its bar dropping (Z1 at
  8.4–11.4 s).
- Translucent arrows for air and for the plane's direction.
- Z3 uses an on-screen 15-minute timer.
- On-screen text is limited to the one gauge label.

**Ours**
- Air "molecule" spheres in tunnels (abstract).
- A clear navy diagram with four labels and OUTSIDE = INSIDE / INSIDE > OUTSIDE titles. It is the
  clearest teaching in the video, but it looks like a different film.
- The balloon metaphor.
- No view that ties the inside back to Max's head.

## 10. Top 8 fixes, ranked by impact per cost

1. **End on the payoff and loop: drop the follow card and the dead air.**
   - Cut the S13 card; end within 0.5 s after the last word.
   - Better still, end on POP / Max's relief and let it loop to the opening.
   - **No re-render**: edit and mix only.
2. **Make every hit audible.**
   - Raise routine cues about 4 dB and add a whoosh on every cut (see `zack_style_study.md` §2).
   - Then judge on a phone speaker. Treat the onset count (at least 6 per 10 s) as a check, not a
     target; don't add sounds just to raise it (Codex's caution, and it is right).
   - Keep our POP and muffle release; that is where we already beat Zack.
   - **No re-render**: `mix.py` only.
3. **Captions in plain white**, with at most one yellow keyword, and no fully gold chunks.
   - **No re-render of the film frames.** It is an EDIT text-strip change and a re-encode, if the
     edit's text strips can be re-rendered over the cached frames.
4. **Re-voice with melody and run-ons.**
   - ElevenLabs v3 with stability on Creative (low), style up, and delivery tags per line
     ([excited], [dramatic], [whispers] before POP).
   - Write the stressed words in capitals. Run sentences together with 0.1–0.25 s gaps.
   - Re-record the hook until "pop" is unmistakable (check it with whisper).
   - Audition stability 0.0 against our 0.5. Rough aims: per-sentence span 10 st or more, stressed
     words +5 st, voice share 90 % or more. Don't aim for Zack's measured ~18 st, which octave errors
     may inflate.
   - **Needs a re-render**: shot timing follows the voice. ElevenLabs credits only with the owner's OK.
5. **Rewrite to Zack's chain at 30–35 s.** Open mid-action with felt stakes ("As the plane climbs, the
   air trapped behind your eardrum pushes out until it feels like it could burst"), then "That's
   because…", then "But before it does…" with the POP at about 70 %. Then a 2-sentence descent plus the
   swallow/yawn tip, ending on a line that leads back into the opening.
   - **Needs a re-render** (do it together with fix 4).
6. **Opening 0–2 s.**
   - Max in clear pain from frame 0, hand on his ear: a stronger wince, which the film needs anyway (see
     the EAR_POP thumbnail face).
   - Jet passing the lens with a boom.
   - By about 2 s, push through his cheek with the skin layers fading into the ear cutaway; no dip
     through black.
   - **Needs a re-render.**
7. **One cutaway world instead of tunnels plus diagram.**
   - A side cross-section of the head (canal → eardrum → middle ear → Eustachian tube → throat) in a
     medical-model style on a teal background.
   - The camera looks at it with slow pushes. Animate the bulge, the glowing tube and the POP on it.
   - Fold the diagram's labels in as 2–3 in-world tags.
   - Keep at most one short tunnel ride as a transition.
   - **Needs a re-render** (the biggest build).
8. **One look.**
   - A brighter, warmer key on Max and a soft sky-blue/teal background behind him.
   - Shallow depth of field on his close-ups.
   - Replace the low-poly night city with a daytime descent through clouds (reuse the jet and cloud
     set), or cut it.
   - **Needs a re-render.**

**Where we can beat Zack rather than copy him:**
- **Sound:** the felt muffle → POP release; Zack never makes you *hear* the symptom.
- **A practical tip:** the swallow/yawn/chew close-up is actionable; Zack's ear Short has none.
- **A label system in-world** that teaches more clearly than his single gauge.

Keep all three, but inside his pace and look.

## 11. Codex 008 vs this reading

Codex's answer is in `shorts/tools/codex/answers/008-zack-vs-ours.md`.

**We agree on**
- Removing the follow tail (both rank it #1).
- One persistent anatomical cutaway instead of pink tunnels.
- Holding Max's discomfort longer, with his ear, hand and face in frame.
- Replacing the dip through black with a reveal through the skin.
- One longer, continuous mechanism shot.
- Cutting or rebuilding the night city.
- Keeping Max's thumbs-up gesture.

**Codex adds**
- `build_previz.py` `build_edit()` hard-codes the black dip, and the `match_cut:window` in the YAML is
  never implemented.
- `audio.py` adds its 0.28 s gap on top of each take's own padding (`engine.py`). That matches our
  measured gaps of 0.38–0.80 s, not 0.28 s.
- S04 turns the camera round about 168°, which flips the viewer's orientation.
- Material values in `sets/ear.py` to try first: less clear-coat, more roughness.

**Where I'd still push harder**
- **Voice.** Codex calls the voice a "modest" gap. Pace is modest; melody is not. Even after the
  conservative octave cleaning, Zack is about 8–9 st per syllable against our 6.4. The ASR mishearing
  of "pop" in the hook is a concrete defect.
- **Stakes.** Codex doesn't want Zack's repeated rupture threat. Agreed, but one stated stake ("feels
  like it could burst") is what makes his first 6 s land, and our script has none.
