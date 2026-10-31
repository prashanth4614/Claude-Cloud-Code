---
name: production-process
description: The gated production process for every new Short, from idea to upload. Covers brainstorming with the owner, fact-checking, the script and screenplay with Codex review, voice lock, pre-frame QA, frame tests, the Mac animatic with a .blend for the owner, sound design, the final render and the post-launch review. Each gate has inputs, outputs, owners, pass criteria and a sign-off, so errors are caught early and iterations drop. Use whenever starting a new video, moving a video to its next step, or deciding whether a change is allowed; works with the shorts-craft (what good looks like) and sfx-design (sound) skills.
---

# Production process: gates from idea to upload

**Why:** the pilot took 11 mixes and several re-renders because problems were found late (voice after
animation, the look after the render, the 2D diagram after the final render). Every gate below catches
one class of problem while it is still cheap to fix.

**How:**
- Each video gets a tracker, `shorts/<video>/production.md`, copied from `templates/production.md`.
- A gate passes only when its checks pass **and** the owner writes "approved" (a chat reply is fine;
  record it in the tracker with the date).
- What "good" means comes from the `shorts-craft` skill (the formula, the house look, the
  one-3D-world rule) and the `sfx-design` skill (sound).

**Who does what** (helper sessions: CLAUDE.md):

| Role | Does |
|---|---|
| Owner | ideas, decisions, the approval at every gate |
| Claude (this session) | drafts, builds, QA, coordinating and monitoring the helpers |
| Codex helper (Mac) | an independent review at the gates marked **Codex** (`ask_codex.sh`, with images and full context) |
| Web helper (Mac) | references, research, royalty-free sound search |
| Render worker (Mac) | key frames, animatics, the review `.blend`, the thumbnail |
| Cloud voice worker | ElevenLabs takes, SFX and music, mixes |
| Cloud RunPod worker | the final render |

## The cost of going back (the rule that cuts iterations)

Once a gate passes, its outputs are **locked**. Changing a locked item sends the video back to that
gate, and every later gate re-runs:

| Locked at | Item | What a change costs |
|---|---|---|
| G2 | facts, script | a new voice take and new timing (G4 onwards) |
| G3 | screenplay, shot list, transition chain | new key frames and animatic (G5 onwards) |
| G4 | voice | re-timed animation (G5 onwards); never after G7 |
| G6 | key frames, look | a new animatic |
| G7 | the animatic (picture lock) | only sound and grade can change after this |
| G8 | sound | a remix only (cheap) |
| G9 | final frames | a paid re-render: avoid |

Decide in words before paying in pixels.

---

## G0 Idea: brainstorm with the owner

- **Brainstorm:** Claude brings 5-8 candidate questions in the channel's range (any curious topic).
  Each gets a one-line hook, the hidden-world device it would use (shorts-craft §1 toolbox) and the
  "hear it" moment.
- **Differentiation check (web helper):** what Shorts already exist on it (Zack and others), which
  angles are taken, and what fresh angle we have.
- **Output:** the chosen question and angle in the tracker. **Owner approves.**

## G1 Story and facts: brainstorm, then check every claim

- **Story:** the beat outline (shorts-craft §1: hook, stakes, cause, payoff at 65-75%, extension,
  takeaway, loop line), worked out with the owner. Before any prose, agree what the viewer *feels*
  at each beat.
- **Facts:** every factual claim goes into `shorts/<video>/facts.md` (template:
  `templates/facts.md`), with **two reputable sources** (encyclopaedia, government or medical site,
  university, a peer-reviewed review).
  - Simplifications are written down as such, with why they're still true enough.
  - "Common myths" are checked so we don't repeat one.
- **Codex** reviews the outline and fact table: accuracy, missing caveats, engagement, how well it
  follows the formula.
- **Pass:** every claim sourced; no open accuracy issue; Codex's objections resolved or rejected with
  a reason. **Owner approves.**

## G2 Script

- **Draft:** written to shorts-craft §1: 30-35 s, 85-95 words, second person, chained "That's
  because / But / And when", one 3D metaphor, a takeaway, and a loop line.
- **Read-aloud check:** time it at 170 wpm, mark the 3-5 stressed words (CAPS), and fix the
  tongue-twisters (the pilot's "pop" was misheard as "poke").
- **Codex** reviews the script against the fact table and the formula. Give it the facts, the beat
  outline and two Zack reference transcripts or summaries (`shorts/reference/`).
- **Pass:** every sentence traces to the fact table; the word count and timing are in range; the hook
  works on its own. **Owner approves → the script is locked.**

## G3 Screenplay: how we present it

- **Shot list** (`shots.yaml`): 9-12 shots, for each the line it covers, the world, the camera move, Max's
  expression and what the viewer must understand.
- **The transition chain,** written as one line with the physical link for each cut (shorts-craft §3:
  match position within 10%, continuous motion, screen direction).
- **Visual design:** the hidden-world device, the one 3D world (no 2D inserts), the colour code, the
  in-world metaphor object, the meter or label plan (2-3 labels at most), and the "hear it" moment.
- **Rough boards:** one Workbench still per shot from blockout geometry, as a contact sheet. These are
  minutes of work, not renders.
- **Asset list:** every character, prop and set the shots need, each with its source (shorts-craft §11),
  licence, cost and restyle notes. The web helper finds and verifies them. Anything paid, CC-BY-SA or
  AI-generated needs the owner's yes here.
- **Codex** reviews the shot list, transition chain and boards (with images).
- **Pass:**
  - every line has a picture that explains it;
  - the transition chain has no unmotivated cut;
  - the one-world crop test passes on the boards.

  **Owner approves.**

## G4 Voice: lock it before animating (moved earlier than the pilot)

The animation is timed to the words, so the voice comes first.
- **Audition:** stability 0.0 against 0.5 on about 10 s; pick the better one.
- **Full take:** the whole script as one take (cloud voice worker).
- **Gates:** `voice_check.py` (pace, coverage, gaps, pitch span, stress, ASR of the hook).
- **Codex** reviews the numbers plus the transcript and stress marks.
- **Pass:** the voice gates pass, and the owner listens on a phone. **Owner approves → voice locked**
  (the timing file drives the animation).

## G5 Pre-frame QA: before any frame is rendered

Run on the built `.blend`, with no rendering:
- `shorts/blender/qa_scene.py`: foreign sets in frame, holes, a camera inside a surface, bad scales.
- **Camera checks:**
  - no turn over 90° within a shot;
  - screen direction holds across cuts;
  - match-cut subject position within 10% of the frame across each linked cut;
  - the camera never clips into geometry;
  - speed ramps only inside transitions.
- **Depth and clarity:**
  - the subject separated from the background (light, colour code, depth of field only on Max);
  - nothing important in the bottom 22% (captions and the Shorts interface);
  - labels ≤ 3 and attached in 3D.
- **The one-3D-world check:** no flat 2D planes facing the camera as diagrams; the palette is
  within the house look.
- **Codex** reviews the QA report and the camera and transition code paths.
- **Pass:** no QA failures, or each one waived by the owner with a reason. (Extend `qa_scene.py` with
  the camera, transition and safe-zone checks as each new video needs them.)

## G6 Frame test: key frames, reviewed by Claude and Codex

- **Render (render worker, Mac):** for every shot its first, middle and last frame, plus both sides of
  every transition. Low samples, but the final look: Cycles or EEVEE, then
  `house_grade.py frames ink_amber`.
- **Review sheets:** contact sheets with the script line, the shot intent and the transition link
  printed under each pair.
- **Claude, then Codex,** review them (with images and full context): readability at phone size,
  transition alignment, depth and clarity, Max's expressions, the look, the crop test.
- **Pass:** both reviews have no open "must fix"; the owner sees the sheets. **Owner approves.**

## G7 Animatic and review `.blend` on the Mac: picture lock

- **Low-res full film** with the locked voice (render worker; Workbench or quick EEVEE).
- **The `.blend` for the owner:** a packed copy, `out/<video>/<video>_review.blend`, with
  sound and markers per line. The owner opens it in Blender and plays or scrubs the timeline. Nothing
  renders.
- **Claude** checks the animatic: timing against the voice, the action on the right word, the
  transitions, holds that are too short or too long.
- **Pass:** the owner has watched it and approves. **Picture locked.**

## G8 Sound: SFX, beds, music and final voice treatment

- **Design:** per the `sfx-design` skill: the cue sheet on picture beats, the "hear it" moment, beds,
  and music (if any).
- **Sources:**
  - ElevenLabs SFX or Music (cloud voice worker);
  - or royalty-free libraries found by the web helper, with each **licence recorded in
    `assets/LICENSES.md`**.
- **Codex** reviews the cue sheet and the audit numbers.
- **Checks:** `audit_mix.py` passes; the owner listens on a phone and on headphones. **Owner approves.**

## G9 Final render

- **RunPod worker:** `--dry-run`, then a bench of 8 frames per set (cost and time estimate given to the
  owner), then the full render on the owner's go. Pods are always deleted.
- **Automatic frame QA:** black or corrupt frames, flicker (big frame-to-frame changes outside cuts),
  any caption over a face, and a spot-check sheet at 1 fps reviewed by Claude.
- **Assemble:** grade, mix, encode; true peak ≤ -1.5 dBTP; -14 LUFS.

## G10 Publish and learn

- **Upload pack:** the thumbnail (render worker), title, description, hashtags, AI-disclosure answer
  and pinned comment.
- **After 48 h and 7 days:** the owner shares retention and swipe-away numbers. Claude notes where
  viewers dropped and why.
- **Feed the lessons back:** every lesson becomes a rule in `shorts-craft`, `sfx-design` or this
  skill. That's how the next video starts better.
