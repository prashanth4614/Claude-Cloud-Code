# G4 full take: stability 0.5

The owner's clone `x5ld1ovD8agu3EPB7Qpj`, `eleven_v3`, stability 0.5, similarity 0.85, made with
`python3 shorts/train_step_off/voice.py full 0.5`. One take of the locked script, no retries.

- **Characters used:** 668 (limit 700).
- **Duration:** 48.35 s raw from ElevenLabs. That's `full_stab0.5.mp3`, the review copy, with its pauses
  as delivered. It's **41.74 s** after `compress_pauses` (max 0.4 s), in `out/.../take.wav`, the audio the
  edit uses and that `voice_check` measured. `timings_stab0.5.json` matches the 41.74 s version.

## Per-line durations (compressed take)

| Line | Duration | Caption |
|---|---|---|
| 1 | 3.64 s | Getting off a slow train looks easy. Physics disagrees. |
| 2 | 6.18 s | At ten kilometres an hour it looks like a crawl, but that's more than twice a comfortable walking pace. |
| 3 | 6.38 s | That's because when your shoe grips, your foot slows sharply, while your upper body keeps moving. |
| 4 | 4.38 s | So facing backward, you can tip backward, the way you can't see. |
| 5 | 5.30 s | Facing sideways, you're still moving along the platform, which can throw you off balance. |
| 6 | 6.40 s | Facing forward, a few quick steps can spread out the slowdown, but you can still lose your balance. |
| 7 | 5.46 s | One wet patch, one bag, one crowded step, and the gap is right there. |
| 8 | 4.00 s | So wait until the train has completely stopped, even if |
| | **41.74 s** | |

## voice_check

`python3 .claude/skills/shorts-craft/scripts/voice_check.py out/train_step_off/voice/full_stab0.5/take.wav --hook "Getting off a slow train looks easy" --runtime 42`

```
transcript: Getting off a slow train looks easy. Physics disagrees. At 10 km an hour, it looks like a crawl, but that's more than twice a comfortable walking pace. That's because when your shoe grips, your foot slows sharply while your upper body keeps moving. So facing backward, you can tip backward the way you can't see. Facing sideways, you're still moving along the platform which can throw you off balance. Facing forward, a few quick steps can spread out the slow down, but you can still lose your balance. One wet patch, one bag, one crowded step and the gap is right there. So wait until the train has completely stopped even if

[WARN] pace 185 wpm while speaking (target (165, 185))
[WARN] voice covers 87% of 42.0 s (>= 90%)
[WARN] gaps 0.48, 0.24, 0.20, 0.30, 0.22, 0.36, 0.30, 0.36, 0.24, 0.28, 0.26, 0.32, 0.20, 0.28, 0.26, 0.44, 0.28 s (<= 0.25 s, one payoff beat allowed)
[WARN] pitch span 6.0 st over word medians (>= 8.0)

phrase                                         span   stress jump
[WARN] Getting off a slow train looks easy.           4.1 st  Getting +3.7 st
[WARN] At 10 km an hour,                              5.2 st  10 +3.5 st
[WARN] it looks like a crawl,                         2.6 st  looks +0.8 st
[WARN] but that's more than twice a comfortable wal   1.9 st  more +1.5 st
[WARN] That's because when your shoe grips,           4.9 st  grips, +1.4 st
[WARN] your foot slows sharply while your upper bod   2.5 st  upper +0.9 st
[WARN] So facing backward,                            2.7 st  backward, +1.0 st
[WARN] you can tip backward the way you can't see.    3.9 st  tip +5.0 st
[WARN] Facing sideways,                               0.2 st  Facing +0.1 st
[WARN] you're still moving along the platform which   5.3 st  still +5.7 st
[WARN] Facing forward,                                0.0 st  forward, -0.0 st
[WARN] a few quick steps can spread out the slow do   6.0 st  quick +6.5 st
[WARN] but you can still lose your balance.           3.8 st  still +3.0 st
[WARN] One wet patch,                                 1.3 st  One +0.0 st
[WARN] one bag,                                       0.5 st  bag, -0.3 st
[WARN] one crowded step and the gap is right there.   2.5 st  gap +1.3 st
[WARN] So wait until the train has completely stopp   3.6 st  wait +2.2 st

[PASS] ASR hears the hook "getting off a slow train looks easy" unprompted
```

## Words Whisper misheard or heard with confidence under 0.5

Whisper `small.en`, compared with the caption text. Times are given for the compressed take (wav) and
the raw take (review mp3).

| Script | Whisper heard | Confidence | wav time | mp3 time | Notes |
|---|---|---|---|---|---|
| "ten kilometres" | "10 km" | 0.51 (wav), 0.43 (mp3) | 3.88 s | 5.28 s | "10" for "ten" is just number formatting. "km" means the word may be clipped ("k'm"), the same doubt as in the audition. Listen here first. |
| "an" (hour) | "an" | 0.07 (wav), 0.05 (mp3) | 4.52 s | 5.88 s | Barely voiced, probably swallowed into "kilometres an hour". |
| "slowdown" | "slow down" | 0.67, 0.89 | 29.42 s | 34.00 s | Just how Whisper split the word; heard correctly. |

All other words match the script. The captions in `timings_stab0.5.json` come from the caption text, so
they're right whatever Whisper heard.

These notes come from measurements and a Whisper transcript, not from listening.

## Locked take (MAX_PAUSE 0.25): ON HOLD, the cut clips "Physics"

`MAX_PAUSE=0.25 python3 shorts/train_step_off/voice.py full 0.5` came entirely from the cache. The run
was made with the network blocked, so no ElevenLabs credits were used, and the cache still holds one
file. The result is **40.04 s**, with these per-line durations:
3.49, 6.03, 6.08, 4.27, 5.15, 6.13, 5.04, 3.85 s.

**Not committed as `locked_take.mp3`:** the tighter cut removes the start of "Physics". Whisper hears
"Getting off a slow train looks easy. **Six** disagrees."

- **Cause:** the word alignment puts "Physics" at 3.38 s in the raw take. In the audio, the "Ph" sound
  starts at about 3.10 s and the vowel at about 3.19 s; "easy." ends at about 2.69 s.
- `compress_pauses` therefore treats 2.69-3.38 s as a gap. At 0.25 it removes the middle 0.44 s
  (2.82-3.26 s), which takes out "Ph" and the start of the vowel.
- At 0.4 (the 41.74 s take above), the cut was 2.89-3.18 s. That clips only the edge of the "Ph", and
  Whisper still hears "Physics" (0.97).
- The caption timing for "Physics" in both timings files (2.56-2.61 s here) also comes from that
  misplaced start, so the word's caption would appear late.

**Local experiment (no repo code changed):** a cut that only removes frames under 0.01 RMS inside each
gap keeps "Physics" whole; Whisper also hears "kilometers". But the take then shortens only to 46.05 s,
because most gaps hold breath noise above that level. A fix needs a decision: either a silence-aware cut
with a tuned threshold in `engine.compress_pauses`, or a fixed start for "Physics", or keeping
MAX_PAUSE 0.4.

voice_check on the 40.04 s cut (`--runtime 41`), for the record:

```
transcript: Getting off a slow train looks easy. Six disagrees. At 10 km an hour, it looks like a crawl, but that's more than twice a comfortable walking pace. That's because when your shoe grips, your foot slows sharply while your upper body keeps moving. So facing backward, you can tip backward the way you can't see. Facing sideways, you're still moving along the platform which can throw you off balance. Facing forward, a few quick steps can spread out the slow down, but you can still lose your balance. One wet patch, one bag, one crowded step and the gap is right there. So wait until the train has completely stopped even if

[WARN] pace 191 wpm while speaking (target (165, 185))
[WARN] voice covers 87% of 41.0 s (>= 90%)
[WARN] gaps 0.36, 0.26, 0.16, 0.22, 0.22, 0.26, 0.32, 0.28, 0.26, 0.20, 0.28, 0.20, 0.20, 0.38, 0.20, 0.32, 0.30 s (<= 0.25 s, one payoff beat allowed)
[WARN] pitch span 6.1 st over word medians (>= 8.0)

phrase                                         span   stress jump
[WARN] Getting off a slow train looks easy.           4.1 st  Getting +3.7 st
[WARN] At 10 km an hour,                              5.3 st  10 +3.6 st
[WARN] it looks like a crawl,                         2.8 st  looks +0.6 st
[WARN] but that's more than twice a comfortable wal   2.0 st  more +1.7 st
[WARN] That's because when your shoe grips,           5.7 st  grips, +1.1 st
[WARN] your foot slows sharply while your upper bod   3.0 st  upper +1.8 st
[WARN] So facing backward,                            3.0 st  backward, +1.0 st
[WARN] you can tip backward the way you can't see.    1.5 st  tip -0.1 st
[WARN] Facing sideways,                               0.0 st  sideways, +0.0 st
[WARN] you're still moving along the platform which   5.3 st  still +5.7 st
[WARN] Facing forward,                                0.4 st  forward, +0.2 st
[PASS] a few quick steps can spread out the slow do   6.2 st  quick +6.4 st
[WARN] but you can still lose your balance.           3.9 st  still +3.4 st
[WARN] One wet patch,                                 1.8 st  One +0.4 st
[WARN] one bag,                                       0.4 st  bag, -0.2 st
[WARN] one crowded step and the gap is right there.   2.6 st  gap +1.6 st
[WARN] So wait until the train has completely stopp   3.5 st  wait +2.5 st

[PASS] ASR hears the hook "getting off a slow train looks easy" unprompted
```
