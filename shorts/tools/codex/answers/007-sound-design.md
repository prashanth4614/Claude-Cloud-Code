# Codex answer: 007-sound-design

_model: gpt-6.1-sol, reasoning effort: high, read-only, cap 600s_

**Verdict: good direction, over-scored.** Fewer sonic resets will improve flow. Keep existing picture anchors; offsets below describe them. Skip molecule bubbles and map swishes: they add clutter and suggest liquid.

Run beds continuously through same-world shots; ear_map shares ear_inside. World changes: incoming bed leads 200ms, outgoing trails 400–600ms; use 600–800ms equal-power crossfades. Keep cabin under S00–S02, with exterior wind overlaid. Swishes only for physical pushes/whips: start 100ms early, peak on fastest motion, decay 200ms afterward. Keep one uninterrupted score; remove the [ending fade](../Claude-Cloud-Code-codex/shorts/pilot_ear_pop/mix.py). Don’t raise beds to conceal hiss.

Starting levels: bed RMS below active-speech RMS: **C** cabin −30dB; **I** ear/map −32; **W** wind −32; **D** city −34. **P** pressure texture −24. SFX numbers below mean **peaks below dialogue peaks**. Unlisted accents: omit.

| Shot | Bed | SFX: timing; level |
|---|---|---|
| S00 | C+P | Occluded immediately; tiny seat creak −22 |
| S01 | C+W | Jet cut+450ms; −18 |
| S02 | C | Dive outgoing cut−120ms; −16 |
| S03 | I | Continue dive; pass cut+350ms; −24 |
| S04 | I | Eardrum pass ground−50ms; −22 |
| S04m | I | No label pluck |
| S05a | W | Climb cut+800ms; −18 |
| S05b | I | Air thins at drops; −24 |
| S06a | I+P | Stretch pushes+200ms; −20 |
| S06b | I+P | Stretch bulges−67ms; −16; sustain through balloon |
| S07 | C+P | Muffle begins muffled−150ms |
| S08a | I+P | Continue pressure; no tube accent |
| S08b | I+P | Valve cracks+100ms; −16 |
| S09a | I+P | Air escapes −18; whip outgoing cut−100ms, −22 |
| S09b | I | POP pop+33ms; −6; pressure releases |
| S09c | C | Exhale relief+100ms; −22 |
| S10 | D | Distant plane cut+900ms; −22; omit gear |
| S11a | I+P | Pressure rises; thud shut+267ms, −20 |
| S11b | I+P | Stretch inward+67ms; −18 |
| S12a | C+P | Swallow+133ms −20; yawn−67ms −24; bites chewing+367/633/900/1167ms −26 |
| S12b | I | Valve pull+33ms −20; air pull+133ms −24; settle open+67ms −18 |
| S13 | C | Optional chime cut+267ms −28; maintain loop bed |

Muffle ambience/music; keep narration and explanatory Foley clear. Ramp 120ms to **800Hz low-pass, 24dB/oct**, adding soft mono 350–650Hz pressure texture. This preserves phone-audible body; 400Hz risks near-disappearance. Skip tinnitus: competing symptom, piercing band. Hold reduced brightness/pressure until POP; restore over 150–250ms. S00 eases out at 0.63s without a release sound.

Music prompt:

> “47.4-second instrumental science miniature, 90bpm; sparse felt piano, warm pad, occasional soft pizzicato. Clean modern recording, restrained curiosity; no drums, vocals, hiss or stings. 0–11 wonder; 11–27 gentle tension; 27–30.7 suspended texture; 30.7 soft harmonic release; 31–45 warm clarity; 45–47.4 return to opening harmony/texture, seamless re-entry.”

Drop marimba. Set `music_length_ms=47400`, `force_instrumental=true` ([API](https://elevenlabs.io/docs/api-reference/music/compose)). Edit the release precisely afterward.

Music: −21dB RMS baseline; additional −3dB speech duck, anticipatory 150ms attack/600ms release. Bridge gaps <500ms. Dip music/ambience another 9dB from POP−250ms; recover over 350ms afterward.

NR: stationary; `prop_decrease=0.7–0.85`, threshold 1.5, frequency smoothing 500Hz, time smoothing 80ms ([parameters](https://github.com/timsainb/noisereduce)). Profile genuine noisy pauses, never digital silence. Denoise before compression; compare 0.7/0.85 loudness-matched for watery consonants. HPF75 won’t remove 94–164Hz; avoid broadly notching the voice fundamental. Make presence boost optional. Twenty-millisecond fades prevent clicks only; place within nonspeech handles, preserve timing.

Two-pass master **complete mix** to −14 LUFS integrated, ≤−1.5dBTP ([FFmpeg](https://ffmpeg.org/ffmpeg-filters.html#loudnorm)). Current `mix.py:184` limits sample peaks; verify true peaks after AAC.

Ranked: ① clean voice ② continuous beds/score ③ pressure→POP contrast ④ selective Foley ⑤ phone/mono/headphone and loop QA.

Estimate: **3–5 engineer-hours**, minutes CPU, no Blender rerender. ₹0 using CC0 beds and [credited Incompetech](https://incompetech.com/music/royalty-free/licenses/); approved ElevenLabs credits otherwise.

Unresolved questions: none.
_took 228 s_
STATUS: OK
