# Codex answer: 009-zack-plan

_model: gpt-6.1-sol, reasoning effort: high, read-only, cap 600s_

**Verdict: re-voice v2 completely; leave routine SFX levels; use felt pain without rupture language; switch captions to white. Build one coherent 34-second film.**

1. **Voice: substantial delivery gap; modest speed gap.** I revise 008. Cleaned pitch evidence, flat mechanism/remedy lines, excess silence and “ears poke” together justify intervention. The rewritten script warrants one continuous take rather than stitched repairs.

   Audition v3 stability **0.0 versus 0.5** on ten seconds; generate the complete script with the winner. Keep similarity 0.85 initially. Use sparse `[curious]`/`[warm]` tags and CAPS on **POP, DROPS, OUTWARD, INWARD**; skip theatrical whispering. Tags and capitalization are supported delivery controls. [ElevenLabs guidance](https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices#prompting-eleven-v3).

   Proposed acceptance gates: cleaned syllable-median p5–p95 span **8–10 st**; mechanism/remedy phrase spans **≥6 st**; selected stress jumps **+4–7 st**; speaking pace **165–185 wpm**; voice coverage **≥90%**. Actual interphrase gaps **0.10–0.25 s**, except one **≤0.4 s** payoff beat. Unprompted ASR must hear “ears pop”; human phone listening must confirm it. Metrics never excuse an unnatural take. Remove padding accumulation at `audio.py:83`/`engine.py:329`.

2. **SFX: leave routine levels; add no blanket whooshes.** The supplied audit contradicts “buried under beds.” It doesn’t prove perceptual clarity: spectral masking still matters. I’m applying the repo’s **sfx-design** skill: whooshes only when travelling between worlds.

   Settle this with loudness-matched, picture-synced phone A/Bs: current mix versus **+3 dB on one suspected masked cue**, music muted first, then restored. Change only cues whose action becomes clearer without obscuring words. Onset count is no acceptance target.

3. **Stakes: yes, within six seconds.** Use **“That tight, blocked feeling can really hurt.”** It states a recognizable consequence without implying routine imminent rupture. Pressure imbalance can cause pain; swallowing/yawning helps equalization. [MedlinePlus](https://medlineplus.gov/ency/article/001064.htm).

4. **Captions: yes—white, at most one yellow keyword.** `build_previz.py:616` colors the entire strip. Ship white first; individual keyword coloring needs separate positioned text elements.

**Ordered plan, (a): v11b today, no film re-render.**

1. Remove follow text/tail; retain thumbs-up under the final spoken payoff.
2. Tighten actual pauses, especially the 1.1-second extra POP hold. Recut cached shots and resync captions/SFX.
3. Replace the city with existing anatomy coverage; remove the black interval using earlier usable entry frames.
4. Recompose white captions over clean cached film frames; rebuild mix, audit, phone-check and encode. Don’t invoke FILM scene-strip rendering.

Budget **2–4 hours**, ₹0 incremental. Keep this an editorial improvement; don’t force existing narration into 34 seconds.

**Then (b): v2, one coordinated re-render batch.**

5. Lock this approximately **91-word** script and voice before animation:

| Seconds | Narration | Picture |
|---|---|---|
| 0–3 | “Why do your ears POP on a plane?” | Max discomfort, hand/ear/face visible; brief climbing-jet insert. |
| 3–6 | “That tight, blocked feeling can really hurt.” | Return to Max; 12–15-frame skin-peel entry. |
| 6–13 | “As the plane climbs, cabin pressure drops. Air trapped in your middle ear now pushes your eardrum outward.” | Persistent cutaway; slight bulge and resting outline. |
| 13–22 | “Then the Eustachian tube, connecting your middle ear to your throat, opens. Air escapes, the pressure on both sides balances, and—POP!” | Uninterrupted mechanism shot; airflow, relaxation, audible release. |
| 22–27 | “Coming down, cabin pressure rises. If the tube stays closed, your eardrum bends inward.” | Same orientation; reverse pressure and deformation. |
| 27–32 | “Swallowing or yawning helps open that tube, letting air back in to balance the pressure.” | Max swallows; same cutaway admits air. |
| 32–34 | “Pressure balanced. Hearing clear.” | Relief and thumbs-up; match opening framing, continuous cabin bed. |

6. Use cream bone, coral tissue, teal background; blue cabin air/amber middle-ear air. Outside stays screen-left. Sparse particles, readable anatomy, minimal DOF; slow 5–10% pushes. Nine shots total.

7. Preserve muffle→POP clarity, steady beds and restrained accents. Review Mac animatic, then batch-render approved shots.

Estimate **4–6 engineer days**, existing licensed assets, TTS credits; **34–102 GPU-min** at the pipeline’s 2–6 s/frame assumption. ₹15–90 remains an unbenchmarked render allowance.

**Beat Zack on:** anatomical continuity; felt muffle→clear sound; useful, accurately demonstrated relief.

Unresolved questions: none.
_took 107 s_
STATUS: OK
