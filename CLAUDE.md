# Project rules for Claude sessions

YouTube Shorts production pipeline. **The agreed production pipeline is `PIPELINE.md`
(Blender 3D + RunPod + ElevenLabs voice + Claude code-based edit). Follow it.** See also `README.md`, `shorts/README.md`,
`shorts/ai/README.md` and `cloud/README.md`.

## Images and AI video: the user generates them, Claude writes the prompts

- **Do not call any image- or video-generation API** (Gemini/Imagen, Veo, OpenAI images,
  ElevenLabs Image & Video, etc.), and don't automate the ChatGPT or Gemini apps.
  Paused by the user on 2026-10-29 until they say otherwise. `shorts/ai/gemini_gen.py` stays
  in the repo but must not be run.
- Whenever a video needs images or AI clips, **give the user ready-to-paste prompts in chat**:
  1. a character sheet first, for any recurring character;
  2. one image prompt per shot, numbered to match the narration lines;
  3. a short Veo motion prompt for the shots worth animating.
  Also keep them in `shorts/ai/<video>/prompts.json`, which `shorts/ai/shot_helper.py` reads.
- Prompt rules:
  - 9:16 vertical, subject centred.
  - No text, labels, logos or watermarks (the pipeline adds all text).
  - One fixed style suffix per video, and "Using the attached character sheet, keep <name>
    exactly the same:" on every shot with that character.
  - Original characters only.
- The user saves results as `shorts/ai/<video>/shots/NN.png` (or `NN.mp4`), and the
  character sheet as `shorts/ai/<video>/<name>_sheet.png`. Then assemble with
  `shorts/ear_pop_ai.py`, or that video's equivalent assembler.

## Codex helper (code review only)

- The user allowed (2026-10-30) a Codex second opinion through the **Codex CLI on their Mac**
  (`shorts/tools/ask_codex.sh`, read-only sandbox), for code review and help with stubborn bugs.
  Requests go in `shorts/tools/codex/requests/<id>.md`; answers come back in `.../answers/<id>.md`.
- **Codex reviews; it never writes code** (owner, 2026-10-31). Claude writes every change, then asks
  Codex to review it (the diff, the renders, the plan) and to find bugs and weak spots. Requests must
  not ask for patches, functions or ready-to-apply code; findings come back as file:line and what's wrong.
- This is not image or video generation; that pause above still stands. Verify any Codex
  finding before acting on it; Claude stays the only one editing the repo.

## Voice

- Narration uses the user's ElevenLabs cloned voice: `--voice elevenlabs:x5ld1ovD8agu3EPB7Qpj`.
  ElevenLabs is used for text-to-speech only (the plan has no Image & Video access).
- Cloud sessions get the ElevenLabs key as a network secret attached by the proxy, so
  `$ELEVENLABS_API_KEY` may be empty even though requests work. Never print, log or commit any key.

## Helper sessions (reuse these; don't create new ones)

The owner's Mac has three standing helper sessions (Remote Control bridge), and two cloud workers take
long jobs off the coordinating session, so the owner can keep talking to it while they run. Send each task to the one
that fits it with `send_message`, and create a new helper only for a genuinely new kind of task, with the
owner's OK.

| Helper | Session id | Use for |
|---|---|---|
| Render worker | `session_01Bok4noiXNe3cEe1E2MxQpM` | Blender on the Mac: animatics, review renders, thumbnails, Mac-side previews |
| Codex helper | `session_01Bok4nppX4eaPC9ozBb3Gms` | every `shorts/tools/ask_codex.sh <id>` run (code and creative review) |
| Web / YouTube | `session_01Bok4noPAoM8Fa4xBMKHT9P` | Chrome on the Mac: YouTube references (`yt_reference.py`), web research, measurements of reference videos |
| Cloud worker: voice & audio | `session_01Bok4nmfJr7VJ7ka18W8PBn` | long ElevenLabs jobs in the cloud: voice takes and auditions, `voice_check.py`, SFX and music generation, mix builds (`mix.py`, `telugu.py`) |
| Cloud worker: RunPod renders | `session_01Bok4npHajGYFXx5epHgMSF` | RunPod GPU renders (`final_render.sh`: dry run, bench, full, assemble), watching the pods and deleting them |

**Monitoring:**
- **The coordinating session can't be woken automatically.** It is bound to the owner's trusted
  device, so scheduled check-ins (`send_later`) and messages from helpers into it are refused
  (ACCESS_DENIED, verified 2026-10-31). Don't schedule check-ins into it. Instead, **at the start of
  every reply**, check each helper that has an open task (`get_session`, the branch for its pushes)
  and report one line on each.
- **Self-monitoring that does work:** while a helper is busy, run
  `shorts/tools/watch_branch.sh '<path regex>' <minutes>` with the Bash tool's `run_in_background`. It
  polls the branch every minute and exits when the helper's push lands, which re-invokes this session to
  act on it (apply, review, send the next task) without the owner having to message. Re-arm it after
  each event while work is open.
- Helpers deliver by pushing to the branch, and by opening results in Preview on the Mac for the
  owner.
- When checking, read its state (`get_session`, `list_events` filtered to assistant/result, or its
  pushes on the branch). Then:
  - give the owner a one-line progress note;
  - report the outcome.
- A helper stuck or asking for something (a permission prompt, a missing tool) gets unblocked or
  escalated to the owner at once.
- Helpers can't always message back (a trusted-device limit), so read their transcript or the branch
  rather than waiting for a reply.
- The cloud workers' earlier blockers (2026-10-29: an ElevenLabs 401, a missing TTS cache) are stale:
  - the key now reaches ElevenLabs through the proxy;
  - the pilot's takes are cached through `shorts/pilot_ear_pop/takes/`.

  Brief each worker fully with every task (files, settings, spend limits). Credits are spent only after
  the owner's OK, and RunPod jobs always run a `--dry-run` first.

## Making a new video

- Follow the `production-process` skill (`.claude/skills/production-process/`): gates G0-G10 from the
  idea to upload, each with checks, a Codex review where marked, and the owner's approval recorded in
  `shorts/<video>/production.md`. Voice is locked before animation; picture is locked before sound; the
  final render only runs after the animatic and review `.blend` are approved.

- Use the `shorts-craft` skill (`.claude/skills/shorts-craft/`) for every new Short, on any topic:
  screenplay and presentation devices, the one-3D-world rule (no 2D diagram inserts), aligned
  transitions, camera, Max, voice gates (`scripts/voice_check.py`), captions, ending, thumbnail and the
  pre-render checklist.
- House look: **ink & amber** (the owner's choice): art-direct scenes in it and finish with
  `shorts/look/house_grade.py frames ink_amber`. Don't re-edit published videos to apply any of this.

## Sound

- For any sound-mix work (SFX, transitions, music, room tone, voice clean-up, loudness), use the
  `sfx-design` skill (`.claude/skills/sfx-design/`): its rules, targets and `scripts/audit_mix.py`.

## Rendering

- Heavy Blender renders go to RunPod via `cloud/render_runpod.py`, after a `--dry-run`.
  Pods must always be deleted.
- Don't start paid renders, or anything else that spends credits, unless the user asks for it.

## Git

- Work on `claude/youtube-video-production-4ic14n`. Run `git pull --no-rebase` before
  pushing, because the user's Mac session pushes to the same branch.
- Never commit `out/`, `voices/`, TTS caches or keys.
