import subprocess
import csv
import re


LP_FILES = [
    "decomp-pluripotent-14-05-2023.lp",
    "Fonctions-bool-Cont-cloture-11-12-2023.lp",
    "SBF-cpath-constraints-12-06-2024.lp",
    "Test-decomp-pluripotent-14-05-2024.lp",
]

PREDICATES = ["weight","funct"]


def parse_answer_set(line, predicates):
    """Parse one answer set line into a dict of {predicate_instance: value}"""
    row = {}
    tokens = line.strip().split()

    for token in tokens:
        # CSP format: predicate(a,b)=value  e.g. cost(task1,worker2)=5
        csp_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)(\([^)]*\))?=(-?\d+)', token)
        # Regular ASP atom: predicate(a,b)
        asp_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)(\([^)]*\))?$', token)

        if csp_match:
            name = csp_match.group(1)
            args = csp_match.group(2) or ""
            value = csp_match.group(3)
            if name in predicates:
                col = f"{name}{args}"   # e.g. "cost(task1,worker2)"
                row[col] = value

        elif asp_match:
            name = asp_match.group(1)
            args = asp_match.group(2) or ""
            if name in predicates:
                col = f"{name}{args}"   # e.g. "assign(task1,worker2)"
                row[col] = "true"       # boolean atom — just mark as present

    return row

def solve_and_export(lp_files, predicates, output_csv="output.csv"):
    result = subprocess.run(
        ["clingcon", "4"] + lp_files,
        capture_output=True, text=True
    )

    all_rows = []
    answer_number = 0

    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("Answer:"):
            answer_number += 1
        elif answer_number > 0 and line and not line.startswith(("SATISFIABLE", "UNSATISFIABLE", "OPTIMUM", "Models", "Calls", "Time", "CPU")):
            row = parse_answer_set(line, predicates)
            if row:
                row["answer_set"] = answer_number
                all_rows.append(row)
                answer_number = 0  # reset until next "Answer:" line

    if not all_rows:
        print("No results found. Check your #show directives and predicate names.")
        return

    # Build unified column list across all rows
    all_cols = ["answer_set"]
    seen = set(all_cols)
    for row in all_rows:
        for col in row:
            if col not in seen:
                all_cols.append(col)
                seen.add(col)

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_cols, restval="")
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Exported {len(all_rows)} answer sets to {output_csv}")

solve_and_export(LP_FILES, PREDICATES, output_csv="output.csv")