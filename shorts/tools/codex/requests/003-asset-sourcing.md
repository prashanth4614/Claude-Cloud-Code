Debate request (under 450 words). Owner's ask: stop hand-modelling everything; get 3D assets free (or
cheap) WITHOUT compromising quality, to look like Zack D Films. Argue against my plan where it's weak.

## Needs (pilot "Why your ears pop on a plane", and reused in future videos)
A. Airliner exterior (S01/S05a/S10). Now: our procedural twin-jet (`sets/airliner.py`), passable, not hero.
B. Cabin interior + seats (S02/S07/S12b/S13, Max sits in it). Now: procedural (`sets/cabin.py`), decent.
C. Ear anatomy (canal, eardrum, ossicles, Eustachian tube; inside fly-through + x-ray map). Now:
   procedural tunnels with wet tissue shading (`sets/ear.py`); stylized, works for the journey.
D. Cumulus clouds near the jet. Now: volumetric lobes (4th attempt; render cost unknown yet).
E. Dusk city from ~30 m (S10). Now: procedural blocks with lit windows, OK.
F. Host character Max (MPFB2 base; owner wants Pixar-ish stylized-realistic face, hair still weak).

## Candidates found (checked via each site's search API today)
- Sketchfab, free account + API token, licence CC-BY (credit in description):
  "AIRBUS A320 (Indonesian Presidential Livery)" 114k faces; "Boeing 787-9 Singapore Airlines" 444k;
  "Air India A321 Exteriors + Interiors" 476k; "Airplane interior" 1.41M; "A detail airplane cabin
  [Blender]" 804k; "Airplane Cabin Pieces" 9.9k; "Ear Set" 12.9k (outer ears only); night-city
  low-poly buildings (stylized). No CC0/CC-BY middle-ear anatomy found (the good ones are NC).
- BlenderKit (add-on; free tier = royalty-free/CC0 free assets; paid tier ~monthly sub):
  FREE "Cumulus Cloud - randomizing", "Buildings", "Highrise Building"; PAID "Generic Airbauss A320
  Airplane", "Cloud Layer Puffy Cumulus VDB", "Procedural Cloud Sky Dome", "Modular City Block".
- Paid marketplaces (royalty-free licence): CGTrader/RenderHub generic airliners and cabins ~$20-60.
- Anatomy: Z-Anatomy / BodyParts3D (CC-BY-SA) have ossicles + tympanic membrane meshes.
- Owner's AI image -> image-to-3D (Meshy/Tripo/Hunyuan3D) for one-off hero props (images by owner only).

## My draft plan
1. Airliner: Sketchfab CC-BY A320 (114k), strip real livery, apply our teal livery (avoid trademarks).
2. Cabin: keep ours for now (Max's acting and camera blocking are built around it); maybe swap seats
   for a Sketchfab/BlenderKit seat model later.
3. Ear: keep our stylized tunnels (Zack-style journeys are stylized anyway); add BodyParts3D ossicles
   for the x-ray map only.
4. Clouds: try BlenderKit free "Cumulus Cloud - randomizing" vs our volume lobes; paid VDB if needed.
5. City: keep ours (it's lit and reads well), or BlenderKit free buildings for variety.
6. Max: keep; revisit with a paid character tool later.
Accounts/costs for the owner: free Sketchfab + BlenderKit accounts; maybe 1 BlenderKit month or one
$20-40 model.

Answer: (1) per need, keep / replace / which candidate, and why, in Zack D Films terms (what the viewer
actually notices in a 1-3 s shot); (2) anything I missed that gives a bigger quality jump per hour or
per rupee (e.g. Fab/Quixel free assets, Character Creator/ActorCore, Mixamo, Polyhaven models);
(3) licence or trademark traps (airline liveries, aircraft shapes, CC-BY-SA, Sketchfab "Free Standard");
(4) your final ranked top-3 actions.
