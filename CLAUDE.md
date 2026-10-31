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
- This is not image or video generation; that pause above still stands. Verify any Codex
  suggestion before applying it; Claude stays the only one editing the repo.

## Voice

- Narration uses the user's ElevenLabs cloned voice: `--voice elevenlabs:x5ld1ovD8agu3EPB7Qpj`.
  ElevenLabs is used for text-to-speech only (the plan has no Image & Video access).
- Cloud sessions get the ElevenLabs key as a network secret attached by the proxy, so
  `$ELEVENLABS_API_KEY` may be empty even though requests work. Never print, log or commit any key.

## Helper sessions on the Mac (reuse these; don't create new ones)

The owner's Mac has three standing helper sessions (Remote Control bridge). Send each task to the one
that fits it with `send_message`, and create a new helper only for a genuinely new kind of task, with the
owner's OK.

| Helper | Session id | Use for |
|---|---|---|
| Render worker | `session_01Bok4noiXNe3cEe1E2MxQpM` | Blender on the Mac: animatics, review renders, thumbnails, Mac-side previews |
| Codex helper | `session_01Bok4nppX4eaPC9ozBb3Gms` | every `shorts/tools/ask_codex.sh <id>` run (code and creative review) |
| Web / YouTube | `session_01Bok4noPAoM8Fa4xBMKHT9P` | Chrome on the Mac: YouTube references (`yt_reference.py`), web research, measurements of reference videos |

**Monitoring:**
- Every time a helper gets a task, schedule a check-in (`send_later`, about 10-15 minutes, or matched
  to the job's length).
- On each check-in, read its state (`get_session`, `list_events` filtered to assistant/result, or its
  pushes on the branch). Then:
  - give the owner a one-line progress note;
  - re-arm until the task is done;
  - report the outcome.
- A helper stuck or asking for something (a permission prompt, a missing tool) gets unblocked or
  escalated to the owner at once.
- Helpers can't always message back (a trusted-device limit), so read their transcript or the branch
  rather than waiting for a reply.
- Cancel pending check-ins once the work is reported.

## Making a new video

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
