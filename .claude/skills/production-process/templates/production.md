# <Video title>: production tracker

Process: `.claude/skills/production-process/SKILL.md`. A gate is done when its checks pass **and** the
owner approves (record the date). Changing a locked item reopens its gate.

| Gate | Status | Approved (date) | Notes / links |
|---|---|---|---|
| G0 Idea and angle | ☐ | | question, angle, device, "hear it" moment |
| G1 Story and facts (Codex) | ☐ | | `facts.md`, Codex request id |
| G2 Script locked (Codex) | ☐ | | word count, timing at 170 wpm |
| G3 Screenplay, shot list, transition chain, boards (Codex) | ☐ | | `shots.yaml`, boards sheet |
| G4 Voice locked | ☐ | | take id, `voice_check.py` result |
| G5 Pre-frame QA (Codex) | ☐ | | QA report, waivers |
| G6 Key-frame test (Claude + Codex) | ☐ | | sheets, must-fix list |
| G7 Animatic + review .blend: picture lock | ☐ | | `out/<video>/<video>_review.blend` |
| G8 Sound (Codex) | ☐ | | `audit_mix.py` result, licences |
| G9 Final render | ☐ | | bench cost/time, frame QA |
| G10 Publish + 48 h/7 d review | ☐ | | retention notes, lessons added to skills |

## Decisions log

- <date> <decision> (<who>)

## Open issues

- …
