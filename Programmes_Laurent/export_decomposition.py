import subprocess
import csv
import re
import numpy as np
import itertools
from functools import reduce


LP_FILES = [
    "decomp-pluripotent-14-05-2023.lp",
    "Fonctions-bool-Cont-cloture-11-12-2023.lp",
    "SBF-cpath-constraints-12-06-2024.lp",
    "setup_decomp.lp",
]

N = 0

MAX_DIMENSION = 4

# PREDICATES = ["weight","funct"]

def parse_func(line):
    """Parse a line of predicates 'func' """
    func_row = {}
    tokens = line.split()
    for token in tokens:
        asp_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\(([0-9]*)\,([0-9]*)\)', token)

        name = asp_match.group(1)
        arg = asp_match.group(2)
        value = asp_match.group(3)
        func_row[f"f_{arg}"] = value
    return func_row

def parse_weight(line):
    """Parse a line of CP predicates 'weight' """
    weight_row = {}
    tokens = line.split()

    for token in tokens:
        csp_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\(([0-9]*)\,([0-9]*)\)?=(-?\d+)', token)

        name = csp_match.group(1)
        arg = csp_match.group(2),csp_match.group(3)
        value = csp_match.group(4)
        weight_row[f"w_{arg[0]},{arg[1]}"] = value
  
    return weight_row

def solve_and_export(lp_files, constant, max_answer_n = 0,output_csv="output.csv"):
    result = subprocess.run(
        ["clingcon", f"{max_answer_n}","--project","--parallel","8"] + constant + lp_files,
        capture_output=True, text=True
    )


    all_rows = []
    answer_number = 0
    result_iterator = iter(result.stdout.splitlines())


    while (line := next(result_iterator, None)) is not None and not line.startswith(("SATISFIABLE","UNSATISFIABLE","UNKNOWN")):
        line = line.strip()
        print(line)
        if line.startswith("Answer:"):
            answer_number += 1
            line = next(result_iterator, None)
            func_row = parse_func(line)
            line = next(result_iterator, None)
            line = next(result_iterator, None)
            weight_row = parse_weight(line)
            row = func_row | weight_row
            all_rows.append(row)

    if not all_rows:
        print("No results found.")
        return



    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_rows[0].keys(), restval="")
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Finished successfully ({answer_number} rows written in {output_csv})")


def complete_decomp_vect_generator(d):
    """return a generator of all the possible decomposition vector in dimension d"""
    if d == 1:
        return [[2]] 
    else :
        return [[i] + list((2-i)*np.array(v)) for i,v in itertools.product(range(3),complete_decomp_vect_generator(d-1))]


def rec_decomp_binary_vector_sum(d,s):
    """"""
    if d == 1 :
        return [[s]]
    else :
        return reduce(lambda l1,l2:l1+l2,([[i] + v for v in rec_decomp_binary_vector_sum(d-1,(s-i) // 2)] for i in range(s+1) if (s-i) % 2 == 0))


if __name__ == "__main__":
    for d in range(1,MAX_DIMENSION):
        for v in complete_decomp_vect_generator(d):
            constant = [f"-c v{i}={v[i]}" for i in range(d)]
            print(constant)
            # solve_and_export(LP_FILES, constant,N, output_csv=f"{d}d_<>_output.csv")
