# Meshy free-tier trial (2026-10-31): needs owner sign-in

**Update (2026-10-31, 21:10–22:10 IST):**
- The Meshy workspace was opened in the automation Chrome on the Mac and brought to the front for the
  owner to sign in.
- It was checked every minute for 60 minutes: **still not signed in**. The trial was not run, and
  0 credits were spent.
- The window is left open (Chrome with the profile `out/reference/profile`). Once the owner has signed
  in there, re-send the task and the helper will run it.

**Status: not run. Needs the owner to sign in.** Nothing was generated and no credits were spent. No
account was created and no credentials were entered.

## What happened

- The Mac helper opened https://www.meshy.ai/workspace in its automation Chrome. That is a separate
  Playwright profile at `out/reference/profile`, not the owner's everyday Chrome.
- The page shows **"Log In | Sign Up Free"**, so it is not signed in, and the trial stopped there as the
  rules require.

## What the workspace showed (logged out, 2026-10-31)

| Item | Value |
|---|---|
| Model options | **Meshy 7.1 – Flagship** ("most detail, highest precision", the latest), Meshy 6, Meshy 6 Lite |
| Modes | Image and Text tabs under "Model"; also Agent, Print, Animate |
| Options | Resolution: Standard / Ultra 2K / Ultra 4K; Texture; Pose (A-Pose / T-Pose / Custom); Smart Topology; License switch "CC BY 4.0" / Private |
| Cost shown | **20 credits, about 1 min** per generation, with texture on and Standard resolution. Not checked whether Ultra or remesh costs more |

**Budget:** 3 models × 20 credits = **60**, exactly the cap. So no retries fit, and any paid remesh or a
higher resolution would go over.

## To run it

1. On the Mac, open the automation Chrome profile and sign in to Meshy (the owner's own account).
   Ask the web helper to "open Meshy for sign-in", and it will open
   https://www.meshy.ai/workspace in that profile for the owner to log in by hand. Or sign in directly
   if that window is already open.
2. Then re-send the trial task. The helper checks it is signed in, confirms the free plan and the
   credit balance, makes the three Text-to-3D models (bench, commuter, coach) at 20 credits each, and
   records paths, credits, times, rigging/remesh cost and preview screenshots in this file.

Prompts, ready for the run:
1. Bench: "Indian railway station platform bench, steel frame, three seats with armrests, chipped blue
   paint, realistic, real-world proportions"
2. Commuter: "Indian male office commuter, about 30, short-sleeved checked shirt, dark trousers, leather
   sandals, backpack, standing in A-pose, realistic proportions" (plus free auto-rigging if it costs 0
   credits)
3. Coach: "section of a Mumbai suburban local train coach, white body with purple stripe, one open
   doorway without doors, barred windows, realistic"
