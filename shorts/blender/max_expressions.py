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

# Face units not listed are 0. Keep weights below ~0.9 so the mesh never tears or looks rubbery.
EXPRESSIONS = {
    "neutral": {},
    # S01-S02 hook: one brow up, the other down, mouth pulled to one side, eyes slightly narrowed.
    "puzzled": {   # v4: stronger asymmetry, mouth pulled hard to one side, lips pressed
        "browOuterUpLeft": 0.85, "browInnerUp": 0.55, "browDownRight": 0.6,
        "eyeSquintRight": 0.7, "eyeWideLeft": 0.35,
        "mouthLeft": 0.7, "mouthPressLeft": 0.6, "mouthPressRight": 0.35, "mouthRollLower": 0.25,
        "mouthFrownRight": 0.25,
    },
    # Pain (v4, stronger and asymmetric so it reads at phone size): brows knotted, one eye squeezed more.
    "wince": {
        "browDownLeft": 0.9, "browDownRight": 0.7, "browInnerUp": 0.6,
        "eyeSquintLeft": 0.85, "eyeSquintRight": 0.6, "eyeBlinkLeft": 0.7, "eyeBlinkRight": 0.35,
        "cheekSquintLeft": 0.8, "cheekSquintRight": 0.55, "noseSneerLeft": 0.7, "noseSneerRight": 0.5,
        "mouthStretchLeft": 0.7, "mouthStretchRight": 0.5, "mouthUpperUpLeft": 0.45, "mouthUpperUpRight": 0.3,
        "mouthLowerDownLeft": 0.3, "mouthLowerDownRight": 0.2, "mouthFrownLeft": 0.25, "mouthFrownRight": 0.2,
        "jawOpen": 0.1,
    },
    # The moment it hurts most (the ear-pop thumbnail face): one eye shut, teeth gritted, pulled to one side.
    "ear_pop": {
        "browDownLeft": 0.95, "browDownRight": 0.75, "browInnerUp": 0.85,
        "eyeBlinkLeft": 0.88, "eyeSquintLeft": 0.7, "cheekSquintLeft": 0.9,
        "eyeBlinkRight": 0.18, "eyeSquintRight": 0.5, "cheekSquintRight": 0.55, "eyeWideRight": 0.12,
        "noseSneerLeft": 0.85, "noseSneerRight": 0.6,
        "jawOpen": 0.16, "mouthStretchLeft": 0.85, "mouthStretchRight": 0.6, "mouthLeft": 0.25,
        "mouthUpperUpLeft": 0.7, "mouthUpperUpRight": 0.45, "mouthLowerDownLeft": 0.55,
        "mouthLowerDownRight": 0.4, "mouthFrownLeft": 0.35, "mouthFrownRight": 0.2,
    },
    # General reactions for any topic (v4).
    "surprised": {
        "browInnerUp": 0.9, "browOuterUpLeft": 0.85, "browOuterUpRight": 0.75,
        "eyeWideLeft": 0.85, "eyeWideRight": 0.8, "jawOpen": 0.35, "mouthFunnel": 0.25,
        "mouthLowerDownLeft": 0.3, "mouthLowerDownRight": 0.3,
    },
    "amazed": {   # "wow": soft O mouth, lifted brows, eyes wide but warm
        "browInnerUp": 0.7, "browOuterUpLeft": 0.65, "browOuterUpRight": 0.55,
        "eyeWideLeft": 0.55, "eyeWideRight": 0.5, "cheekSquintLeft": 0.15, "cheekSquintRight": 0.15,
        "jawOpen": 0.42, "mouthFunnel": 0.5, "mouthPucker": 0.2, "mouthSmileLeft": 0.15, "mouthSmileRight": 0.1,
    },
    "curious": {  # one brow high, the other low, a half-smile pulled to one side (v4: bigger)
        "browOuterUpLeft": 0.85, "browInnerUp": 0.45, "browDownRight": 0.45,
        "eyeWideLeft": 0.45, "eyeSquintRight": 0.55, "mouthLeft": 0.45, "mouthSmileLeft": 0.45,
        "mouthPressRight": 0.4, "mouthDimpleLeft": 0.3, "cheekSquintLeft": 0.25,
    },
    "thinking": {  # eyes up and to the side, lips pushed to one side, one brow down (v4: bigger)
        "browDownLeft": 0.55, "browInnerUp": 0.5, "browOuterUpRight": 0.4,
        "eyeLookUpLeft": 0.8, "eyeLookUpRight": 0.8, "eyeLookOutLeft": 0.45, "eyeLookInRight": 0.45,
        "mouthPucker": 0.45, "mouthRight": 0.55, "mouthPressLeft": 0.35, "mouthRollLower": 0.2,
        "eyeSquintLeft": 0.25,
    },
    "scared": {   # inner brows up and together, eyes wide, mouth stretched back
        "browInnerUp": 0.95, "browDownLeft": 0.25, "browDownRight": 0.25,
        "eyeWideLeft": 0.9, "eyeWideRight": 0.9, "mouthStretchLeft": 0.65, "mouthStretchRight": 0.65,
        "jawOpen": 0.22, "mouthLowerDownLeft": 0.35, "mouthLowerDownRight": 0.35,
    },
    "laughing": {
        "mouthSmileLeft": 0.95, "mouthSmileRight": 0.9, "jawOpen": 0.4, "mouthUpperUpLeft": 0.3,
        "mouthUpperUpRight": 0.3, "cheekSquintLeft": 0.85, "cheekSquintRight": 0.8,
        "eyeSquintLeft": 0.6, "eyeSquintRight": 0.55, "eyeBlinkLeft": 0.35, "eyeBlinkRight": 0.3,
        "browInnerUp": 0.2,
    },
    "disgusted": {  # v4: a big one-sided sneer, upper lip curled, brows down, head pulled back
        "noseSneerLeft": 0.95, "noseSneerRight": 0.7, "mouthUpperUpLeft": 0.85, "mouthUpperUpRight": 0.55,
        "browDownLeft": 0.8, "browDownRight": 0.55, "eyeSquintLeft": 0.7, "eyeSquintRight": 0.45,
        "mouthFrownLeft": 0.55, "mouthFrownRight": 0.4, "mouthLeft": 0.3, "cheekSquintLeft": 0.6,
        "mouthShrugUpper": 0.3,
    },
    # S12a "swallowing": lips pressed and rolled in, jaw slightly forward, soft blink.
    "swallow": {
        "mouthRollLower": 0.45, "mouthRollUpper": 0.3, "mouthPressLeft": 0.5, "mouthPressRight": 0.5,
        "mouthClose": 0.2, "jawForward": 0.15, "eyeBlinkLeft": 0.3, "eyeBlinkRight": 0.3,
        "browInnerUp": 0.2,
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
    "chew": {
        "jawOpen": 0.22, "jawLeft": 0.12, "mouthLeft": 0.2, "mouthPucker": 0.15, "cheekPuff": 0.12,
        "mouthRollLower": 0.1,
    },
    "chew_b": {
        "jawOpen": 0.04, "jawRight": 0.08, "mouthRight": 0.1, "mouthPressLeft": 0.3,
        "mouthPressRight": 0.3, "cheekPuff": 0.1,
    },
    # S12b "pull the tube open": relief, a soft closed-mouth smile and relaxed eyes.
    "relief_smile": {  # v4: a fuller smile, eyes softly closing, brows lifted
        "browOuterUpLeft": 0.35, "browOuterUpRight": 0.35,
        "mouthSmileLeft": 0.65, "mouthSmileRight": 0.6, "mouthDimpleLeft": 0.3, "mouthDimpleRight": 0.3,
        "cheekSquintLeft": 0.45, "cheekSquintRight": 0.45, "eyeSquintLeft": 0.3, "eyeSquintRight": 0.3,
        "eyeBlinkLeft": 0.15, "eyeBlinkRight": 0.15, "browInnerUp": 0.35,
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
    "puzzled": (-3, 8, 6),
    "wince": (6, -6, 0),
    "ear_pop": (5, -9, -4),
    "surprised": (-5, 0, 0),
    "amazed": (-7, 4, 0),
    "curious": (-4, 8, 6),
    "thinking": (-11, -9, -10),
    "scared": (5, 0, 0),
    "laughing": (-10, 4, 0),
    "disgusted": (6, -10, -8),
    "swallow": (4, 0, 0),
    "yawn": (-14, 3, 0),
    "chew": (0, 0, 0),
    "chew_b": (0, 0, 0),
    "relief_smile": (-6, -5, 0),
    "thumbs_up": (-1, 5, 0),
}

SHEET_ORDER = ["neutral", "puzzled", "curious", "thinking", "surprised", "amazed", "scared", "wince", "ear_pop",
               "disgusted", "laughing", "relief_smile", "swallow", "yawn", "chew", "thumbs_up"]
