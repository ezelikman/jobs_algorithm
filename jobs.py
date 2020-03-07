from ortools.graph import pywrapgraph
from jobs_config import *

from PyInquirer import prompt
import traceback
import time
import csv
import os
import timestring
import math

# Should be in the filename, at the beginning
survey_name = "Jobs"

def confirm(message, default=True):
    question = {
        'type': 'confirm',
        'name': 'result',
        'message': message,
        'default': default,
    }
    return prompt(question)['result']

def inq_input(message):
    question = {
        'type': 'input',
        'name': 'result',
        'message': message,
    }
    return prompt(question)['result']

def num_input(message):
    question = {
        'type': 'input',
        'name': 'result',
        'message': message,
        'validate': lambda s : s.isnumeric(),
    }
    return prompt(question)['result']

def list_select(message, options):
    question = {
        'type': 'list',
        'name': 'result',
        'message': message,
        'choices': options,
    }
    return prompt(question)['result']

# Given a list of filenames, find the one corresponding to the most recent data
def most_recent(jobs_files):
    # Extract date from filename
    def to_date(filename):
        if ".qsf" in filename:
            return timestring.Date("1 1 1970")
        try:
            date = filename[len(survey_name) + 1:-4].replace(".", ":").replace("_", " ")
            return timestring.Date(date)
        except:
            print("Failed to parse ", filename)
    job_file = max(jobs_files, key=to_date)
    print("Job file: ", job_file)
    return job_file

# Reduce all values in an array past a certain value by count
def reduce_past(array, pivot, count):
    # This is kind of hard because [1,2,2,2,5] - 2 -> [1,2]
    return [max(r - count, 1) if r > pivot else r for r in array]

# Extract all necessary information from the csv
def get_data(filename="jobs.csv"):
  humans = {}
  with open(filename, 'r', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for count, row in enumerate(reader):
        try:
            name = row["Q1"]
            human = {}
            # Get all weekly-related information
            def weeklies(human):
                # Broad weekly rankings
                weekly_base = []
                for col in row:
                    if weekly_jobs_col in col:
                        try:
                            weekly_base.append(int(row[col]))
                        except:
                            return False
                # What the general rankings are
                human["Weekly"] = weekly_base
                # Used to hold the per-slot rankings
                human["Weekly_Rankings"] = [False] * sum(weekly_counts)
                # Does the person have a biweekly? If TM, no
                human["Theme_Manager"] = [row[col] == "Yes" for col in row if TM_col in col][0]
                # Preference for same-day vs different-day biweekly
                human["SameDay"] = 0 if human["Theme_Manager"] else [int(row[col]) for col in row if sameday_col in col][0] - 6


                # Start with general ranks
                rank = 1
                buffer = 2  # Account for deleted jobs
                for ii in range(len(weekly_jobs) + buffer):
                    if ii + 1 in human["Weekly"]:
                        job = human["Weekly"].index(ii + 1)
                        human["Weekly_Rankings"][weekly_index[job][0]:weekly_index[job][1]] = [rank] * weekly_counts[job]
                        rank += weekly_counts[job]
                # Precise weekly preferences
                human["Weekly_Precise"] = [job for job in row[weekly_precise_col].split(",") if job in weekly_precise_names]


                # Add the specific job ranks
                # Should correspond to however many values are before the first precise rank
                # e.g. [1,1,1,1,1,1] -> [1,1,1,1,1,2] should be impossible
                rank = 1
                for job in human["Weekly_Precise"]:
                    if job in weekly_precise_names:
                        job_id = weekly_precise_names.index(job)
                        job_count = weekly_precise_counts[job_id]
                        job_indices = weekly_precise_index[job_id]
                        human["Weekly_Rankings"] = [r + job_count if r >= rank and r < rank + job_count else r for r in human["Weekly_Rankings"]]
                        human["Weekly_Rankings"][job_indices[0]:job_indices[1]] = [rank] * job_count
                        rank += weekly_precise_counts[job_id]

                # Remove all impossible jobs
                human["Weekly_Reject"] = [job for job in row[weekly_reject_col].split(",") if job in weekly_precise_names]
                for job in human["Weekly_Reject"]:
                    if job in weekly_precise_names:
                        job_id = weekly_precise_names.index(job)
                        rank = human["Weekly_Rankings"][weekly_precise_index[job_id][0]]
                        human["Weekly_Rankings"] = reduce_past(human["Weekly_Rankings"], rank, weekly_precise_counts[job_id])
                        human["Weekly_Rankings"][weekly_precise_index[job_id][0]:weekly_precise_index[job_id][1]] = [False] * weekly_precise_counts[job_id]

                # Account for jobs with special needs
                human["Lifter"] = [row[col] == "Yes" for col in row if lifter_col in col][0]
                if not human["Lifter"]:
                    job_id = weekly_precise_names.index("Brew Crew (Varies)")
                    rank = human["Weekly_Rankings"][weekly_precise_index[job_id][0]]
                    human["Weekly_Rankings"] = reduce_past(human["Weekly_Rankings"], rank, 1)
                    human["Weekly_Rankings"][weekly_precise_index[job_id][0]] = False

                # Ignore Sunday weeklies if same-day preference is very strong
                if human["SameDay"] >= 4:
                    for job in weekly_precise:
                        if "Su" in job[2]:
                            job_id = weekly_precise_names.index(job[0])
                            rank = human["Weekly_Rankings"][weekly_precise_index[job_id][0]]
                            human["Weekly_Rankings"] = reduce_past(human["Weekly_Rankings"], rank, weekly_precise_counts[job_id])
                            job_indices = weekly_precise_index[job_id]
                            human["Weekly_Rankings"][job_indices[0]:job_indices[1]] = [False] * weekly_precise_counts[job_id]
                return True

            def biweeklies(human):
                if not human["Theme_Manager"]:
                    human["Biweekly"] = [int(row[col]) for col in row if biweekly_col in col]
                    human["Biweekly_Rankings"] = [False] * sum(biweekly_counts)

                    rank = 1
                    buffer = 5  # Account for deleted jobs
                    for ii in range(len(biweekly_jobs) + buffer):
                        if ii + 1 in human["Biweekly"]:
                            job = human["Biweekly"].index(ii + 1)
                            human["Biweekly_Rankings"][biweekly_index[job][0]:biweekly_index[job][1]] = [rank] * biweekly_counts[job]
                            rank += biweekly_counts[job]

            if weeklies(human):
                biweeklies(human)
                humans[name + " (" + str(count) + ")"] = human
        except Exception as e:
            print(traceback.format_exc())
            pass
    return humans

def solve(jobs, names, costs, quadratic=True):
    if quadratic:
        costs = [[c ** 2 for c in b] for b in costs]
    rows = len(costs)
    cols = len(costs[0])
    assignment = pywrapgraph.LinearSumAssignment()
    for worker in range(rows):
        for task in range(cols):
            if costs[worker][task]:
                assignment.AddArcWithCost(worker, task, costs[worker][task])

    solve_status = assignment.Solve()
    if solve_status == assignment.OPTIMAL:
        assignments = []
        for ii in range(assignment.NumNodes()):
            assignments.append([
                names[ii],
                jobs[assignment.RightMate(ii)],
                assignment.AssignmentCost(ii)])
        if quadratic:
            total = 0
            for assigned in assignments:
                assigned[2] = math.sqrt(assigned[2])
                total += assigned[2]
            return total, assignments
        else:
            return assignment.OptimalCost(), assignments
    elif solve_status == assignment.INFEASIBLE:
        print('No assignment is possible.')
    elif solve_status == assignment.POSSIBLE_OVERFLOW:
        print('Some input costs are too large and may cause an integer overflow.')


def extra_jobs(job_names_list, job_costs_list, extra_count):
    real_jobs = len(job_costs_list)
    for ii in range(extra_count):
        job_names_list.append("Extra Job (" + str(ii + 1) + ")")
        fair = True
        if fair:
            extra_cost = [sum(job_costs_list[kk][jj] for kk in range(real_jobs))/real_jobs for jj, job in enumerate(job_costs_list[0])]
            extra_cost = [int((cost)) for cost in extra_cost]
        else:
            extra_cost = [1] * len(job_costs_list[0])
        job_costs_list.append(extra_cost)

# Updates biweekly costs in_place
def handle_biweekly_overlap(biweekly_costs, biweekly_names, idx, weekly_day, sameday):
    biweekly_days = [job[2] for job in biweekly_jobs]
    possible_overlap = None
    for day in weekly_day:
            if day in biweekly_days:
                    possible_overlap = day

    if possible_overlap is not None:
        for jj, job in enumerate(biweekly_jobs):
            if sameday > 0:
                    if possible_overlap in job[2]:
                                for kk in range(biweekly_index[jj][0],biweekly_index[jj][1]):
                                    biweekly_costs[idx][kk] += sameday ** 2
            if sameday < 0:
                        if possible_overlap not in job[2]:
                                for kk in range(biweekly_index[jj][0], biweekly_index[jj][1]):
                                        biweekly_costs[idx][kk] += sameday ** 2

def main(jobs_file, verbose=True, rerun=False):
    humans = get_data(jobs_file)

    weekly_names = list(humans.keys())
    biweekly_names = []
    for name, human in humans.items():
        if not human["Theme_Manager"]:
            biweekly_names.append(name)

    weekly_costs = [
        humans[name]["Weekly_Rankings"]
        for name in weekly_names
    ]

    if rerun:
        for idx, name in enumerate(weekly_names):
            prev_rank = num_input(f'What rank did {name} get?')
            weekly_costs[idx] = [
                (weekly_cost + int(prev_rank) if weekly_cost != False else weekly_cost)
                for weekly_cost in weekly_costs[idx]
            ]

    extra_jobs(weekly_names, weekly_costs, len(weekly_all) - len(weekly_names))
    if verbose:
        print("Computing weeklies")
    weekly_cost, weekly_assignments = solve(weekly_all, weekly_names, weekly_costs)

    biweekly_costs = [humans[name]["Biweekly_Rankings"] for name in biweekly_names]
    for idx, name in enumerate(biweekly_names):
        assignment_idx = weekly_names.index(name)
        weekly = weekly_assignments[assignment_idx]
        weekly_rank = weekly[2]
        biweekly_costs[idx] = [
            int(cost + weekly_rank * idx / len(weekly_all))
            for idx, cost in enumerate(biweekly_costs[idx])]
        sameday = humans[name]["SameDay"]

        if sameday != 0:
            weekly_day = weekly_precise[weekly_precise_names.index(weekly[1])][2]
            handle_biweekly_overlap(biweekly_costs, name, idx, weekly_day, sameday)

    extra_jobs(biweekly_names, biweekly_costs, len(biweekly_all) - len(biweekly_costs))
    if verbose:
        print("Computing biweeklies")
    biweekly_cost, biweekly_assignments = solve(biweekly_all, biweekly_names, biweekly_costs)
    for biweekly_assignment in biweekly_assignments:
        if biweekly_assignment[0] in humans:
            biweekly_assignment[2] = humans[biweekly_assignment[0]]["Biweekly_Rankings"][biweekly_all.index(biweekly_assignment[1])]

    if verbose:
        print("Average ranks: %s / %s and %s / %s" % (
                round(weekly_cost / len(weekly_names), 1), len(weekly_names),
                round(biweekly_cost / len(biweekly_names), 1), len(biweekly_names)))
        for ii, (name, weekly_job, weekly_rank) in enumerate(weekly_assignments):
            if name in biweekly_names:
                _, biweekly_job, biweekly_rank = biweekly_assignments[biweekly_names.index(name)]
                print('%s assigned to %s and %s.  Ranks = %d and %d' % (
                    name, weekly_job, biweekly_job,
                    weekly_rank, biweekly_rank))
            else:
                print('%s (Theme Manager) assigned to %s.  Rank = %d' % (
                    name, weekly_job, weekly_rank))
    return {
        "weekly": [weekly_assignments, weekly_costs],
        "biweekly": [biweekly_assignments, biweekly_costs]
    }

def subnames(test_name, all_names):
    subname_list = []
    for cur_name in all_names:
        if test_name.lower() in cur_name.lower():
            subname_list.append(cur_name)
    return subname_list

def find_swap(weekly, biweekly):
    is_weekly_swap = confirm("A weekly? ", default=True)
    if is_weekly_swap:
        target_assignment_list, target_costs_list = weekly
        target_all = weekly_all
    else:
        target_assignment_list, target_costs_list = biweekly
        target_all = biweekly_all

    all_names = [name for name, job, rank in target_assignment_list]
    matches = []
    while len(matches) == 0:
        matches = subnames(inq_input("Who needs a swap? "), all_names)
        if len(matches) == 0:
            print("Nobody found with this name")

    if len(matches) > 1:
        target_in = list_select(
            "Multiple matches: Which person did you mean: ",
            sorted(matches))
    else:
        target_in = matches[0]

    target_idx = all_names.index(target_in)
    target_job = target_assignment_list[target_idx][1]

    print(f"Finding a swap for {target_in}'s {target_job}")
    top_n = 20
    print(f"--- Showing top {top_n}")
    possible_list = []
    for (cur_name, assigned_job, rank), cur_costs in zip(target_assignment_list, target_costs_list):
        if assigned_job == target_job:
            continue
        possible_list.append([cur_costs[target_idx] - rank, cur_name, assigned_job])
    for improvement, cur_name, assigned_job in sorted(possible_list)[:top_n]:
        print(f"{cur_name} has {assigned_job} ({int(improvement)})")


if __name__ == "__main__":
    rerun = confirm("Have you run the algorithm before?", default=True)
    matching_files = [f for f in [files for root, dirs, files in os.walk(".")][0] if survey_name in f]
    start_time = time.clock()
    jobs_file = list_select("Which file is the survey results?", matching_files)
    results = main(jobs_file, rerun=rerun)
    print()
    print("Time =", int((time.clock() - start_time) * 1E3), "ms")
    if confirm("Does someone need a swap?", default=False):
        find_swap(**results)
