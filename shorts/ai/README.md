# AI-visuals version: shot pack for "Why Your Ears Pop on a Plane"

Version 4 of Short #1. It has the same narration, captions, music and SFX as
the 2D, Three.js and Blender versions, so only the visuals differ.

**Workflow:** generate stills in **ChatGPT** or **Gemini**, then animate the
best ones with **Veo** (Gemini app or Google Flow). Save each shot as
`shorts/ai/ear_pop/shots/NN.png` or `NN.mp4`, then run:

```bash
python3 shorts/ear_pop_ai.py --voice en_US-joe-medium.onnx --shots shorts/ai/ear_pop/shots
```

Missing shots render as placeholders, so you can preview after every few shots.
Any aspect ratio works: the assembler crops to 9:16, so **keep the subject centred**.

---

## Step 0: Make the character sheet (do this once, reuse it forever)

Paste this into **ChatGPT** (or Gemini) and keep the result as `max_sheet.png`:

> Character turnaround sheet of an original 3D animated character named Max: a friendly man in his late 20s,
> slightly stylized proportions (large expressive brown eyes, soft rounded features, short messy dark-brown hair),
> wearing a teal crew-neck t-shirt. Front view, 3/4 view, side view, plus 4 facial expressions
> (neutral, wincing in discomfort, big yawn, happy smile). High-end 3D animated film look, soft studio lighting,
> subsurface skin, plain light-grey background, no text, no logos.

Then **attach `max_sheet.png` to every prompt that shows Max** and start it with
*"Using the attached character sheet, keep Max exactly the same:"*. This is the
single biggest factor in looking professional.

## Style suffix (append to every image prompt)

> …high-end 3D animated film still, cinematic lighting, shallow depth of field, rich colour, vertical 9:16 composition,
> subject centred, no text, no labels, no watermark, no logos.

For the **inside-the-body** shots use this suffix instead:

> …stylized 3D medical visualization, glowing translucent tissue, soft volumetric light, dark warm background,
> clean and non-gory, vertical 9:16, subject centred, no text, no labels.

Never put words in the images. The assembler adds every label, number and caption, so they're always spelled right.

---

## The 13 shots

The duration column is how long each line is on screen. One Veo clip (~8 s) covers any of them.
**Animate** marks the shots that are worth spending Veo generations on. The rest can stay stills, which get a slow camera move automatically.

| # | Line (narration) | Dur | Image prompt (+ suffix) | Animate? Motion prompt for Veo |
|---|---|---|---|---|
| 01 | "Ever wondered why your ears pop on a plane?" | 2.3 s | A white passenger jet climbing steeply through golden-hour clouds, dramatic low angle, sun flare | ⭐ **Yes.** "The jet climbs toward camera through the clouds, clouds streaming past fast, camera tracks with it." |
| 02 | "Here's what's actually happening inside your head." | 2.5 s | Max in an airplane window seat, touching his ear with a puzzled face, warm cabin light, clouds in the window | ⭐ **Yes.** "Slow push-in toward Max's ear, he tilts his head slightly, subtle cabin vibration." |
| 03 | "Behind your eardrum is a tiny pocket of air, called the middle ear." | 3.5 s | Cutaway cross-section inside a human head: the ear canal tube leading to a thin pearly eardrum membrane, behind it a small glowing air-filled chamber with three tiny bones | ⭐ **Yes.** "Camera glides slowly down the ear canal toward the glowing eardrum, tiny air particles drifting." |
| 04 | "On the ground, the air pressure inside matches the air outside." | 3.6 s | Same cross-section, perfectly calm, soft balanced blue glow on both sides of a flat eardrum, air particles evenly spread | Still is fine |
| 05 | "But as the plane climbs, the air pressure in the cabin drops." | 3.4 s | The jet high above a sea of clouds, deep blue thin-air sky, cold light | Optional: "Jet cruises upward, clouds fall away below." |
| 06 | "The air trapped inside pushes out, and your eardrum bulges like a balloon." | 4.0 s | Close-up of the eardrum membrane stretched and bulging outward like a balloon, glowing red at the edges from strain, air particles crowded behind it | ⭐ **Yes.** "The membrane slowly inflates outward like a balloon, stretching, pulsing gently." |
| 07 | "That's the muffled, blocked feeling." | 2.0 s | Max wincing, hand pressed over one ear, eyes squeezed, the cabin behind him blurred and muted | Optional: "Max shakes his head slightly, discomfort." |
| 08 | "Then a tiny tube to your throat, the Eustachian tube, cracks open." | 3.7 s | Cross-section showing a narrow tube running from the middle-ear chamber down to the throat, the tube opening up, glowing air bubbles starting to rush down it | ⭐ **Yes.** "The tube widens open and glowing air bubbles rush down through it." |
| 09 | "Air escapes, the pressure evens out, and... POP!" | 3.2 s | The eardrum snapping back flat with a bright burst of light and a circular shockwave ripple | ⭐ **Yes.** "The membrane snaps flat in an instant, burst of light, shockwave ripple." |
| 10 | "Landing is actually worse." | 1.7 s | The jet descending toward glittering city lights at dusk, landing gear down | Optional: "Jet descends toward the city lights." |
| 11 | "The tube doesn't open on its own as easily, so your eardrum gets pushed inward." | 4.2 s | The eardrum pressed inward, and the narrow tube pinched shut, glowing warning red | ⭐ **Yes.** "The membrane is pushed inward, the tube squeezes shut, red warning glow pulses." |
| 12 | "That's why swallowing, yawning, or chewing gum helps. They pull the tube open." | 4.4 s | Max in his seat mid-yawn, big open mouth, relaxed, warm light | Optional: "Max yawns widely, then relaxes into a relieved smile." |
| 13 | "Follow for more weird things your body does." | 2.8 s | Max smiling at the camera, giving a thumbs-up, cozy cabin light | Optional: "Max smiles and gives a thumbs-up to camera." |

Keep the top ~15% and the area around 75–80% height fairly simple: the HUD badges sit at the top and the captions sit low.

---

## How to animate (Veo)

1. Generate the still first and pick the best one. **Image-to-video beats text-to-video** for consistency.
2. In the **Gemini app**: upload the still, ask *"Animate this image: <motion prompt>"*, and choose 9:16 if offered.
   In **Google Flow**: use *Frames to Video* with the still as the first frame. It gives more control and can extend clips.
3. Motion prompts should be **one camera move plus one action**. Big character acting is where AI video breaks.
4. Veo adds its own sound. The assembler **drops the clip audio** and uses our narration and SFX instead.
5. Prioritise the ⭐ shots (01, 02, 03, 06, 08, 09, 11). That's 7 clips. Stills cover the rest.

## Quality checklist (reject and regenerate if any fail)

- [ ] Max looks like the **same person** as in the character sheet (face, hair, shirt colour)
- [ ] No garbled text, logos or extra fingers
- [ ] The subject is centred, with nothing important in the outer 15% on the left or right (9:16 crop)
- [ ] The anatomy reads clearly at phone size: one idea per shot
- [ ] Colour and lighting match the neighbouring shots, so the cuts feel like one film

## Rights and disclosure

- Check the current terms of each tool for commercial use. OpenAI's and Google's terms generally leave
  ownership of outputs with you, but plans and terms change, so confirm before monetizing.
- Veo clips carry an invisible SynthID watermark, and some plans or apps add a visible one too. Check this before you upload.
- YouTube's "altered or synthetic" label is for **realistic** footage. A stylized 3D cartoon generally
  doesn't need it, but YouTube may auto-label AI-made content, and that's fine.
