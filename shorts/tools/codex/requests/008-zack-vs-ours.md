IMAGES: shorts/reference/ours/pilot_v11_sheet_1.jpg shorts/reference/ours/pilot_v11_sheet_2.jpg out/reference/compare/zack_1_sheet.jpg out/reference/compare/zack_2_sheet.jpg out/reference/compare/zack_3_sheet.jpg

# In-depth comparison: our ear-pop pilot vs Zack D Films Shorts

The owner wants an in-depth, honest comparison of our finished pilot with Zack D Films Shorts, and a plan
to match or beat them. Be critical and specific; argue with my reading where you disagree. 1200 words max.

## The images
- `pilot_v11_sheet_1/2.jpg`: our rendered pilot (47.4 s), one frame per second, timestamps top-left.
  The captions in our frames are part of the video.
- `zack_1/2/3_sheet.jpg`: three Zack D Films Shorts, one frame per second (local only, not in git).
  Their titles, timings, transcripts and voice measurements are in `out/reference/compare/zack_metrics.md`.
  Read it.
- Earlier measurements of both: `shorts/reference/zack_style_study.md`. Our shot list:
  `shorts/pilot_ear_pop/shots.yaml`. Our script: `shorts/pilot_ear_pop/script.yaml`.

## Our measured facts (v11)
- **Length:** 47.4 s, 22 shots (mean 2.15 s, longest 4.1 s).
- **Voice:**
  - 112 words; speaking 41.6 s, 88% of the runtime.
  - 162 words per minute while speaking (line range 136-202).
  - The owner's ElevenLabs v3 clone.
  - Pitch span p5-p95 7.7 semitones overall. Lines 9-11 flatten to 4.2-5.2 st; the hook line is 6.9.
  - Every gap between lines is 0.28 s; one pause is 1.38 s (after POP).
- **Sound:**
  - ElevenLabs score about 20 LU under the voice, no ducking.
  - Per-world room tone; 31 Foley hits; designed whooshes on world changes.
  - Pressure drone plus muffle from "muffled" to the POP.
- **Worlds:** a realistic cabin with Max (MakeHuman-based CG); pink inside-the-ear tunnels with air
  "molecule" spheres; a flat navy diagram with labels (canal / eardrum / middle ear / tube); the sky
  with an airliner; a low-detail night city.
- **Ending:** Max's thumbs-up plus a "Follow for more weird body facts" card (1.9 s).

## My (Claude's) reading, to argue with
1. **Opening:**
   - Max's wince plays 0-0.6 s, then the jet, then by 3 s a calm Max looking up.
   - The problem is stated but not felt; the visual hook fades in 3 s.
2. **Inside the ear:**
   - About 13 s of similar pink tunnels (4-9 s, 14-17 s, 23-31 s) with no anatomical context, so a
     viewer can't tell where they are.
   - The blue diagram (10-11 s, 18-19 s, 38-40 s, 44-45 s) is the clearest storytelling but feels like
     a different film.
3. **Three visual languages** (realistic cabin, abstract tunnel, flat diagram) and no consistent
   cutaway that connects the outside face to the inside anatomy.
4. **The night city (33-34 s)** reads low-poly next to the rest.
5. **The voice** is clear but even: a narrow pitch span at the end and machine-regular 0.28 s gaps.
6. **The ending** stops on a "follow" card rather than on the payoff or a loop back to the start.

## Questions
For each area give: what Zack does (cite timestamps in their sheets), what we do (cite our timestamps),
the gap, and a concrete fix in our pipeline (Blender build_previz.py / real_max.py, mix.py, script.yaml,
ElevenLabs settings). Mark each fix "no re-render" or "needs a re-render".

1. **Storytelling:** structure (hook, setup, escalation, payoff, button), stakes, and how quickly the
   question is answered; the sentence-level writing.
2. **Opening shot:** the first 1.5 s, frame by frame.
3. **Transitions:** cut types and their frequency, and how they move from outside to inside the body.
4. **Camera movement:** speed, type and consistency.
5. **Voice modulation:** pace, pitch, emphasis, pauses. Compare with `zack_metrics.md`.
6. **SFX and music.**
7. **Ending shot.**
8. **Colour grading and look:** palette, contrast, saturation, lighting, depth of field, material realism.
9. **How things are explained:** visual metaphors, anatomy views, on-screen graphics, cross-sections.
10. **The 8 changes** that would most close the gap, ranked by impact per cost, and where we could
    plausibly **beat** Zack rather than copy.
11. **Disagreements:** where my reading above is wrong.
