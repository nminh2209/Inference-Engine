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


#--------------------------------------------------------------------------------------------------------------------- hminhpartaye

class Chaining:
    def __init__(self, kb, query): 
        self.kb = kb
        self.query = query

    def FindSingleClause(self):
        self.queue = []
        for clause in self.kb:
            if '=>' not in clause:
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


import sys

class Main:            
    filename = sys.argv[1]
    method = sys.argv[2]
    
    print(sys.argv[1], sys.argv[2])
    
    result = abcxyzgc.read_file(filename)
    kb = result[0]
    query = result[1]
    print('This is the KB:', kb)
    print('This is the QUERY:', query)

    # Choose the appropriate inference method based on input
    if method.lower() == 'fc':
        algorithm = FC(kb, query)                         
    elif method.lower() == 'bc':
        algorithm = BC(kb, query)            
    elif method.lower() == 'tt':
        algorithm = TT(kb, query)

    else:
        print('Error: Wrong search method input. Please check the command.')
        sys.exit()
            
    algorithm.CheckEntails()    
    sys.exit()

