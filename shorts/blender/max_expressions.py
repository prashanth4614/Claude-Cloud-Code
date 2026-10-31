"""Max's hand-keyed expression library: ARKit face-unit weights (0..1) plus a little head/neck pose.

Each expression is what the animator keys on the beat word; animate_face() in build_max.py blends
between them with eased keys (ease in ~6 frames, hold, ease out). Tweak the numbers here, never in
the .blend, so every shot and every video gets the same Max.
"""

FACE_UNITS = {
    "browDownLeft", "browDownRight", "browInnerUp", "browOuterUpLeft", "browOuterUpRight", "cheekPuff",
    "cheekSquintLeft", "cheekSquintRight", "eyeBlinkLeft", "eyeBlinkRight", "eyeLookDownLeft",
    "eyeLookDownRight", "eyeLookInLeft", "eyeLookInRight", "eyeLookOutLeft", "eyeLookOutRight",
    "eyeLookUpLeft", "eyeLookUpRight", "eyeSquintLeft", "eyeSquintRight", "eyeWideLeft", "eyeWideRight",
    "jawForward", "jawLeft", "jawOpen", "jawRight", "mouthClose", "mouthDimpleLeft", "mouthDimpleRight",
    "mouthFrownLeft", "mouthFrownRight", "mouthFunnel", "mouthLeft", "mouthLowerDownLeft",
    "mouthLowerDownRight", "mouthPressLeft", "mouthPressRight", "mouthPucker", "mouthRight",
    "mouthRollLower", "mouthRollUpper", "mouthShrugLower", "mouthShrugUpper", "mouthSmileLeft",
    "mouthSmileRight", "mouthStretchLeft", "mouthStretchRight", "mouthUpperUpLeft", "mouthUpperUpRight",
    "noseSneerLeft", "noseSneerRight", "tongueOut",
}  # the 52 ARKit face units (MPFB faceunits01 pack)
EXTRA_UNITS = {"throatRise"}   # our own shape keys on Max.body, built by max_look.py (the larynx for swallowing)

# Face units not listed are 0. Keep weights below ~0.9 so the mesh never tears or looks rubbery.
EXPRESSIONS = {
    "neutral": {   # v6j (Codex 015: the bare mesh reads slightly worried): a calm, relaxed baseline
        "mouthSmileLeft": 0.1, "mouthSmileRight": 0.1, "browDownLeft": 0.12, "browDownRight": 0.12,
        "cheekSquintLeft": 0.05, "cheekSquintRight": 0.05,
    },
    # S01-S02 hook: one brow up, the other down, mouth pulled to one side, eyes slightly narrowed.
    "puzzled": {   # v6g (Codex 014): stronger brow asymmetry (one down hard, one up), narrowed, concentrating eyes
        "browDownLeft": 0.2, "browDownRight": 0.9, "browOuterUpLeft": 0.95, "browInnerUp": 0.15,
        "eyeSquintLeft": 0.45, "eyeSquintRight": 0.75, "noseSneerRight": 0.3,
        "mouthLeft": 0.6, "mouthPressLeft": 0.55, "mouthPressRight": 0.4, "mouthFrownLeft": 0.35,
        "mouthFrownRight": 0.5, "mouthRollLower": 0.2, "mouthShrugLower": 0.4,
    },
    # Pain (v4, stronger and asymmetric so it reads at phone size): brows knotted, one eye squeezed more.
    "wince": {   # v6e: both eyes squeezed, lips pressed tight (no teeth), symmetric; ear_pop is the one-eyed, open grimace
        "browDownLeft": 0.85, "browDownRight": 0.85, "browInnerUp": 0.45,
        "eyeSquintLeft": 0.8, "eyeSquintRight": 0.8, "eyeBlinkLeft": 0.75, "eyeBlinkRight": 0.7,
        "cheekSquintLeft": 0.75, "cheekSquintRight": 0.7, "noseSneerLeft": 0.6, "noseSneerRight": 0.55,
        "mouthStretchLeft": 0.6, "mouthStretchRight": 0.55, "mouthPressLeft": 0.6, "mouthPressRight": 0.6,
        "mouthRollLower": 0.25, "mouthClose": 0.05,
    },
    # The moment it hurts most (the ear-pop thumbnail face): one eye shut, teeth gritted, pulled to one side.
    "ear_pop": {   # v6e: strongly one-sided: left eye shut, right eye open, mouth yanked toward the ear, head tilted to it
        "browDownLeft": 0.95, "browDownRight": 0.55, "browInnerUp": 0.85, "browOuterUpRight": 0.3,
        "eyeBlinkLeft": 0.9, "eyeSquintLeft": 0.7, "cheekSquintLeft": 0.9,
        "eyeBlinkRight": 0.05, "eyeSquintRight": 0.35, "cheekSquintRight": 0.4, "eyeWideRight": 0.3,
        "noseSneerLeft": 0.9, "noseSneerRight": 0.45,
        "jawOpen": 0.24, "mouthStretchLeft": 0.9, "mouthStretchRight": 0.45, "mouthLeft": 0.45,
        "mouthUpperUpLeft": 0.75, "mouthUpperUpRight": 0.3, "mouthLowerDownLeft": 0.6,
        "mouthLowerDownRight": 0.3, "mouthFrownLeft": 0.4, "mouthFrownRight": 0.15,
    },
    # General reactions for any topic (v4).
    "surprised": {   # v6j: startled: brows maxed, eyes wide, jaw dropped, no smile at all, head pulled back
        "browInnerUp": 1.0, "browOuterUpLeft": 1.0, "browOuterUpRight": 0.95,
        "eyeWideLeft": 0.75, "eyeWideRight": 0.7, "jawOpen": 0.72,
        "mouthLowerDownLeft": 0.35, "mouthLowerDownRight": 0.35, "mouthUpperUpLeft": 0.15, "mouthUpperUpRight": 0.15,
        "mouthStretchLeft": 0.25, "mouthStretchRight": 0.25, "mouthFrownLeft": 0.1, "mouthFrownRight": 0.1,
    },
    "amazed": {   # v6j (Codex 015: same as surprised): delighted wonder: a big open smile, cheeks lifting the lower lids, soft brows
        "browInnerUp": 0.6, "browOuterUpLeft": 0.55, "browOuterUpRight": 0.5,
        "eyeWideLeft": 0.15, "eyeWideRight": 0.12, "cheekSquintLeft": 0.6, "cheekSquintRight": 0.55,
        "eyeSquintLeft": 0.3, "eyeSquintRight": 0.28,
        "jawOpen": 0.3, "mouthFunnel": 0.2, "mouthSmileLeft": 0.7, "mouthSmileRight": 0.65,
        "mouthUpperUpLeft": 0.2, "mouthUpperUpRight": 0.2, "mouthDimpleLeft": 0.2, "mouthDimpleRight": 0.2,
    },
    "curious": {   # v6g (Codex 014: read amused): a directed gaze at something, one brow high, lips parted, leaning in
        "browInnerUp": 0.6, "browOuterUpLeft": 0.95, "browOuterUpRight": 0.4,
        "eyeWideLeft": 0.4, "eyeWideRight": 0.3, "eyeLookOutLeft": 0.35, "eyeLookInRight": 0.35,
        "eyeLookDownLeft": 0.15, "eyeLookDownRight": 0.15,
        "mouthSmileLeft": 0.3, "mouthSmileRight": 0.1, "jawOpen": 0.07, "mouthClose": 0.02,
        "mouthLowerDownLeft": 0.12, "mouthLowerDownRight": 0.1,
    },
    "thinking": {   # v6e: a furrowed 'hmm': eyes up and away, lips pushed hard to one side and chin up
        "browDownLeft": 0.65, "browDownRight": 0.35, "browOuterUpRight": 0.55,
        "eyeLookUpLeft": 0.85, "eyeLookUpRight": 0.85, "eyeLookOutLeft": 0.5, "eyeLookInRight": 0.5,
        "eyeSquintLeft": 0.4, "eyeSquintRight": 0.2,
        "mouthPucker": 0.35, "mouthRight": 0.75, "mouthPressLeft": 0.45, "mouthRollLower": 0.3,
        "mouthShrugLower": 0.3, "cheekSquintRight": 0.25,
    },
    "scared": {   # v6g (Codex 014: read as worried): wide eyes with lifted lids, lips apart, corners pulled sideways and down
        "browInnerUp": 1.0, "browDownLeft": 0.35, "browDownRight": 0.35, "browOuterUpLeft": 0.3,
        "browOuterUpRight": 0.3, "eyeWideLeft": 0.85, "eyeWideRight": 0.85,
        "jawOpen": 0.2, "mouthStretchLeft": 0.85, "mouthStretchRight": 0.85, "mouthLowerDownLeft": 0.45,
        "mouthLowerDownRight": 0.45, "mouthFrownLeft": 0.35, "mouthFrownRight": 0.35, "mouthUpperUpLeft": 0.15,
        "mouthUpperUpRight": 0.15,
    },
    "laughing": {   # v6j (Codex 015: 'sleepy eyes'): cheeks push up into the lower lids (squint, not blink), nose crinkles
        "mouthSmileLeft": 0.95, "mouthSmileRight": 0.9, "jawOpen": 0.4, "mouthUpperUpLeft": 0.35,
        "mouthUpperUpRight": 0.35, "cheekSquintLeft": 1.0, "cheekSquintRight": 0.95,
        "eyeSquintLeft": 0.8, "eyeSquintRight": 0.75, "eyeBlinkLeft": 0.12, "eyeBlinkRight": 0.1,
        "mouthDimpleLeft": 0.3, "mouthDimpleRight": 0.3, "noseSneerLeft": 0.2, "noseSneerRight": 0.2,
        "browInnerUp": 0.15, "browDownLeft": 0.1, "browDownRight": 0.1,
    },
    "disgusted": {   # v6e: an 'ew': nose wrinkled hard, upper lip lifted, chin pushed up, head drawn back and away
        "noseSneerLeft": 1.0, "noseSneerRight": 0.85, "mouthUpperUpLeft": 1.0, "mouthUpperUpRight": 0.7,
        "browDownLeft": 0.85, "browDownRight": 0.6, "eyeSquintLeft": 0.75, "eyeSquintRight": 0.55,
        "mouthFrownLeft": 0.7, "mouthFrownRight": 0.55, "mouthLeft": 0.25, "cheekSquintLeft": 0.75,
        "cheekSquintRight": 0.4, "mouthShrugLower": 0.5, "mouthShrugUpper": 0.4,
    },
    # S12a "swallowing": lips pressed and rolled in, jaw slightly forward, soft blink.
    "swallow": {   # v5: the larynx visibly rises (throatRise, max_look.add_throat_rise), lips sealed
        "mouthRollLower": 0.45, "mouthRollUpper": 0.3, "mouthPressLeft": 0.5, "mouthPressRight": 0.5,
        "mouthClose": 0.2, "jawForward": 0.15, "eyeBlinkLeft": 0.3, "eyeBlinkRight": 0.3,
        "browInnerUp": 0.2, "throatRise": 1.0,
    },
    # S12b "yawning": jaw fully open, eyes squeezed nearly shut, brows lifted, nose crinkled.
    "yawn": {
        "jawOpen": 0.95, "mouthFunnel": 0.2, "mouthStretchLeft": 0.25, "mouthStretchRight": 0.25,
        "mouthLowerDownLeft": 0.3, "mouthLowerDownRight": 0.3,
        "eyeBlinkLeft": 0.8, "eyeBlinkRight": 0.8, "eyeSquintLeft": 0.45, "eyeSquintRight": 0.45,
        "browInnerUp": 0.55, "noseSneerLeft": 0.3, "noseSneerRight": 0.3, "cheekSquintLeft": 0.3,
        "cheekSquintRight": 0.3,
    },
    # S12b "chewing gum": one chew pose; animate_face alternates it with chew_b on a 9-frame cycle.
    # Chewing (v5, Codex 011 finding): the jaw opens but the lips stay sealed: mouthClose follows jawOpen at
    # ~0.7, so the jaw moves under closed lips; the cheeks fill as the bolus moves. build_max.chew_cycle()
    # alternates chew / chew_b.
    # v6c (Codex 012): bigger, sealed jaw work; cheek fullness suggested on one side with the opposite
    # squint/press (the 52 units have no one-sided cheek puff). chew_r / chew_b_r mirror them (below).
    "chew": {   # v6j (Codex 015: read as lip-pursing): jaw-led, relaxed lips (no press/shrug bunching), cheek compression
        "jawOpen": 0.62, "mouthClose": 0.6,
        "jawLeft": 0.75, "jawForward": 0.06,
        "mouthLeft": 0.15, "cheekPuff": 0.75, "cheekSquintRight": 0.5, "cheekSquintLeft": 0.15,
        "mouthPressLeft": 0.2, "mouthPressRight": 0.2,   # v6k: a light press seals the peak (the Mac saw a gap)
    },
    "chew_b": {   # v6j: a real in-between (jaw half up, still moving), so the cycle reads continuous, not peak-flat-peak
        "jawOpen": 0.28, "mouthClose": 0.26,
        "jawLeft": 0.3, "mouthLeft": 0.06,
        "cheekPuff": 0.45, "cheekSquintRight": 0.25,
    },
    # S12b "pull the tube open": relief, a soft closed-mouth smile and relaxed eyes.
    "relief_smile": {   # v6e: an exhale of relief: eyes closing, inner brows soft up, gentle closed smile, head tipped back
        "browInnerUp": 0.55, "browOuterUpLeft": 0.2, "browOuterUpRight": 0.2,
        "eyeBlinkLeft": 0.65, "eyeBlinkRight": 0.65, "eyeSquintLeft": 0.2, "eyeSquintRight": 0.2,
        "mouthSmileLeft": 0.5, "mouthSmileRight": 0.45, "mouthClose": 0.02, "mouthRollLower": 0.1,
        "cheekSquintLeft": 0.35, "cheekSquintRight": 0.35, "cheekPuff": 0.12,
    },
    # S13 "Follow for more": big open grin to camera (the hand does the thumbs-up).
    "thumbs_up": {
        "mouthSmileLeft": 0.9, "mouthSmileRight": 0.9, "jawOpen": 0.12, "mouthUpperUpLeft": 0.2,
        "mouthUpperUpRight": 0.2, "mouthLowerDownLeft": 0.2, "mouthLowerDownRight": 0.2,
        "cheekSquintLeft": 0.55, "cheekSquintRight": 0.55, "eyeSquintLeft": 0.25,
        "eyeSquintRight": 0.25, "browOuterUpLeft": 0.25, "browOuterUpRight": 0.25,
    },
}

# Head and neck rotation in degrees (x = nod down, y = tilt to his left, z = turn to his left).
HEAD_POSE = {
    "neutral": (0, 0, 0),
    "puzzled": (-2, 9, 9),
    "wince": (8, -3, 0),
    "ear_pop": (5, -9, -12),
    "surprised": (-9, 0, 0),
    "amazed": (-5, 5, 3),
    "curious": (7, 8, 8),
    "thinking": (-12, -10, -8),
    "scared": (10, -8, 0),
    "laughing": (-10, 4, 0),
    "disgusted": (-5, -14, -8),
    "swallow": (10, 0, 0),       # v6b: a chin tuck, so a still reads as swallowing
    "yawn": (-14, 3, 0),
    "chew": (7, -5, 0),
    "chew_b": (1, -2, 0),
    "relief_smile": (-12, -4, 3),
    "thumbs_up": (-1, 5, 0),
}

def _mirror_chew(units):
    def opposite(name):
        if name.endswith("Left"):
            return name[:-4] + "Right"
        if name.endswith("Right"):
            return name[:-5] + "Left"
        return name
    return {opposite(k): v for k, v in units.items()}


for _name in ("chew", "chew_b"):     # the bolus moves side to side: alternate chews mirror
    EXPRESSIONS[_name + "_r"] = _mirror_chew(EXPRESSIONS[_name])
    _x, _y, _z = HEAD_POSE[_name]
    HEAD_POSE[_name + "_r"] = (_x, -_y, -_z)
    assert set(EXPRESSIONS[_name]) <= FACE_UNITS

SHEET_ORDER = ["neutral", "puzzled", "curious", "thinking", "surprised", "amazed", "scared", "wince", "ear_pop",
               "disgusted", "laughing", "relief_smile", "swallow", "yawn", "chew", "thumbs_up"]
