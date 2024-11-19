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
                    if clause.strip():  
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

def truth_table(kb, query):
    symbols = set(query)
    for clause in kb:
        antecedent, consequent = parse_clause(clause)
        symbols.update(antecedent + [consequent])
    symbols = list(symbols)

    models_count = 0
    for assignment in generate_truth_assignments(symbols):
        if all(evaluate_clause(clause, assignment) for clause in kb):  
            models_count += 1
            if not assignment[query]: 
                return "NO"
    return f"YES: {models_count}"

#--------------------------------------------------------------------------------------------------------------------- hminhpartaye

class Chaining:
    def __init__(self, kb, query): 
        self.kb = kb
        self.query = query

    def FindSingleClause(self):
        self.queue = []
        for clause in self.kb:
            if '=>' not in clause and clause.strip():
                self.queue.append(clause)
        return self.queue

    def GenerateSentenceList(self):
        self.sentence_list = []
        for clause in self.kb:
            if '=>' in clause:
                premise, conclusion = clause.split('=>')
                premise_symbols = [symbol.strip() for symbol in premise.split('&')]
                conclusion = conclusion.strip()
                sentence = {
                    'premise': premise_symbols,
                    'conclusion': conclusion,
                    'count': len(premise_symbols)
                }
                self.sentence_list.append(sentence)
        return self.sentence_list

class FC(Chaining):
    def __init__(self, kb, query):  
        super().__init__(kb, query)
        self.queue = []
        self.sentence_list = []
        self.inferred = []

    def CheckEntails(self):
        self.FindSingleClause()
        self.GenerateSentenceList()
        
        while self.queue:
            current_symbol = self.queue.pop(0)
            self.inferred.append(current_symbol)
            
            for sentence in self.sentence_list:
                if current_symbol in sentence['premise']:
                    sentence['count'] -= 1
                    if sentence['count'] == 0:
                        self.queue.append(sentence['conclusion'])
        
            if self.query in self.inferred:
                print('YES:', ', '.join(self.inferred))
                return True
        
        print('NO')
        return False

class BC(Chaining):
    def __init__(self, kb, query):  
        super().__init__(kb, query)
        self.queue = []
        self.sentence_list = []
        self.inferred = []
        self.visited = set()

    def CheckEntails(self):
        self.FindSingleClause()
        self.GenerateSentenceList()
        
        if self.TruthValue(self.query):
            print('YES:', ', '.join(self.inferred))
            return True
        else:
            print('NO')
            return False

    def TruthValue(self, symbol):
        if symbol in self.inferred:
            return True
        
        if symbol in self.queue:
            self.inferred.append(symbol)
            return True
        
        if symbol in self.visited:
            return False

        self.visited.add(symbol)

        for sentence in self.sentence_list:
            if symbol == sentence['conclusion']:
                all_premises_true = all(self.TruthValue(premise) for premise in sentence['premise'])
                if all_premises_true and symbol not in self.inferred:
                    self.queue.append(symbol)
                    self.inferred.append(symbol)
                    return True

        return False
    

class DPLL:
    def __init__(self, kb, query):
            self.kb = kb
            self.query = query
    def CheckEntails(self):
        result, model_count = self.dpll(self.kb, {})
        if result:
            print(f'YES: {model_count}')
        else:
            print('NO')

    def convert_to_clauses(self, kb):
        return [self.parse_clause(clause) for clause in kb]

    def parse_clause(self, clause):
        return [literal.strip() for literal in clause.split('|')]

    def dpll(self, clauses, assignment):
        if self.all_clauses_satisfied(clauses, assignment):
            return True, 1
        if self.any_clause_falsified(clauses, assignment):
            return False, 0

        unit_clauses = self.find_unit_clauses(clauses)
        if unit_clauses:
            unit = unit_clauses[0][0]
            return self.dpll(self.simplify_clauses(clauses, unit), {**assignment, unit: True})

        pure_literals = self.find_pure_literals(clauses)
        if pure_literals:
            pure_literal = next(iter(pure_literals))
            return self.dpll(self.simplify_clauses(clauses, pure_literal), {**assignment, pure_literal: True})

        literal = self.select_literal(clauses)
        result_true, count_true = self.dpll(self.simplify_clauses(clauses, literal), {**assignment, literal: True})
        result_false, count_false = self.dpll(self.simplify_clauses(clauses, f'-{literal}'), {**assignment, literal: False})
        return (result_true or result_false), (count_true + count_false)

    def simplify_clauses(self, clauses, literal):
        simplified = []
        for clause in clauses:
            if literal not in clause:
                filtered_clause = [lit for lit in clause if lit != f'-{literal}' and lit != literal[1:]]
                simplified.append(filtered_clause)
        return simplified

    def evaluate_clause(self, clause, assignment):
        for literal in clause:
            if assignment.get(literal) is True:
                return True
            if assignment.get(f'-{literal}') is False:
                return True
        return None

    def all_clauses_satisfied(self, clauses, assignment):
        return all(self.evaluate_clause(clause, assignment) for clause in clauses)

    def any_clause_falsified(self, clauses, assignment):
        return any(self.evaluate_clause(clause, assignment) is False for clause in clauses)

    def find_unit_clauses(self, clauses):
        return [clause for clause in clauses if len(clause) == 1]

    def find_pure_literals(self, clauses):
        literals = {literal for clause in clauses for literal in clause}
        return {literal for literal in literals if f'-{literal}' not in literals and literal[1:] not in literals}

    def select_literal(self, clauses):
        for clause in clauses:
            for literal in clause:
                return literal





class Main:            
    filename = sys.argv[1]
    method = sys.argv[2]
    
    print(sys.argv[1], sys.argv[2])
    
    kb, query = parse_file(filename)
    
    print('This is the KB:', kb)
    print('This is the QUERY:', query)

    # Choose the appropriate inference method based on input
    if method.lower() == 'fc':
        algorithm = FC(kb, query) 
        algorithm.CheckEntails()                         
    elif method.lower() == 'bc':
        algorithm = BC(kb, query)
        algorithm.CheckEntails()           
    elif method.lower() == 'tt':
        result = truth_table(kb, query)
        print(result)
    elif method.lower() == 'dpll':
        algorithm = DPLL(kb, query)
    else:
        print('Error: Wrong search method input. Please check the command.')
        sys.exit()
            
       
    sys.exit()


'''
def main():
    filename = sys.argv[1]
    method = sys.argv[2]
    

    kb, query = parse_file(filename)

    if method.lower() == 'tt':
        result = truth_table(kb, query)
        print(result)
    elif method.lower() == 'bc':
        bc_engine = BC(kb, query)
        bc_engine.CheckEntails()
    elif method.lower() == 'fc':
        algorithm = FC(kb, query)
        algorithm.CheckEntails()
    else:
        print('Error: Wrong search method input. Please check the command.')
        return
    
    

if __name__ == "__main__":
    main()
'''