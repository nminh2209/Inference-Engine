import sys
import os
from itertools import product
from tabulate import tabulate
import re

class TextFileAnalyzer:
    def __init__(self, filename):
        self.filename = filename

    def read_file(filename):
        if len(sys.argv) != 3:
            print('Error: You need to use the following format "python iengine.py <filename> <method>".')
            sys.exit()

        if not os.path.exists(filename):
            print('Error: The map file does not exist. Please check the file path.')
            sys.exit()

        with open(filename, 'r') as file:
            content = file.read()

        tell_index = content.find('TELL')
        ask_index = content.find('ASK')

        if tell_index == -1 or ask_index == -1:
            print('Error: The file content is not formatted correctly. Please check the file content.')
            sys.exit()

        kb_content = content[tell_index + 4:ask_index].strip()
        query = content[ask_index + 3:].strip()

        if not kb_content or not query:
            print('Error: The file content is not formatted correctly. Please check the file content.')
            sys.exit()

        kb = [clause.strip() for clause in kb_content.split(';') if clause.strip()]

        if sys.argv[2].lower() not in ["tt", "dpll"]:
            additional_connectives = ['<=>', '||', '~']
            symbol_set = set()
            for clause in kb:
                for connective in additional_connectives:
                    if connective in clause:
                        symbol_set.add(connective)

            if symbol_set:
                print('Error: Only TT/DPLL method can read generic KB with additional connectives:', ', '.join(symbol_set))
                sys.exit()

        return kb, query

class TT:
    def __init__(self, kb, query):
        self.model_list = []
        self.kb = kb
        self.query = query

    def ExtractSymbols(self, kb):
        pattern = r'[a-zA-Z]+\d*'
        symbol_set = set()
        for clause in kb:
            symbols = re.findall(pattern, clause)
            symbol_set.update(symbols)
        return list(symbol_set)

    def CheckEntails(self):
        valid_model_count = self.CreateTruthTable()
        if valid_model_count:
            print('YES:', valid_model_count)
        else:
            print('NO')

    def CreateTruthTable(self):
        symbols = self.ExtractSymbols(self.kb)
        models = list(product([True, False], repeat=len(symbols)))

        data = []
        headers = symbols + self.kb + [self.query]
        valid_model_count = 0

        for model_values in models:
            model = dict(zip(symbols, model_values))
            row = [model[symbol] for symbol in symbols]
            kb_values = [self.Check_if_clause_true(clause, model) for clause in self.kb]
            row.extend(kb_values)
            query_value = self.Check_if_clause_true(self.query, model)
            row.append(query_value)

            if all(kb_values) and query_value:
                valid_model_count += 1
                green = '\033[92m'
                end = '\033[0m'
                colored_row = [f"{green}{str(cell)}{end}" for cell in row]
            else:
                colored_row = [f"{str(cell)}" for cell in row]

            data.append(colored_row)

        print(tabulate(data, headers=headers, tablefmt="fancy_grid"))
        return valid_model_count

    def Check_if_kb_true(self, model):
        for clause in self.kb:
            if not self.Check_if_clause_true(clause, model):
                return False
        return True

    def Check_if_clause_true(self, clause, model):
        clause = clause.replace(" ", "")
        return self.EvaluateClause(clause, model)

    def EvaluateClause(self, clause, model):
        left, op, right = self.FindMainOperator(clause)
        if op == '<=>':
            return self.EvaluateClause(left, model) == self.EvaluateClause(right, model)
        elif op == '=>':
            return not self.EvaluateClause(left, model) or self.EvaluateClause(right, model)
        elif op == '||':
            return self.EvaluateClause(left, model) or self.EvaluateClause(right, model)
        elif op == '&':
            return self.EvaluateClause(left, model) and self.EvaluateClause(right, model)
        elif clause.startswith('~'):
            return not self.EvaluateClause(clause[1:], model)
        else:
            return model.get(clause.strip(), False)

    def FindMainOperator(self, clause):
        bracket_level = 0
        result = None

        for i in range(len(clause)):
            if clause[i] == '(':
                bracket_level += 1
            elif clause[i] == ')':
                bracket_level -= 1
            elif bracket_level == 0:
                if clause[i:i + 3] == '<=>':
                    result = clause[:i], '<=>', clause[i + 3:]
                    break
                elif clause[i:i + 2] == '=>':
                    result = clause[:i], '=>', clause[i + 2:]
                    break
                elif clause[i:i + 2] == '||':
                    result = clause[:i], '||', clause[i + 2:]
                    break
                elif clause[i] == '&':
                    result = clause[:i], '&', clause[i + 1:]
                    break

        if result:
            left, op, right = result
            if left[0] == '(' and left[-1] == ')':
                left = left[1:-1]
            if right[0] == '(' and right[-1] == ')':
                right = right[1:-1]
            return left, op, right
        else:
            return clause, None, None


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
        
        result = TextFileAnalyzer.read_file(filename)
        kb = result[0]
        query = result[1]
        print ('This is the KB: ',kb)
        print ('This is the QUERY: ',query)

        #Choose the appropriate method based on the input
        if method.lower() == 'fc':
            algorithm = FC(kb, query)                         
        elif method.lower() == 'bc':
            algorithm = BC(kb, query)            
        elif method.lower() == 'tt':
            algorithm = TT(kb, query)
        elif method.lower() == 'dpll':
            algorithm = DPLL(kb, query)
        else:
            #Handle incorrect method input
            print('-----------------------------------------------------------------------------------------------------------------------\n')
            print('Error: Wrong search method input. Please check the command. \n')
            print('-----------------------------------------------------------------------------------------------------------------------')
            sys.exit()  #Exit the program if the method input is incorrect
            
        algorithm.CheckEntails()    
        sys.exit()
''''
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


''''''
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