# utils/level.py

# Level thresholds in total seconds
LEVEL_THRESHOLDS = [
    300,        # Level 1: 5 min
    900,        # Level 2: 15 min
    1800,       # Level 3: 30 min
    3600,       # Level 4: 1 hr
    7200,       # Level 5: 2 hr
    18000,      # Level 6: 5 hr
    36000,      # Level 7: 10 hr
    72000,      # Level 8: 20 hr
    180000,     # Level 9: 50 hr
    360000      # Level 10: 100 hr
]

def calculate_level(total_seconds):
    for i in reversed(range(len(LEVEL_THRESHOLDS))):
        if total_seconds >= LEVEL_THRESHOLDS[i]:
            return i + 1
    return 0
