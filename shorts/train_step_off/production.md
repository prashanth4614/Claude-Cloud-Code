# Why you fall stepping off a slow train: production tracker

Process: `.claude/skills/production-process/SKILL.md`. A gate is done when its checks pass **and** the
owner approves (record the date). Changing a locked item reopens its gate.

| Gate | Status | Approved (date) | Notes / links |
|---|---|---|---|
| G0 Idea and angle | ☑ | 2026-10-31 | see G0 below; web differentiation check pending |
| G1 Story and facts (Codex) | ☑ | 2026-10-31 | `story.md` rev 2, `facts.md`; Codex 017 objections all applied |
| G2 Script locked (Codex) | ◐ | | `script.md` draft 2 (Codex 018 applied); waiting for the owner's lock |
| G3 Screenplay, shot list, transition chain, boards (Codex) | ☐ | | `shots.yaml`, boards sheet |
| G4 Voice locked | ☐ | | take id, `voice_check.py` result |
| G5 Pre-frame QA (Codex) | ☐ | | QA report, waivers |
| G6 Key-frame test (Claude + Codex) | ☐ | | sheets, must-fix list |
| G7 Animatic + review .blend: picture lock | ☐ | | `out/train_step_off/train_step_off_review.blend` |
| G8 Sound (Codex) | ☐ | | `audit_mix.py` result, licences |
| G9 Final render | ☐ | | bench cost/time, frame QA |
| G10 Publish + 48 h/7 d review | ☐ | | retention notes, lessons added to skills |

## G0: idea and angle (owner approved 2026-10-31)

- **Question:** why do you fall when you step off a slow-moving train?
- **Angle:** physics first ("why you fall"), never a how-to. Facing back vs sideways vs forward, then
  "even the best way can fail", then wait for a full stop. (YouTube harmful/dangerous policy: no
  instructional framing in the title, hook or captions.)
- **Setting:** a Mumbai local train (EMU) arriving at a suburban station.
- **Hook:** "Getting off a slow train looks easy. Physics disagrees."
- **Device:** the "inertia ghost", a translucent amber copy of Max that keeps moving at train speed
  while his feet are stopped; momentum arrows attached in 3D.
- **"Hear it" moment:** the shoe's scuff and squeak as friction grabs the foot, then the thud.
- **Owner's requests:**
  1. a cinematic drone opener over the train with Max planning to step out;
  2. a cut to the motorman's cab speedometer with the needle dropping while Max decides;
  3. the fall shown for every scenario.
- **Telugu version:** not now.

## Decisions log

- 2026-10-31 Meshy shelved; beat outline approved, go to the next step (owner)

- 2026-10-31 Mumbai local; "why you fall" framing; hook 3; no Telugu version for now (owner)
- 2026-10-31 Runtime up to ~50 s, as long as every shot is tight (owner): all three falls stay
- 2026-10-31 Falls are shown up to impact (slow motion, freeze or cut on contact, no injury), to stay
  within YouTube policy and the channel's tone (Claude proposal, pending the owner's OK)

## Open issues

- Assets: a Mumbai EMU coach (exterior, door, interior), a platform with its edge and gap, a cab
  speedometer, a crowd. Sourcing and licences at G3.
