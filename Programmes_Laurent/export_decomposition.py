import subprocess
import csv


LP_FILES = [
    "decomp-pluripotent-14-05-2023.lp",
    "Fonctions-bool-Cont-cloture-11-12-2023.lp",
    "SBF-cpath-constraints-12-06-2024.lp",
    "Test-decomp-pluripotent-14-05-2024.lp",
]

PREDICATES = ["weight","funct"]


def parse_output(output):
    rows_by_predicate = {p: [] for p in PREDICATES}
    for line in output.splitlines():
        line = line.strip()
        if not line or line in ("SATISFIABLE", "UNSATISFIABLE", "OPTIMUM FOUND"):
            continue
        # Each atom on the line separated by spaces
        for atom in line.split():
            name = atom.split("(")[0]
            if name in rows_by_predicate:
                args_str = atom[len(name)+1:-1] if "(" in atom else ""
                args = args_str.split(",") if args_str else []
                rows_by_predicate[name].append(args)
    return rows_by_predicate

result = subprocess.run(
    ["clingcon", "0"] + ["test.lp"],
    capture_output=True, text=True
)

rows_by_predicate = parse_output(result.stdout)

for predicate, rows in rows_by_predicate.items():
    if not rows:
        print(f"No results for '{predicate}', skipping.")
        continue
    with open(f"output_{predicate}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([f"arg{i+1}" for i in range(len(rows[0]))])
        writer.writerows(rows)
    print(f"Exported {len(rows)} rows → output_{predicate}.csv")