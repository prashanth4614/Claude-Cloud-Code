# Prompt pack

Replace `{…}` placeholders. Keep the **style suffix** and the **family block**
identical in every prompt so characters and look stay consistent.

## Style suffix (append to every image prompt)
```
hand-painted 2D anime background art, soft cel shading, watercolor sky,
warm nostalgic atmosphere, gentle film grain, highly detailed environment,
cinematic composition, 16:9
```

## Family block (an original family; don't copy existing characters)
```
a young family: father (30s, short black hair, blue plaid flannel shirt),
mother (30s, shoulder-length brown hair, rust-red blouse), son (8, messy black
hair, light-blue shirt), daughter (6, brown bob with small pigtails, orange top)
```
Generate a **character sheet** first (front/side views of all four) and use it
as the reference image (`--cref` in Midjourney, a reference upload in other
tools).

## Scene prompt template
```
{FAMILY BLOCK} {action} inside/at {setting}, {time of day}, {weather},
{lighting: warm lamp light / golden hour / blue rainy dusk}, {STYLE SUFFIX}
```

### Example shot list: "Rainy Road Trip" (expand to 30–60 shots)
| # | Action / setting | Weather & light | SFX |
|---|---|---|---|
| 1 | Loading bags into an old yellow camper van in front of a country house | misty morning | birds, van door |
| 2 | Van driving on a wet coastal road, seen from a hill | light rain, grey-blue | rain, engine hum |
| 3 | Kids pressing faces to the rain-streaked window | soft window light | rain on glass |
| 4 | Mother cooking soup on a small stove inside the van while dad drives | warm interior light | sizzle, simmer |
| 5 | Family eating noodles at the fold-out table | lamp light, rain outside | slurping, rain |
| 6 | Van parked by a lake, umbrellas, rain rings on the water | overcast | rain on umbrella |
| 7 | Dad and son grilling sweet potatoes under the awning | dusk, orange glow | fire crackle |
| 8 | Kids asleep under blankets, rain on the skylight | night, blue + warm | heavy rain, thunder far |
| 9 | Thumbnail: cutaway view of the van showing every cozy room at once | night, stars, warm windows | — |

## Image-to-video motion prompts (Kling / Runway / Luma / Veo)
```
static camera, gentle steam rising from the pot, rain streaks on window, subtle breathing, no camera shake
slow push-in, campfire flickering, sparks drifting up, characters blink softly
static camera, raindrops hitting the lake surface, leaves swaying lightly
```
Keep it subtle. Big character motion is where AI video breaks.

## Music prompts (Suno / Udio paid tier, or search terms for a licensed library)
```
gentle solo piano, soft strings, nostalgic Japanese countryside, warm, 70 bpm, instrumental, slow waltz 3/4
music box and acoustic guitar lullaby, cozy rainy evening, 65 bpm, instrumental, soft and sleepy
lofi piano, vinyl crackle, rainy window, relaxed, 75 bpm, instrumental
```
Don't prompt with real composer or film names. It's against most tools'
terms and makes Content ID problems more likely.

## Title templates
```
Cozy {activity} with Family {emoji} | Relaxing Piano & Rain Sounds for Sleep & Study
A Rainy Day in Our {setting} 🌧️ | Cozy Anime-Style Ambience
Back to Childhood: {activity} with Grandparents in the Countryside 🌾 | Relaxing Music
```

## Description template
```
{2 lines of mood: "Rain taps on the roof of our little camper van while soup simmers…"}

🎵 Tracklist
{paste out/*.tracklist.txt}

Illustrations: AI-assisted, edited by {channel}. Music: {source + licence}.
#cozyanimation #relaxingmusic #rainsounds
```
