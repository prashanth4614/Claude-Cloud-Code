# Cozy Anime-Style Relax Videos — Reverse Engineering & Production Playbook

Reference video: **"Road trip with family in the Mobile Home 🚐🌧️ on a rainy day ⛈ Ghibli - Style Video"**
by [Zippy Relax Music](https://www.youtube.com/@ZippyRelaxMusic) — <https://youtu.be/FvmesyqYENM>

> **What this analysis is based on:** the video's title, the thumbnail, the three
> frames YouTube generates at 25% / 50% / 75% of the runtime, and public
> channel stats (videos, views, durations). YouTube blocked the actual
> video/audio stream from the analysis machine, so **the music section is
> inferred from the niche and channel description, not heard**. Watch the
> video once yourself with the checklist in §1.4 to confirm the details.

---

## 1. Reverse engineering

### 1.1 The channel's numbers

| Metric | Value |
|---|---|
| Subscribers | 25.8K |
| Total views | 4.62M |
| Videos | 39 (channel created 2021, but all of these uploads are from the last ~9 months, so it looks like a repurposed channel) |
| Video length | **almost all 31–32 minutes** |
| Best performers | 1M ("Harvesting Vegetables, Raising Poultry and Cooking…"), 535K ("Sleeping with Grandparents…"), 461K, 262K, 202K |
| Typical video | 15K–100K views |

**Takeaway:** views follow a power law. A handful of hits carry the channel,
and the hits share a theme: **nostalgia, grandparents and countryside, food and
cooking, harvesting**. The "mobile home road trip" sub-series does worse
(11K–44K). Food plus family plus childhood nostalgia beats novelty settings.

### 1.2 Format anatomy

| Element | What they do |
|---|---|
| **Visuals** | AI-generated still illustrations in a hand-painted 2D anime style (soft cel shading, watercolour skies, warm lamp light). Around 30–60 different scenes per video. |
| **Motion** | "Subtle motion visuals" (the channel description's own words): slow zoom/pan, and probably some AI image-to-video for small movements like steam, rain and flickering firelight. No real animation or lip-sync. |
| **Story** | A loose "day in the life" of an unnamed family (dad, mum, a boy and a girl, sometimes grandparents). The scenes are only vaguely connected: the 75% frame of the *rainy road trip* video is a snowy Lunar New Year market. **Continuity is weak, and that's an opening for you.** |
| **Characters** | A generic anime family. Character consistency varies between scenes because the art style drifts (compare the cartoonier market scene to the painterly campfire). |
| **Text on screen** | None visible in the sampled frames. |
| **Length** | About 31 minutes. That's over the 8-minute mid-roll threshold, and long enough for study and sleep sessions. |
| **Thumbnail** | The single most detailed, "wow" frame: a cutaway vehicle showing several cozy rooms at once (driver, kitchen, rooftop pool), with a night sky, warm interior light against a cool exterior, and lots of tiny details to make people click. |
| **Title formula** | `[Cozy activity] + [setting] + [weather/mood emoji] + "Ghibli-Style Video"` |
| **Keywords** | ghibli style video, cozy animation, chill music, study music, calm music, aesthetic video, wholesome video, family warmth, cooking asmr, heartwarming story |

### 1.3 Audio (inferred)

The channel describes itself as *"gentle sounds blend with subtle motion
visuals… help you sleep better, focus more easily"*. Titles mention *rain
sounds* and *ASMR cooking*. Assume the soundtrack is built like this:

1. **Music bed:** soft solo piano, or piano with strings, music box or acoustic
   guitar, at 60–80 BPM. This is the "Ghibli-inspired" sound: major-key
   nostalgic melodies, waltz-like 3/4 time, a few lofi tracks. Very likely
   AI-generated (Suno or Udio style) or royalty-free library music, around
   3–5 tracks of 6–10 minutes each.
2. **Ambience layer:** rain on a roof or window, distant thunder, crickets,
   a crackling fire, kept 10–20 dB under the music.
3. **Foley/ASMR:** cooking sizzle, knife chopping, pouring tea, timed to the
   scenes on screen.
4. **Mastering:** quiet and compressed, with no sudden peaks (so sleepers
   don't wake up) and fade-in/out at the ends.

### 1.4 Checklist to confirm it yourself (5 minutes)

- [ ] Are scenes still images with zoom/pan, or do characters actually move (Kling/Runway-style)?
- [ ] Average seconds per scene (time 5 scenes)?
- [ ] Transition type: crossfade, cut, or fade to black?
- [ ] Is the music piano, lofi, or vocal? How many distinct tracks?
- [ ] Do the sound effects follow the scenes (sizzle during cooking)?
- [ ] Description: tracklist or timestamps, music credits, AI disclosure?
- [ ] Pinned comment, end screen, playlist placement?

---

## 2. How to make one (step by step)

```
Concept & shot list ─► Image generation ─► (optional) image-to-video ─►
Music + ambience ─► Assemble (pipeline/make_video.py) ─► Thumbnail ─► Upload & SEO
```

### Step 1: Concept and shot list (30 min)
Pick **one** theme and give it a real arc. For example, *"Rainy road trip"*:
morning departure → driving in rain → cooking lunch in the van → kids at the
window → evening campfire → sleeping while it rains. That's 30–60 shots,
written as a table: scene, time of day, weather, action, sound effect. Prompt
templates are in [`pipeline/prompts.md`](pipeline/prompts.md).

### Step 2: Images (1–3 h)
- **Tools:** Midjourney, ChatGPT/GPT image, Flux, Leonardo, or Ideogram. Use a
  plan whose licence allows **commercial use**.
- Lock character consistency with a **character reference sheet** (the same
  family in every prompt, plus Midjourney `--cref`/`--sref` or a reference
  image), and keep one fixed style suffix.
- Generate at 16:9, at least 1920×1080 (upscale to 4K if you can; it makes
  the zoom/pan sharper).
- Make the thumbnail image separately: a busier composition with more
  detail and stronger contrast.

### Step 3: Motion (optional, but this is the main upgrade)
Animate the 10–20 best stills with image-to-video (Kling, Runway, Luma, Veo,
Hailuo, etc.) using prompts like *"gentle steam rising, rain on window,
subtle breathing, camera static"*. Keep clips 5–10 s; the pipeline
slows/extends them. Drop the `.mp4` clips into the same scenes folder as the
stills.

### Step 4: Music and sound
| Source | Commercial/monetization OK? |
|---|---|
| YouTube Audio Library | ✅ free |
| Suno / Udio **paid** plan | ✅ you get commercial rights on paid tiers (check current terms) |
| Epidemic Sound, Artlist, Musicbed (subscription) | ✅ whitelist your channel |
| Pixabay / free sites | ⚠️ often fine, but Content ID claims happen |
| Actual Studio Ghibli / Joe Hisaishi music, or covers of it | ❌ will be claimed or blocked |

Example music prompt: *"gentle solo piano with soft strings, nostalgic
Japanese countryside, warm, 70 bpm, instrumental, no vocals, slow waltz"*.
Aim for 3–5 tracks totalling around 30 minutes. For rain, use a licensed
ambience file or the pipeline's built-in `--rain-audio` (procedurally
generated, so it can't be claimed).

### Step 5: Assemble (automated)
```bash
python3 pipeline/make_video.py \
  --images scenes/ --music music/ \
  --rain-audio --rain-visual 0.015 \
  --seconds-per-image 20 --out out/rainy_roadtrip.mp4
```
This gives a 1080p H.264 + AAC MP4, Ken Burns motion that alternates zoom
in/out and pan left/right, crossfades, film grain and vignette, optional rain
streaks, music crossfades, a rain bed, two-pass loudness normalisation to
−14 LUFS (YouTube's playback level), and a `*.tracklist.txt` with
timestamps for the description. Run `--help` to see every option. Needs only
Python 3 and ffmpeg.

Want a 1–3 hour sleep version? Add `--minutes 120`. The music bed and the
visual loop repeat automatically.

### Step 6: Thumbnail
Use the formula from §1.2: one hero image, a cutaway or "window into a cozy
space", warm light inside and cool blue/night outside, a small family, lots of
detail. At most 2–4 big words, or no text at all (the reference uses none).
Check that it still reads at phone size.

### Step 7: Upload and SEO
- **Title:** `Cozy Rainy Road Trip with Family 🚐🌧️ | Relaxing Piano & Rain Sounds for Sleep & Study`
- **Description:** two lines of mood text, then the tracklist with timestamps,
  then music credits, then 3 hashtags (`#cozyanimation #relaxingmusic #rainsounds`).
- **Chapters:** the timestamps double as chapters. The first one must be `00:00`.
- **Playlists:** "Rainy Day", "Countryside Life", "Sleep" — make playlists that
  binge-watch well.
- **Schedule:** 2–3 uploads a week at a consistent time. Use YouTube's A/B
  "Test & Compare" with 3 thumbnails.

---

## 3. How to beat the reference (improvements)

1. **Real continuity:** a named recurring family (*"The Hoshino Family"*), with
   each video one coherent day. The reference jumps from a rainy van to a snowy
   market. Viewers come back for characters, not random scenes.
2. **More motion:** even 30% of scenes animated (steam, rain, blinking,
   flickering fire) feels more premium than pure zoom-and-pan.
3. **Sound synced to the picture:** sizzle when cooking, a door creak, pages
   turning. Cheap to add, and it makes the video feel crafted.
4. **Lean into the winners:** the data in §1.1 says grandparents, childhood
   nostalgia, harvesting and cooking. Make the van theme a side series.
5. **Length ladder:** a 30 min main video, a 1–3 h "sleep" re-edit of the same
   assets (low effort, high watch time), and 30–60 s **Shorts** cut from the
   best animated moments with a link to the full video.
6. **Seasonal calendar:** publish 2–3 weeks ahead of rainy season, autumn
   harvest, winter, Lunar New Year and summer holidays.
7. **Your own music identity:** a consistent piano "theme" across videos,
   which you can later release on Spotify via DistroKid as a second income
   stream. Only do this with music you own the rights to.
8. **4K export:** `--width 3840 --height 2160`. Relax content is played on TVs.

---

## 4. Monetization: what actually matters

- **YPP eligibility:** 1,000 subscribers plus 4,000 public watch hours in 12
  months (long-form ad revenue), or 10M Shorts views in 90 days. 31-minute
  videos pile up watch hours fast.
- **The real risk, "inauthentic / mass-produced content" (YPP policy):**
  YouTube rejects channels that look template-made with little variation, for
  example AI slideshows plus stock music published at volume. You can still get
  accepted with this format. What reviewers want to see is *your own creative
  input*: a consistent story and characters, custom motion and sound design,
  varied structure, and channel branding. Section 3 is exactly that list.
  Don't publish dozens of near-identical videos.
- **Music rights:** every track needs commercial and YouTube rights. Keep the
  licence or receipt for each one (paid AI-music plans included) to dispute
  Content ID claims.
- **AI disclosure:** YouTube's "altered or synthetic content" label is
  required for *realistic* content. Stylised anime illustration generally
  doesn't need it, but stating "AI-assisted illustrations" in the description
  costs nothing and builds trust.
- **The "Ghibli" name:** Studio Ghibli is a trademark, and its characters
  (Totoro, Kiki, etc.) and film music are copyrighted. An art *style* isn't
  protected, but never use their characters, logos or soundtrack, and prefer
  "Ghibli-inspired" or "cozy anime style" wording. Using the word in titles is
  common in this niche but carries some risk.
- **RPM expectations:** relax/sleep content usually earns a below-average RPM
  (very roughly $0.5–$3 per 1,000 views, depending on audience country), but
  it makes up for that with long watch sessions and evergreen views. A channel
  at the reference's level (about 4.6M views) would make low thousands of USD
  in total. Treat these as ballpark figures, not promises.

---

## Repo layout

```
README.md               ← this playbook
pipeline/make_video.py  ← automated video assembly (ffmpeg)
pipeline/prompts.md     ← image / motion / music / title prompt templates
```
