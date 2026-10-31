IMAGES: shorts/reference/ours/pilot_v11_sheet_1.jpg shorts/reference/ours/pilot_v11_sheet_2.jpg

# Settle the open points from 008, then one plan for pilot v2

Read `shorts/tools/codex/answers/008-zack-vs-ours.md` (yours) and `shorts/reference/zack_vs_ours.md`
(the Mac session's frame-by-frame comparison; section 11 compares it with yours). Claude (coordinating
session) agrees with both on: drop the follow tail; one persistent anatomical cutaway; hold Max's
discomfort with hand, ear and face in frame; a skin-peel entry instead of the black dip; one longer
continuous mechanism shot; cut the night city; keep the thumbs-up and the muffle → POP release.
700 words max.

## Rule on these disagreements (pick a side, give a reason, give a number where useful)

1. **Voice gap: modest or large?**
   - You: modest (pace 166-187 wpm vs our 162; Zack's ~18 st pitch span may be octave errors).
   - Mac session: even after cleaning octave errors, Zack is 8-9 st per syllable vs our 6.4. Stressed
     words: +4 to +12 st vs ours +2 to +4. Our voice fills 81% of the runtime vs 95-96%. Whisper hears
     our hook as "why your ears poke".
   - Claude's own measurement: 7.7 st overall; lines 9-11 at 4.2-5.2 st.
   - Decide: re-voice the whole script (v3, lower stability, tags, CAPS stress, run-on gaps), or only
     re-perform the flat lines? Give pass/fail criteria for the new take (span, stress jumps, gaps, ASR
     check).
2. **SFX: buried or fine?**
   - The Mac's detector finds 9 onsets in our mix (Zack 6-10 per 10 s).
   - Claude's audit (`.claude/skills/sfx-design/scripts/audit_mix.py`) puts every v11 cue -8 to -16 dB
     under the speech level and +6 to +25 dB over the bed; the owner has already asked twice for fewer,
     cleaner whooshes.
   - Decide: raise the routine cues, add whooshes on more cuts, or leave them? What check settles it?
3. **Stakes line.** The Mac session wants one danger line ("feels like it could burst"); you warned
   against copying Zack's rupture threat. Is one felt-stakes line in the first 6 s right for us, and
   how should it be worded accurately?
4. **Captions.**
   - The Mac session: Zack uses plain white captions and no fully coloured chunks. Ours colour the
     whole "hot" chunk gold (build_previz.py: the whole TEXT strip is (1, 0.86, 0.1) when hot).
   - Change to white with at most one yellow keyword?

## Then: the v2 plan
- One ordered build plan for pilot v2 (target 30-35 s): script beats with target seconds, shot list
  (fewer, longer shots), voice spec, look spec (cutaway style and palette), sound changes and the
  ending.
- Group the steps into: (a) no re-render, can ship as v11b today; (b) needs a re-render, as one batch.
- Name the 3 things where v2 should **beat** Zack rather than copy him.
