Sound-mix review for the ear-pop pilot (owner's verdict on v2: "SFX not syncing, random noise all through,
swallow/yawn/chew sounds don't work, voice not punchy enough"). Answer under 500 words. Argue where my plan is weak.

## Facts (measured)
- Mix built by `shorts/pilot_ear_pop/mix.py` from `plan.json` (frames of shots and spoken words, 30 fps).
- Cue files (ElevenLabs SFX, `audio/sfx/*.mp3`) were placed by FILE START, but their hits come late:
  stretch peaks 1.09 s in, jet_climb 0.82 s, gear_down 0.99 s, card_soft 0.44 s. ear_pop and stretch were
  generated at -37/-34 dBFS peak; normalising them raised their hiss ~35 dB.
- Procedural cues from `shorts/engine.py` `sfx()` are noise-based: whoosh spectral flatness 0.70, pop 0.51.
- Beds: a "wind" bed that is band-passed white noise (sky/city), a body bed with heartbeat, a cabin hum; ducked 6 dB.
- Swallow/yawn/chew: only a synthetic "gulp" blip, placed on the spoken word, not on Max's face animation
  (`real_max.py`: swallow peaks at word+4 frames, yawn opens to word+10, chew cycles every 8 frames).
- Voice: ElevenLabs v3 take, polish chain `highpass 80, deesser, acompressor 2.2:1, loudnorm -16`.
- No music bed. Zack D Films (fan wiki) always runs background music under the narration.

## My plan (argue with it)
1. Drop: wind bed, procedural whoosh/pop, the boosted near-silent cues. Keep at most a very low cabin tone in
   cabin shots; no continuous noise under the ear journey.
2. Regenerate ~12 short, clean SFX with ElevenLabs Sound Effects (prompts asking "clean, no background noise,
   single hit"): whoosh-in, whoosh-through, whip, deep satisfying ear pop, rubbery membrane stretch, wet tube
   click, air hiss, soft thud, swallow gulp, short yawn, gum chewing (4 chews), soft UI pop for labels.
3. Sync by the cue's detected PEAK (transient) to the visual action frame: membrane/tube/pop to the shape-key
   keyframes; swallow/yawn/chew to Max's face keys, not the words; whooshes so their peak lands on the cut.
4. Music: a light, curious ~90-100 bpm bed (ElevenLabs Music or a YouTube Audio Library track), at about
   -20 dB under the voice, ducked 3-4 dB while he speaks, a lift into the POP, a soft resolve on the end card.
5. Voice punch: HPF 90 Hz, -3 dB at 300 Hz, +4 dB presence at 3-4 kHz, +2 dB air shelf at 10 kHz, compressor
   4:1 fast (5 ms / 80 ms), gentle saturation, de-esser, limiter; voice -14 LUFS short-term, everything else
   at least 8 dB under it.
6. Check sync with a spectrogram strip of the final mix marked with every visual beat, before the owner listens.

## Questions
(1) What makes Shorts-style (Zack D Films-like) sound feel "pro"? Density of SFX, music level, ducking,
    silence before the payoff, stereo, transients: be specific with numbers where you can.
(2) Agree/disagree with each step; anything I'm missing (e.g. sub-bass hit on the POP, reverse-whoosh lead-ins,
    risers, stereo panning for camera moves, room tone)?
(3) Concrete ffmpeg filter chain for the "punchy" narration that survives YouTube's loudness normalisation.
(4) Prompts for the ElevenLabs SFX that avoid hiss/background noise; ideal durations.
(5) Ranked top 5 fixes.
