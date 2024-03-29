from collections import deque
import util
import functools

"""
    Base class for unary constraints
    Implement isSatisfied in subclass to use
"""


class UnaryConstraint:
    def __init__(self, var):
        self.var = var

    def isSatisfied(self, value):
        util.raiseNotDefined()

    def affects(self, var):
        return var == self.var


"""
    Implementation of UnaryConstraint
    Satisfied if value does not match passed in paramater
"""


class BadValueConstraint(UnaryConstraint):
    def __init__(self, var, badValue):
        self.var = var
        self.badValue = badValue

    def isSatisfied(self, value):
        return not value == self.badValue

    def __repr__(self):
        return 'BadValueConstraint (%s) {badValue: %s}' % (
            str(self.var), str(self.badValue))


"""
    Implementation of UnaryConstraint
    Satisfied if value matches passed in paramater
"""


class GoodValueConstraint(UnaryConstraint):
    def __init__(self, var, goodValue):
        self.var = var
        self.goodValue = goodValue

    def isSatisfied(self, value):
        return value == self.goodValue

    def __repr__(self):
        return 'GoodValueConstraint (%s) {goodValue: %s}' % (
            str(self.var), str(self.goodValue))


"""
    Base class for binary constraints
    Implement isSatisfied in subclass to use
"""


class BinaryConstraint:
    def __init__(self, var1, var2):
        self.var1 = var1
        self.var2 = var2

    def isSatisfied(self, value1, value2):
        util.raiseNotDefined()

    def affects(self, var):
        return var == self.var1 or var == self.var2

    def otherVariable(self, var):
        if var == self.var1:
            return self.var2
        return self.var1


"""
    Implementation of BinaryConstraint
    Satisfied if both values assigned are different
"""


class NotEqualConstraint(BinaryConstraint):
    def isSatisfied(self, value1, value2):
        if value1 == value2:
            return False
        return True

    def __repr__(self):
        return 'NotEqualConstraint (%s, %s)' % (str(self.var1), str(self.var2))


class ConstraintSatisfactionProblem:
    """
    Structure of a constraint satisfaction problem.
    Variables and domains should be lists of equal length that have the same order.
    varDomains is a dictionary mapping variables to possible domains.

    A
        variables (list<string>): a list of variable names
        domains (list<set<value>>): a list of sets of domains for each variable
        binaryConstraints (list<BinaryConstraint>): a list of binary constraints to satisfy
        unaryConstraints (list<BinaryConstraint>): a list of unary constraints to satisfy
    """

    def __init__(self, variables, domains, binaryConstraints=[],
                 unaryConstraints=[]):
        """

        :param list[str] variables:
        :param list[set] domains:
        :param list[BinaryConstraint] binaryConstraints:
        :param list[BinaryConstraint] unaryConstraints:
        """
        self.varDomains = {}
        for i in xrange(len(variables)):
            self.varDomains[variables[i]] = domains[i]
        self.binaryConstraints = binaryConstraints
        self.unaryConstraints = unaryConstraints

    def __repr__(self):
        return '---Variable Domains\n%s---Binary Constraints\n%s---Unary Constraints\n%s' % ( \
            ''.join([str(e) + ':' + str(self.varDomains[e]) + '\n' for e in
                     self.varDomains]), \
            ''.join([str(e) + '\n' for e in self.binaryConstraints]), \
            ''.join([str(e) + '\n' for e in self.binaryConstraints]))

    def concerned_constraints(self, var):
        return [constraint
                for constraint in self.binaryConstraints
                if constraint.affects(var)]

    def number_of_concerned_constraints(self, var):
        return len(self.concerned_constraints(var))


class Assignment:
    """
    Representation of a partial assignment.
    Has the same varDomains dictionary stucture as ConstraintSatisfactionProblem.
    Keeps a second dictionary from variables to assigned values, with None being no assignment.

    Args:
        csp (ConstraintSatisfactionProblem): the problem definition for this assignment
    """

    def __init__(self, csp):
        """

        :param ConstraintSatisfactionProblem csp:
        """
        self.varDomains = {}
        for var in csp.varDomains:
            self.varDomains[var] = set(csp.varDomains[var])
        self.assignedValues = {var: None for var in self.varDomains}

    """
    Determines whether this variable has been assigned.

    Args:
        var (string): the variable to be checked if assigned
    Returns:
        boolean
        True if var is assigned, False otherwise
    """

    def isAssigned(self, var):
        """
        :param str var:
        :rtype: bool
        """
        return self.assignedValues[var] is not None

    """
    Determines whether this problem has all variables assigned.

    Returns:
        boolean
        True if assignment is complete, False otherwise
    """

    def isComplete(self):
        """
        :rtype: bool
        """
        for var in self.assignedValues:
            if not self.isAssigned(var):
                return False
        return True

    """
    Gets the solution in the form of a dictionary.

    Returns:
        dictionary<string, value>
        A map from variables to their assigned values. None if not complete.
    """

    def extractSolution(self):
        """

        :rtype: dict
        """
        if not self.isComplete():
            return None
        return self.assignedValues

    def __repr__(self):
        return '---Variable Domains\n%s---Assigned Values\n%s' % (
            ''.join([str(e) + ':' + str(self.varDomains[e]) + '\n' for e in
                     self.varDomains]),
            ''.join([str(e) + ':' + str(self.assignedValues[e]) + '\n' for e in
                     self.assignedValues]))


####################################################################################################


"""
    Checks if a value assigned to a variable is consistent with all binary constraints in a problem.
    Do not assign value to var. Only check if this value would be consistent or not.
    If the other variable for a constraint is not assigned, then the new value is consistent with the constraint.

    Args:
        assignment (Assignment): the partial assignment
        csp (ConstraintSatisfactionProblem): the problem definition
        var (string): the variable that would be assigned
        value (value): the value that would be assigned to the variable
    Returns:
        boolean
        True if the value would be consistent with all currently assigned values, False otherwise
"""


def consistent(assignment, csp, var, value):
    """
    :param Assignment assignment:
    :param ConstraintSatisfactionProblem csp:
    :param str var:
    :rtype: bool
    """
    concerned_constraints = [constraint
                             for constraint in csp.binaryConstraints
                             if constraint.affects(var)
                             and assignment.isAssigned(constraint.otherVariable(var))]

    satisfactions = [constraint.isSatisfied(value, assignment.assignedValues[constraint.otherVariable(var)])
                     for constraint in concerned_constraints]

    return all(satisfactions)


"""
    Recursive backtracking algorithm.
    A new assignment should not be created. The assignment passed in should have its domains updated with inferences.
    In the case that a recursive call returns failure or a variable assignment is incorrect, the inferences made along
    the way should be reversed. See maintainArcConsistency and forwardChecking for the format of inferences.

    Examples of the functions to be passed in:
    orderValuesMethod: orderValues, leastConstrainingValuesHeuristic
    selectVariableMethod: chooseFirstVariable, minimumRemainingValuesHeuristic

    Args:
        assignment (Assignment): a partial assignment to expand upon
        csp (ConstraintSatisfactionProblem): the problem definition
        orderValuesMethod (function<assignment, csp, variable> returns list<value>): a function to decide the next value to try
        selectVariableMethod (function<assignment, csp> returns variable): a function to decide which variable to assign next
    Returns:
        Assignment
        A completed and consistent assignment. None if no solution exists.
"""


def recursiveBacktracking(assignment, csp, orderValuesMethod,
                          selectVariableMethod):
    """
    :param Assignment assignment:
    :param ConstraintSatisfactionProblem csp:
    :param (Assignment, ConstraintSatisfactionProblem, str) -> list orderValuesMethod:
    :param (Assignment, ConstraintSatisfactionProblem) -> T selectVariableMethod:
    :rtype: Assignment
    """
    return recursiveBacktrackingWithInferences(assignment, csp, orderValuesMethod,
                                               selectVariableMethod, noInferences)


"""
    Uses unary constraints to eleminate values from an assignment.

    Args:
        assignment (Assignment): a partial assignment to expand upon
        csp (ConstraintSatisfactionProblem): the problem definition
    Returns:
        Assignment
        An assignment with domains restricted by unary constraints. None if no solution exists.
"""


def eliminateUnaryConstraints(assignment, csp):
    domains = assignment.varDomains
    for var in domains:
        for constraint in (c for c in csp.unaryConstraints if c.affects(var)):
            for value in (v for v in list(domains[var]) if
                          not constraint.isSatisfied(v)):
                domains[var].remove(value)
                if len(domains[var]) == 0:
                    # Failure due to invalid assignment
                    return None
    return assignment


"""
    Trivial method for choosing the next variable to assign.
    Uses no heuristics.
"""


def chooseFirstVariable(assignment, csp):
    for var in csp.varDomains:
        if not assignment.isAssigned(var):
            return var



"""
    Selects the next variable to try to give a value to in an assignment.
    Uses minimum remaining values heuristic to pick a variable. Use degree heuristic for breaking ties.

    Args:
        assignment (Assignment): the partial assignment to expand
        csp (ConstraintSatisfactionProblem): the problem description
    Returns:
        the next variable to assign
"""


def minimumRemainingValuesHeuristic(assignment, csp):
    """
    :param Assignment assignment:
    :param ConstraintSatisfactionProblem csp:
    :rtype: str
    """
    domains = assignment.varDomains
    unassigned_variables = [variable
                            for variable in assignment.assignedValues
                            if not assignment.isAssigned(variable)]
    domain_lengths = [len(domains[variable])
                      for variable in unassigned_variables]
    min_length = min(domain_lengths)
    min_domain_length_variables = [variable
                                   for variable in unassigned_variables
                                   if len(domains[variable]) == min_length]
    variable_with_most_concerned_constraint = max(min_domain_length_variables,
                                                  key=csp.number_of_concerned_constraints)
    return variable_with_most_concerned_constraint


"""
    Trivial method for ordering values to assign.
    Uses no heuristics.
"""


def orderValues(assignment, csp, var):
    return list(assignment.varDomains[var])


"""
    Creates an ordered list of the remaining values left for a given variable.
    Values should be attempted in the order returned.
    The least constraining value should be at the front of the list.

    Args:
        assignment (Assignment): the partial assignment to expand
        csp (ConstraintSatisfactionProblem): the problem description
        var (string): the variable to be assigned the values
    Returns:
        list<values>
        a list of the possible values ordered by the least constraining value heuristic
"""


def num_of_choices(assignment, csp, var, value=None):
    """
        :param Assignment assignment:
        :param ConstraintSatisfactionProblem csp:
        :param str var:
        :return: int
    """
    domains = assignment.varDomains
    concerned_constraints = csp.concerned_constraints(var)

    return sum([len([choice
                     for choice in domains[constraint.otherVariable(var)]
                     if constraint.isSatisfied(choice, value)])
                for constraint in concerned_constraints])



def reduced_choices(assignment, csp, var, value):
    """
    :param Assignment assignment:
    :param ConstraintSatisfactionProblem csp:
    :param str var:
    :return: int
    """
    return num_of_choices(assignment, csp, var) - num_of_choices(assignment, csp, var, value=value)



def leastConstrainingValuesHeuristic(assignment, csp, var):
    """

    :param Assignment assignment:
    :param ConstraintSatisfactionProblem csp:
    :param str var:
    :rtype: list
    """
    values = list(assignment.varDomains[var])
    values.sort(key=functools.partial(reduced_choices, assignment, csp, var))
    return values


"""
    Trivial method for making no inferences.
"""


def noInferences(assignment, csp, var, value):
    return set([])


"""
    Implements the forward checking algorithm.
    Each inference should take the form of (variable, value) where the value is being removed from the
    domain of variable. This format is important so that the inferences can be reversed if they
    result in a conflicting partial assignment. If the algorithm reveals an inconsistency, any
    inferences made should be reversed before ending the fuction.

    Args:
        assignment (Assignment): the partial assignment to expand
        csp (ConstraintSatisfactionProblem): the problem description
        var (string): the variable that has just been assigned a value
        value (string): the value that has just been assigned
    Returns:
        set<tuple<variable, value>>
        the inferences made in this call or None if inconsistent assignment
"""


def forwardChecking(assignment, csp, var, value):
    """

    :param Assignment assignment:
    :param ConstraintSatisfactionProblem csp:
    :param str var:
    :param value:
    :rtype: set or None
    """
    inferences = set([])
    domains = assignment.varDomains
    concerned_constraints = csp.concerned_constraints(var)
    inferences = set((constraint.otherVariable(var), choice)
                     for constraint in concerned_constraints
                     for choice in domains[constraint.otherVariable(var)]
                     if not constraint.isSatisfied(value1=value,
                                                   value2=choice))
    for variable, choice in inferences:
        domains[variable].remove(choice)
        if not domains[variable]:
            for v, c in inferences:
                domains[v].add(c)
            return None
    return inferences


"""
    Recursive backtracking algorithm.
    A new assignment should not be created. The assignment passed in should have its domains updated with inferences.

    In the case that a recursive call returns failure or a variable assignment is incorrect, the inferences made along
    the way should be reversed. See maintainArcConsistency and forwardChecking for the format of inferences.


    Examples of the functions to be passed in:
    orderValuesMethod: orderValues, leastConstrainingValuesHeuristic
    selectVariableMethod: chooseFirstVariable, minimumRemainingValuesHeuristic
    inferenceMethod: noInferences, maintainArcConsistency, forwardChecking


    Args:
        assignment (Assignment): a partial assignment to expand upon
        csp (ConstraintSatisfactionProblem): the problem definition
        orderValuesMethod (function<assignment, csp, variable> returns list<value>): a function to decide the next value to try
        selectVariableMethod (function<assignment, csp> returns variable): a function to decide which variable to assign next
        inferenceMethod (function<assignment, csp, variable, value> returns set<variable, value>): a function to specify what type of inferences to use
                Can be forwardChecking or maintainArcConsistency
    Returns:
        Assignment

        A completed and consistent assignment. None if no solution exists.
"""


def recursiveBacktrackingWithInferences(assignment, csp, orderValuesMethod,
                                        selectVariableMethod, inferenceMethod):
    """
    :param Assignment assignment:
    :param ConstraintSatisfactionProblem csp:
    :param (Assignment, ConstraintSatisfactionProblem, str) -> list orderValuesMethod:
    :param (Assignment, ConstraintSatisfactionProblem) -> T selectVariableMethod:
    :param (Assignment, ConstraintSatisfactionProblem, str, T) -> set[(str, T)] inferenceMethod:
    :rtype: Assignment
    """

    if assignment.isComplete():
        return assignment

    next_variable = selectVariableMethod(assignment, csp)
    consistent_values = [value
                         for value in orderValuesMethod(assignment, csp, next_variable)
                         if consistent(assignment, csp, next_variable, value)]
    for value in consistent_values:
        current_value = assignment.assignedValues[next_variable]
        assignment.assignedValues[next_variable] = value
        inferences = inferenceMethod(assignment, csp, next_variable, value)
        if inferences is not None:
            ret_solution = recursiveBacktracking(assignment, csp, orderValuesMethod, selectVariableMethod)
            if ret_solution:
                return ret_solution
        assignment.assignedValues[next_variable] = current_value
        if inferences is not None:
            for var, val in inferences:
                assignment.varDomains[var].add(val)
    return None


"""
    Helper funciton to maintainArcConsistency and AC3.
    Remove values from var2 domain if constraint cannot be satisfied.
    Each inference should take the form of (variable, value) where the value is being removed from the
    domain of variable. This format is important so that the inferences can be reversed if they
    result in a conflicting partial assignment. If the algorithm reveals an inconsistency, any
    inferences made should be reversed before ending the fuction.

    Args:
        assignment (Assignment): the partial assignment to expand
        csp (ConstraintSatisfactionProblem): the problem description
        var1 (string): the variable with consistent values
        var2 (string): the variable that should have inconsistent values removed
        constraint (BinaryConstraint): the constraint connecting var1 and var2
    Returns:
        set<tuple<variable, value>>
        the inferences made in this call or None if inconsistent assignment
"""


def revise(assignment, csp, var1, var2, constraint):
    """
    :param Assignment assignment:
    :param ConstraintSatisfactionProblem csp:
    :param str var1:
    :param str var2:
    :param BinaryConstraint constraint:
    :rtype: set[(str, T)]
    """
    domains = assignment.varDomains
    inferences = set([])
    for val2 in domains[var2]:
        is_consistent = any(constraint.isSatisfied(val1, val2) for val1 in domains[var1])
        if not is_consistent:
            inferences.add((var2, val2))

    if len(inferences) == len(domains[var2]):
        return None

    for var, val in inferences:
        domains[var].remove(val)

    return inferences


"""
    Implements the maintaining arc consistency algorithm.
    Inferences take the form of (variable, value) where the value is being removed from the
    domain of variable. This format is important so that the inferences can be reversed if they
    result in a conflicting partial assignment. If the algorithm reveals an inconsistency, and
    inferences made should be reversed before ending the fuction.

    Args:
        assignment (Assignment): the partial assignment to expand
        csp (ConstraintSatisfactionProblem): the problem description
        var (string): the variable that has just been assigned a value
        value (string): the value that has just been assigned
    Returns:
        set<<variable, value>>
        the inferences made in this call or None if inconsistent assignment
"""


def maintainArcConsistency(assignment, csp, var=None, value=None, initialQueue=False):
    """

    :param Assignment assignment:
    :param ConstraintSatisfactionProblem csp:
    :param str var:
    :param T value:
    :rtype: set[(str, T)]
    """
    inferences = set([])
    queue = util.Queue()
    domains = assignment.varDomains
    if initialQueue:
        for constraint in csp.binaryConstraints:
            queue.push((constraint.var1, constraint.var2, constraint))
            queue.push((constraint.var2, constraint.var1, constraint))
    else:
        for constraint in csp.concerned_constraints(var):
            queue.push((var, constraint.otherVariable(var), constraint))

    while not queue.isEmpty():
        var1, var2, constraint = queue.pop()
        inference = revise(assignment, csp, var1, var2, constraint)
        if inference is None:
            for _var, _val in inferences:
                domains[_var].add(_val)
            return None
        if inference:
            for _constraint in csp.concerned_constraints(var2):
                queue.push((var2, _constraint.otherVariable(var2), _constraint))
            inferences |= inference

    return inferences


"""
    AC3 algorithm for constraint propogation. Used as a preprocessing step to reduce the problem
    before running recursive backtracking.

    Args:
        assignment (Assignment): the partial assignment to expand
        csp (ConstraintSatisfactionProblem): the problem description
    Returns:
        Assignment
        the updated assignment after inferences are made or None if an inconsistent assignment
"""


def AC3(assignment, csp):
    ret = maintainArcConsistency(assignment, csp, initialQueue=True)
    if ret is None:
        return None
    return assignment


"""
    Solves a binary constraint satisfaction problem.

    Args:
        csp (ConstraintSatisfactionProblem): a CSP to be solved
        orderValuesMethod (function): a function to decide the next value to try
        selectVariableMethod (function): a function to decide which variable to assign next
        inferenceMethod (function): a function to specify what type of inferences to use
        useAC3 (boolean): specifies whether to use the AC3 preprocessing step or not
    Returns:
        dictionary<string, value>
        A map from variables to their assigned values. None if no solution exists.
"""


def solve(csp, orderValuesMethod=leastConstrainingValuesHeuristic,
          selectVariableMethod=minimumRemainingValuesHeuristic,
          inferenceMethod=None, useAC3=True):
    assignment = Assignment(csp)

    assignment = eliminateUnaryConstraints(assignment, csp)
    if assignment == None:
        return assignment

    if useAC3:
        assignment = AC3(assignment, csp)
        if assignment == None:
            return assignment
    if inferenceMethod is None or inferenceMethod == noInferences:
        assignment = recursiveBacktracking(assignment, csp, orderValuesMethod,
                                           selectVariableMethod)
    else:
        assignment = recursiveBacktrackingWithInferences(assignment, csp,
                                                         orderValuesMethod,
                                                         selectVariableMethod,
                                                         inferenceMethod)
    if assignment == None:
        return assignment

    return assignment.extractSolution()
