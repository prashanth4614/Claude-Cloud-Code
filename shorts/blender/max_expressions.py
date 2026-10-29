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
    "puzzled": {
        "browOuterUpLeft": 0.9, "browInnerUp": 0.52, "browDownRight": 0.68,
        "eyeSquintRight": 0.52, "eyeWideLeft": 0.22,
        "mouthLeft": 0.52, "mouthPressLeft": 0.45, "mouthPressRight": 0.22, "mouthRollLower": 0.15,
    },
    # S07 "muffled, blocked feeling": eyes screwed up, nose wrinkled, teeth-gritting stretch.
    "wince": {
        "browDownLeft": 0.8, "browDownRight": 0.8, "browInnerUp": 0.25,
        "eyeSquintLeft": 0.8, "eyeSquintRight": 0.8, "eyeBlinkLeft": 0.45, "eyeBlinkRight": 0.55,
        "cheekSquintLeft": 0.6, "cheekSquintRight": 0.6,
        "noseSneerLeft": 0.55, "noseSneerRight": 0.55,
        "mouthStretchLeft": 0.45, "mouthStretchRight": 0.5, "mouthUpperUpLeft": 0.25,
        "mouthUpperUpRight": 0.3, "mouthFrownLeft": 0.2, "mouthFrownRight": 0.2, "jawOpen": 0.06,
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
    "relief_smile": {
        "mouthSmileLeft": 0.7, "mouthSmileRight": 0.65, "mouthDimpleLeft": 0.3, "mouthDimpleRight": 0.3,
        "cheekSquintLeft": 0.45, "cheekSquintRight": 0.45, "eyeSquintLeft": 0.3, "eyeSquintRight": 0.3,
        "eyeBlinkLeft": 0.12, "eyeBlinkRight": 0.12, "browInnerUp": 0.2,
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
    "puzzled": (-3, 9, 6),
    "wince": (6, -6, 0),
    "swallow": (4, 0, 0),
    "yawn": (-14, 3, 0),
    "chew": (0, 0, 0),
    "chew_b": (0, 0, 0),
    "relief_smile": (-2, -4, 0),
    "thumbs_up": (-1, 5, 0),
}

SHEET_ORDER = ["neutral", "puzzled", "wince", "swallow", "yawn", "chew", "relief_smile", "thumbs_up"]
