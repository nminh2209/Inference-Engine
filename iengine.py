import sys
import os
from itertools import product

def parse_file(filename):
    kb = []
    query = None

    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith("TELL"):
                mode = 'TELL'
            elif line.startswith("ASK"):
                mode = 'ASK'
            elif mode == 'TELL':  
                clauses = line.split(";")  
                for clause in clauses:
                    kb.append(clause.strip())  
            elif mode == 'ASK' and line: 
                query = line.strip()
    return kb, query

def parse_clause(clause):
    if "=>" in clause:
        antecedent, consequent = clause.split("=>")
        antecedent = antecedent.strip().split("&")
        consequent = consequent.strip()
        return antecedent, consequent
    else:
        return [], clause.strip()

def generate_truth_assignments(symbols):
    return [dict(zip(symbols, values)) for values in product([True, False], repeat=len(symbols))]

def evaluate_clause(clause, assignment):
    antecedent, consequent = parse_clause(clause)
    if antecedent: 
        return all(assignment[symbol] for symbol in antecedent) <= assignment[consequent]
    else:  
        return assignment[consequent]
