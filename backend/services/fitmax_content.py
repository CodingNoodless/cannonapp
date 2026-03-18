"""
Structured Fitmax curriculum content.

All content is represented as data so it can be personalized server-side
without shipping mobile app updates.
"""

from __future__ import annotations

from typing import Any, Dict, List


GOAL_BRANCH_CONTENT: Dict[str, Dict[str, Any]] = {
    "lose_weight_cut": {
        "goal_sentence": "You will lose fat while protecting muscle through a smart deficit and high-protein training.",
        "science": [
            "A deficit drives fat loss, but aggressive cuts increase fatigue and muscle loss risk.",
            "Keep protein high and resistance training consistent to preserve lean mass.",
            "Cardio helps, but your calorie target and adherence matter most.",
        ],
    },
    "gain_muscle_bulk": {
        "goal_sentence": "You will build muscle by combining progressive training with a controlled calorie surplus.",
        "science": [
            "Muscle gain requires training stimulus plus enough fuel to recover and adapt.",
            "A small surplus is usually better than a dirty bulk for physique quality.",
            "Protein and sleep quality determine how much of your gain is muscle.",
        ],
    },
    "body_recomposition": {
        "goal_sentence": "You will slowly trade fat for muscle by training hard and eating around maintenance.",
        "science": [
            "Recomp is slower than a pure cut or bulk, but works well for newer or returning lifters.",
            "Protein quality and consistent progression matter more than scale changes.",
            "Expect visual and strength improvements before big weight shifts.",
        ],
    },
    "maintain_tone": {
        "goal_sentence": "You will improve shape and definition by adding muscle while holding body weight steady.",
        "science": [
            "Toning is muscle gain plus stable or slight fat reduction, not a special training style.",
            "Resistance training is non-negotiable if you want visible shape changes.",
            "Slight progression over time beats random high-sweat sessions.",
        ],
    },
    "athletic_performance": {
        "goal_sentence": "You will train for output and resilience with periodized strength and conditioning.",
        "science": [
            "Performance requires sequencing: base, build, peak, and recovery.",
            "Fuel timing and total energy intake directly impact output quality.",
            "Aerobic base plus strength creates durable, repeatable performance.",
        ],
    },
}


FOUNDATION_MODULES: List[Dict[str, Any]] = [
    {
        "id": "fitmax-1",
        "phase": "Foundation",
        "module_number": 1,
        "title": "Your Body, Your Baseline",
        "description": "Understand composition, TDEE, and what your body needs to change.",
        "steps": [
            {
                "title": "Body Composition 101",
                "content": "Your look comes from muscle mass + fat mass distribution, not scale weight alone.",
            },
            {
                "title": "Why Scale Weight Misleads",
                "content": "Water, glycogen, sodium, and digestion can swing daily scale numbers.",
            },
            {
                "title": "TDEE and Your Starting Point",
                "content": "We calculate your maintenance calories and set your target based on your goal.",
            },
        ],
    },
    {
        "id": "fitmax-2",
        "phase": "Foundation",
        "module_number": 2,
        "title": "The Science of Your Goal",
        "description": "Goal-specific physiology and realistic timelines.",
        "steps": [],
    },
    {
        "id": "fitmax-3",
        "phase": "Foundation",
        "module_number": 3,
        "title": "How Muscle Actually Grows",
        "description": "Mechanical tension, overload, recovery, and sleep in practical language.",
        "steps": [
            {
                "title": "Hypertrophy Drivers",
                "content": "Tension is the main signal. Damage and metabolic stress support adaptation.",
            },
            {
                "title": "Progressive Overload",
                "content": "Add reps, load, quality, or set volume over time. Tiny progress compounds.",
            },
            {
                "title": "Recovery Is Part of Training",
                "content": "Muscle grows between sessions. Sleep and stress control decide adaptation quality.",
            },
        ],
    },
    {
        "id": "fitmax-4",
        "phase": "Foundation",
        "module_number": 4,
        "title": "Your Training Split, Explained",
        "description": "Why your weekly split fits your days, goal, and equipment.",
        "steps": [],
    },
]


EXECUTION_MODULES: List[Dict[str, Any]] = [
    {
        "id": "fitmax-5",
        "phase": "Execution",
        "module_number": 5,
        "title": "Movement Mastery: The Big Patterns",
        "description": "Squat, hinge, push, pull, carry with regressions and progressions.",
        "steps": [
            {
                "title": "Squat Pattern",
                "content": "Build quads, glutes, and core control. Keep ribs down and knees tracking toes.",
            },
            {
                "title": "Hinge Pattern",
                "content": "Load posterior chain through hips. Keep spine neutral and push hips back.",
            },
            {
                "title": "Push / Pull / Carry",
                "content": "Balance shoulder mechanics, upper body symmetry, and trunk stability.",
            },
        ],
    },
    {
        "id": "fitmax-6",
        "phase": "Execution",
        "module_number": 6,
        "title": "Your Exercise Library",
        "description": "Searchable movement reference with swaps and cues.",
        "steps": [
            {
                "title": "How to Use the Library",
                "content": "Every plan exercise includes cues, effort signs, and alternatives.",
            },
            {
                "title": "Swap Logic",
                "content": "Choose swaps that preserve movement pattern and target muscles.",
            },
        ],
    },
    {
        "id": "fitmax-7",
        "phase": "Execution",
        "module_number": 7,
        "title": "Intensity Without Burnout",
        "description": "Use RPE/RIR, understand failure proximity, and schedule deloads.",
        "steps": [
            {
                "title": "RPE and RIR",
                "content": "Most working sets should land around RIR 1-3 for hypertrophy progress.",
            },
            {
                "title": "Deload Strategy",
                "content": "When performance stalls and fatigue rises, reduce volume for one week.",
            },
        ],
    },
    {
        "id": "fitmax-8",
        "phase": "Execution",
        "module_number": 8,
        "title": "Nutrition Architecture",
        "description": "Macro targets, meal timing, and practical templates.",
        "steps": [
            {
                "title": "Protein First",
                "content": "Hit your daily protein target every day before optimizing anything else.",
            },
            {
                "title": "Meal Timing",
                "content": "Pre-workout carbs + protein and post-workout protein improve performance and recovery.",
            },
            {
                "title": "Flexible Meal Structure",
                "content": "Use meal templates and substitutions instead of rigid meal plans.",
            },
        ],
    },
    {
        "id": "fitmax-9",
        "phase": "Execution",
        "module_number": 9,
        "title": "Cardio: When, Why, How Much",
        "description": "Goal-specific cardio strategy with realistic weekly dosing.",
        "steps": [
            {
                "title": "Cardio by Goal",
                "content": "Cut: deficit support. Bulk: health support. Performance: capacity development.",
            },
            {
                "title": "LISS vs HIIT",
                "content": "Use mostly LISS for consistency. Add HIIT sparingly when recovery allows.",
            },
        ],
    },
]


OPTIMIZATION_MODULES: List[Dict[str, Any]] = [
    {
        "id": "fitmax-10",
        "phase": "Optimization",
        "module_number": 10,
        "title": "Sleep, Recovery, Hormones",
        "description": "The leverage point most users underestimate.",
        "steps": [
            {
                "title": "Why Sleep Changes Results",
                "content": "Sleep quality affects hunger regulation, recovery hormones, and output.",
            },
            {
                "title": "Recovery Practices",
                "content": "Use walking, mobility, and stress control to keep quality sessions high.",
            },
        ],
    },
    {
        "id": "fitmax-11",
        "phase": "Optimization",
        "module_number": 11,
        "title": "Supplements: What Is Worth It",
        "description": "Evidence-based stack only.",
        "steps": [
            {"title": "Creatine", "content": "3-5g daily, consistent use, high impact per dollar."},
            {"title": "Protein Powder", "content": "Convenience tool when whole food protein is hard to hit."},
            {"title": "Caffeine / Vitamin D / Magnesium", "content": "Situational support when used intentionally."},
        ],
    },
    {
        "id": "fitmax-12",
        "phase": "Optimization",
        "module_number": 12,
        "title": "Posture, Aesthetics, Visual Edge",
        "description": "Looksmax-specific physique principles.",
        "steps": [
            {
                "title": "Visual Impact Muscles",
                "content": "Rear delts, lats, upper chest, glutes, and neck change silhouette fast.",
            },
            {
                "title": "Posture Corrections",
                "content": "Fix common issues with focused mobility + strength pairings.",
            },
        ],
    },
    {
        "id": "fitmax-13",
        "phase": "Optimization",
        "module_number": 13,
        "title": "Plateaus and Adjustments",
        "description": "4-week check-ins and decision trees for stalls.",
        "steps": [
            {
                "title": "Track What Matters",
                "content": "Use weekly scale trend, monthly measurements, photos, and strength markers.",
            },
            {
                "title": "Decision Tree",
                "content": "If progress stalls, adjust calories, volume, recovery, or adherence first.",
            },
        ],
    },
]


MASTERY_MODULES: List[Dict[str, Any]] = [
    {
        "id": "fitmax-14",
        "phase": "Identity",
        "module_number": 14,
        "title": "Building the Fitness Habit",
        "description": "Identity-based consistency and bounce-back systems.",
        "steps": [
            {
                "title": "Identity > Motivation",
                "content": "Operate as someone who trains, not someone waiting to feel inspired.",
            },
            {
                "title": "Missed Day Recovery Rule",
                "content": "Never miss twice. Next actionable step wins momentum back.",
            },
        ],
    },
    {
        "id": "fitmax-15",
        "phase": "Identity",
        "module_number": 15,
        "title": "Graduation and Next Cycle",
        "description": "Review outcomes, lock lessons, and commit to the next cycle.",
        "steps": [
            {
                "title": "Your Cycle Review",
                "content": "Summarize adherence, performance trend, and body composition trajectory.",
            },
            {
                "title": "What Is Next",
                "content": "Pick a specialization block and commit to one more full cycle.",
            },
        ],
    },
]


def _timeline_steps(goal_key: str) -> List[Dict[str, str]]:
    sentence = GOAL_BRANCH_CONTENT.get(goal_key, GOAL_BRANCH_CONTENT["maintain_tone"])["goal_sentence"]
    return [
        {"title": "Week 4", "content": "Consistency baseline set. Technique and routine feel stable."},
        {"title": "Week 8", "content": "Visible trend begins. Performance and adherence matter most now."},
        {"title": "Week 16", "content": "Compounding changes become obvious in measurements and mirror checks."},
        {"title": "Month 6", "content": "Body composition reflects identity-level habits and training maturity."},
        {"title": "Goal In One Sentence", "content": sentence},
    ]


def build_fitmax_course_modules(goal_key: str, split_summary: str, week_preview: str) -> List[Dict[str, Any]]:
    branch = GOAL_BRANCH_CONTENT.get(goal_key, GOAL_BRANCH_CONTENT["maintain_tone"])

    modules: List[Dict[str, Any]] = []
    modules.extend(FOUNDATION_MODULES)
    modules.extend(EXECUTION_MODULES)
    modules.extend(OPTIMIZATION_MODULES)
    modules.extend(MASTERY_MODULES)

    output: List[Dict[str, Any]] = []
    for module in modules:
        clone = {**module, "steps": [dict(s) for s in module.get("steps", [])]}
        if clone["id"] == "fitmax-2":
            clone["steps"] = [
                {"title": "Your Goal Science", "content": " ".join(branch["science"])},
                *_timeline_steps(goal_key),
            ]
        if clone["id"] == "fitmax-4":
            clone["steps"] = [
                {"title": "Why This Split", "content": split_summary},
                {"title": "Your First Week Preview", "content": week_preview},
            ]
        output.append(clone)
    return output

