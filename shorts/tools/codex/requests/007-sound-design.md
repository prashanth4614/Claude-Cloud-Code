Full sound-design plan for the ear-pop pilot (47.4 s). Owner's verdict on v5: "voice clear but a noise bed
comes and goes with my voice; feels like cut-paste scenes with no flow; no sound for the muffled/blocked
feeling; other moments that need SFX are missing; add soothing, interesting background music at the right
level." Take your time; answer under 700 words. Argue where my plan is weak.

## Measured facts
- Voice (ElevenLabs clone, raw take): a constant noise floor inside every line (broadband hiss + hum
  94-164 Hz, flatness 0.73) ~27 dB under speech; between lines the gaps are digital silence. So noise
  switches on/off at each line = the "cut-paste" feel. Spectral noise reduction from a pause profile
  (noisereduce, stationary, prop_decrease 0.85) lowers it to ~36.5 dB under speech, timing unchanged.
- There is NO continuous bed now (no music, no ambience) -> hard silences at every cut.
- Foley: 30 clean ElevenLabs hits already synced to measured picture frames (whoosh into ear, eardrum
  pass, stretch on bulge, valve on 'cracks', air on 'escapes', whip, POP snap, thud on 'shut', inward
  stretch, swallow/yawn/4 chew bites on Max's face keys, plucks for labels/badges, chime on end card).
- Music options: ElevenLabs Music (generate to exact length with a described structure) or a CC-BY
  incompetech track.

## Shot table (time, set, move, transition, spoken beats)
S00    0.00- 0.63s cabin           handheld:0.3  out:cut              beats: wince@0.00
S01    0.63- 2.27s sky_golden_hour drone_reveal  out:match_cut:window beats: pop@1.73
S02    2.27- 3.43s cabin           push_through  out:push_through     beats: plane@2.37
S03    3.43- 7.57s ear_inside      flythrough    out:cut              beats: eardrum@3.53, middle@6.50
S04    7.57- 9.53s ear_inside      flythrough    out:cut              beats: ground@8.07
S04m   9.53-11.57s ear_map         dolly_in      out:cut              beats: matches@9.63
S05a  11.57-13.43s sky_high        pan_follow    out:cut              beats: 
S05b  13.43-14.83s ear_inside      dolly_out     out:cut              beats: drops@14.17
S06a  14.83-17.13s ear_inside      dolly_in      out:cut              beats: pushes@16.00
S06b  17.13-19.80s ear_map         dolly_in      out:cut              beats: bulges@18.03, balloon@19.20
S07   19.80-22.27s cabin           handheld:0.2  out:cut              beats: muffled@20.50
S08a  22.27-24.67s ear_inside      crane_down    out:cut              beats: tube@23.10
S08b  24.67-27.23s ear_inside      dolly_in      out:cut              beats: cracks@26.17
S09a  27.23-29.87s ear_inside      flythrough    out:whip:up          beats: escapes@27.53, evens@28.87
S09b  29.87-31.23s ear_inside      dolly_in      out:cut              beats: pop@30.67
S09c  31.23-32.13s cabin           dolly_in      out:cut              beats: relief@31.23
S10   32.13-34.07s city_dusk       drone_track   out:cut              beats: 
S11a  34.07-37.30s ear_inside      arc:20        out:cut              beats: rises@34.77, shut@36.60
S11b  37.30-40.07s ear_map         dolly_in      out:cut              beats: inward@39.27
S12a  40.07-43.93s cabin           dolly_in      out:cut              beats: swallowing@40.83, yawning@41.73, chewing@42.67
S12b  43.93-45.47s ear_map         dolly_in      out:cut              beats: pull@44.27, open@44.87
S13   45.47-47.33s cabin           dolly_in      out:cut              beats: thumbs@45.67

## My plan (argue with it)
1. Voice: noise reduction (0.85), then the clean static chain (HPF 75, -1.5 dB @300, +2.5 dB @3 kHz,
   2:1 slow compressor), fixed gain. 20 ms fades at each line edge.
2. Continuous beds per world, crossfaded 300-500 ms across cuts, with J/L-cuts (the next world's bed
   leads the picture cut by ~6-10 frames): cabin (soft engine hum + air), inside-ear (soft low "inner
   space" swells, no heartbeat), sky (smooth soft wind), city (distant soft evening hum). Generated as
   seamless ElevenLabs loops. Beds 28-32 dB under speech; the beds also mask the voice's residual noise.
3. Music: ElevenLabs Music, ~47.4 s, soothing + curious (felt piano, soft pizzicato, warm pad, light
   marimba, ~90 bpm), structure: calm wonder 0-11 s, gentle tension 11-27 s (climb, bulge, muffled),
   suspense hold 27-30.6 s, soft release right after the POP at 30.7 s, warm calm 31-45 s, resolve
   45-47.4 s. Music 20 dB under speech, ducked 3 dB per spoken line (150 ms ramps), 9 dB dip 250 ms
   before the POP.
4. Muffle (S07 'muffled', and the cold-open wince S00): the WHOLE bed + music low-passed to ~400 Hz,
   a soft "blocked-ear pressure" drone and a faint, short high ear-ring (tinnitus, ~3 kHz, -30 dB),
   unmuffle with a small airy release when S07 ends. Voice stays clear.
5. Extra SFX: transitions between worlds (cabin->ear, ear->sky, ear->city, map<->inside) with soft
   swishes; molecule "sparkle/bubble" when the air beads appear/thin (S04, S05b) and when blue air
   rises (S12b); a jet-engine swell under the climb (S05a) and a gentle descending plane under S10;
   a relieved exhale on S09c; a soft riser into the POP (S09a end).
6. Mix: two-pass loudness on the full mix, voice -14 LUFS short-term, peaks -1.5 dBTP.

## Questions
(1) What will make it FLOW (not cut-paste) — your concrete rules for J/L-cuts, bed crossfade lengths,
    transition SFX placement relative to the cut, music continuity.
(2) A per-shot cue sheet: for each shot ID, bed + SFX (with timing relative to beats) + relative level.
(3) Muffle design details that read clearly on a phone speaker.
(4) Music: ElevenLabs prompt text you'd use (structure + instrumentation), and its level/ducking numbers.
(5) Noise reduction settings/risks (musical noise) and whether line-edge fades are enough.
(6) Your ranked top 5 to get this "Zack D Films"-pro.
