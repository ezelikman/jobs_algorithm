survey_name = "Jobs"
quadratic_cost = True

# Name, count, day
weekly_precise = [
    ("Job A (M/W)", 1, ["M", "W"]),
    ("Job A (T/T)", 1, ["Tu", "Th"]),
    ("Job B (M)", 2, ["M"]),
    ("Job B (Tu)", 2, ["Tu"]),
    ("Job B (W)", 2, ["W"]),
    ("Job B (Th)", 2, ["Th"]),
    ("Job B (Su)", 2, ["Su"]),
    ("Job C (M)", 3, ["M"]),
    ("Job C (Tu)", 3, ["Tu"]),
    ("Job C (W)", 3, ["W"]),
    ("Job C (Th)", 3, ["Th"]),
    ("Job C (Su)", 3, ["Su"]),
    ("Job D (F)", 1, ["F"]),
    ("Job D (Sa)", 1, ["Sa"]),
    ("Job E (M)", 2, ["M"]),
    ("Job E (Th)", 2, ["Th"]),
    ("Job F (M)", 1, ["M"]),
    ("Job F (Tu)", 1, ["Tu"]),
    ("Job F (W)", 1, ["W"]),
    ("Job F (Th)", 1, ["Th"]),
    ("Job G (Tu)", 2, ["Tu"]),
    ("Job G (Th)", 2, ["Th"]),
    ("Job H (Varies)", 2, ["Sa", "Su"]),
]
weekly_precise_names = [name for name, count, day in weekly_precise]
weekly_precise_col = "Q3_0_GROUP"
weekly_reject_col = "Q3_1_GROUP"
weekly_precise_counts = [job[1] for job in weekly_precise]
weekly_precise_index = [(sum(weekly_precise_counts[:i]), sum(weekly_precise_counts[:i+1]))
                for i, job in enumerate(weekly_precise_counts)]
weekly_all = sum(([name] * count for name, count, day in weekly_precise), [])

weekly_jobs = [
    "Job A",
    "Job B",
    "Job C",
    "Job D",
    "Job E",
    "Job F",
    "Job G",
    "Job H"
]
weekly_counts = [sum([count for name, count, days in weekly_precise if job in name]) for job in weekly_jobs]
weekly_index = [(sum(weekly_counts[:i]), sum(weekly_counts[:i+1])) for i, job in enumerate(weekly_counts)]
weekly_jobs_col = "Q2"

# Name, count, day, weekly overlaps
biweekly_jobs = [
    ("Job I (Crew 1)", 4, ["Su"], []),
    ("Job I (Crew 2)", 4, ["Su"], []),
    ("Job J (Crew 1)", 4, ["Su"], []),
    ("Job J (Crew 2)", 4, ["Su"], []),
    ("Job K (Crew 1)", 2, ["Su"], []),
    ("Job K (Crew 2)", 2, ["Su"], []),
    ("Job L (Crew 1)", 3, ["Su"], ["Job B (Su)"]),
    ("Job L (Crew 2)", 3, ["Su"], ["Job B (Su)"]),
    ("Job M (Crew 1)", 3, ["W"], ["Job B (W)"]),
    ("Job M (Crew 2)", 3, ["W"], ["Job B (W)"]),
    ("Job N Crew 1", 2, ["Su"], []),
    ("Job O Crew 2", 2, ["Su"], []),
]
biweekly_col = "Q6"
biweekly_names = [name for name, count, day, overlaps in biweekly_jobs]
biweekly_counts = [job[1] for job in biweekly_jobs]
biweekly_index = [(sum(biweekly_counts[:i]), sum(biweekly_counts[:i+1]))
                for i, job in enumerate(biweekly_counts)]
biweekly_all = sum(([name] * count for name, count, day, overlaps in biweekly_jobs), [])

sameday_col = "Q11"
lifter_col = "Q12"
TM_col = "Q7"
