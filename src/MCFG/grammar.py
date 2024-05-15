import re
from typing import Literal
from functools import lru_cache
from enum import Enum

StringVariables = tuple[int, ...]

class MCFGRuleElement:

    """A multiple context free grammar rule element

    Parameters
    ----------
    variable
    string_variables

    Attributes
    ----------
    symbol
    string_variables
    """

    def __init__(self, variable: str, *string_variables: StringVariables):
        self._variable = variable
        self._string_variables = string_variables

    def __str__(self) -> str:
        strvars = ', '.join(
            ''.join(str(v) for v in vtup)
            for vtup in self._string_variables
        )
        
        return f"{self._variable}({strvars})"

    def __eq__(self, other) -> bool:
        vareq = self._variable == other._variable
        strvareq = self._string_variables == other._string_variables
        
        return vareq and strvareq
        
    def to_tuple(self) -> tuple[str, tuple[StringVariables, ...]]:
        return (self._variable, self._string_variables)

    def __hash__(self) -> int:
        return hash(self.to_tuple())
        
    @property
    def variable(self) -> str:
        return self._variable

    @property
    def string_variables(self) -> tuple[StringVariables, ...]:
        return self._string_variables

    @property    
    def unique_string_variables(self) -> set[int]:
        return {
            i
            for tup in self.string_variables
            for i in tup
        }
        
SpanIndices = tuple[int, ...]

class MCFGRuleElementInstance:
    """An instantiated multiple context free grammar rule element

    Parameters
    ----------
    symbol
    string_spans

    Attributes
    ----------
    symbol
    string_spans
    """
    def __init__(self, variable: str, *string_spans: SpanIndices):
        self._variable = variable
        self._string_spans = string_spans

    def __eq__(self, other: 'MCFGRuleElementInstance') -> bool:
        vareq = self._variable == other._variable
        strspaneq = self._string_spans == other._string_spans
        
        return vareq and strspaneq
        
    def to_tuple(self) -> tuple[str, tuple[SpanIndices, ...]]:
        return (self._variable, self._string_spans)

    def __hash__(self) -> int:
        return hash(self.to_tuple())

    def __str__(self):
        strspans = ', '.join(
            str(list(stup))
            for stup in self._string_spans
        )
        
        return f"{self._variable}({strspans})"

    def __repr__(self) -> str:
        return self.__str__()
    
    @property
    def variable(self) -> str:
        return self._variable

    @property
    def string_spans(self) -> tuple[SpanIndices, ...]:
        return self._string_spans

SpanMap = dict[int, SpanIndices]

class NormalForm(Enum):
    CNF = 0
    BNF = 1
    GNF = 2

class MCFGRule:
    """A linear multiple context free grammar rule

    Parameters
    ----------
    left_side 
    right_side

    Attributes
    ----------
    left_side
    right_side
    """

    def __init__(self, left_side: MCFGRuleElement, *right_side: MCFGRuleElement):
        self._left_side = left_side
        self._right_side = right_side

        self._validate()

    def to_tuple(self) -> tuple[MCFGRuleElement, tuple[MCFGRuleElement, ...]]:
        return (self._left_side, self._right_side)

    def __hash__(self) -> int:
        return hash(self.to_tuple())
    
    def __repr__(self) -> str:
        return '<Rule: '+str(self)+'>'
        
    def __str__(self) -> str:
        if self.is_epsilon:
            return str(self._left_side)                

        else:
            return str(self._left_side) +\
                ' -> ' +\
                ' '.join(str(el) for el in self._right_side)

    def __eq__(self, other: 'MCFGRule') -> bool:
        left_side_equal = self._left_side == other._left_side
        right_side_equal = self._right_side == other._right_side

        return left_side_equal and right_side_equal

    def _validate(self):
        vs = [
            el.unique_string_variables
            for el in self.right_side
        ]
        sharing = any(
            vs1.intersection(vs2)
            for i, vs1 in enumerate(vs)
            for j, vs2 in enumerate(vs)
            if i < j
        )

        if sharing:
            raise ValueError(
                'right side variables cannot share '
                'string variables'
            )

        if not self.is_epsilon:
            left_vars = self.left_side.unique_string_variables
            right_vars = {
                var for el in self.right_side
                for var in el.unique_string_variables
            }
            if left_vars != right_vars:
                raise ValueError(
                    'number of arguments to instantiate must '
                    'be equal to number of unique string_variables'
                )
        
    @property
    def left_side(self) -> MCFGRuleElement:
        return self._left_side

    @property
    def right_side(self) -> tuple[MCFGRuleElement, ...]:
        return self._right_side

    @property
    def is_epsilon(self) -> bool:
        return len(self._right_side) == 0

    @property
    def unique_variables(self) -> set[str]:
        return {
            el.variable
            for el in [self._left_side]+list(self._right_side)
        }

    def instantiate_left_side(self, *right_side: MCFGRuleElementInstance) -> MCFGRuleElementInstance:
        """Instantiate the left side of the rule given an instantiated right side

        Parameters
        ----------
        right_side
            The instantiated right side of the rule.
        """
        
        if self.is_epsilon:
            strvars = tuple(v[0] for v in self._left_side.string_variables)
            strconst = tuple(el.variable for el in right_side)
            
            if strconst == strvars:
                return MCFGRuleElementInstance(
                    self._left_side.variable,
                    *[s for el in right_side for s in el.string_spans]
                )

        new_spans = []
        span_map = self._build_span_map(right_side[0])
        
        for vs in self._left_side.string_variables:
            for i in range(1,len(vs)):
                end_prev = span_map[vs[i-1]][1]
                begin_curr = span_map[vs[i]][0]

                if end_prev != begin_curr:
                    raise ValueError(
                        f"Spans {span_map[vs[i-1]]} and {span_map[vs[i]]} "
                        f"must be adjacent according to {self} but they "
                        "are not."
                    )
                
            begin_span = span_map[vs[0]][0]
            end_span = span_map[vs[-1]][1]

            new_spans.append((begin_span, end_span))

        return MCFGRuleElementInstance(
            self._left_side.variable, *new_spans
        )

    
    def _build_span_map(self, right_side: tuple[MCFGRuleElementInstance, ...]) -> SpanMap:
        """Construct a mapping from string variables to string spans"""

        if self._right_side_aligns(right_side):
            return {
                strvar[0]: strspan
                for elem, eleminst in zip(
                    self._right_side,
                    right_side
                )
                for strvar, strspan in zip(
                    elem.string_variables,
                    eleminst.string_spans
                )
            }
        else:
            raise ValueError(
                f"Instantiated right side {right_side} do not "
                f"align with rule's right side {self._right_side}"
            )

    def _right_side_aligns(self, right_side: tuple[MCFGRuleElementInstance, ...]) -> bool:
        """Check whether the right side aligns"""

        if len(right_side) == len(self._right_side):
            vars_match = all(
                elem.variable == eleminst.variable
                for elem, eleminst in zip(self._right_side, right_side)
            )
            strvars_match = all(
                len(elem.string_variables) == len(eleminst.string_spans)
                for elem, eleminst in zip(self._right_side, right_side)
            )

            return vars_match and strvars_match
        else:
            return False 

    @classmethod
    def from_string(cls, rule_string) -> 'MCFGRule':
        elem_strs = re.findall('(\w+)\(((?:\w+,? ?)+?)\)', rule_string)

        elem_tuples = [(var, [v.strip()
                              for v in svs.split(',')])
                       for var, svs in elem_strs]

        if len(elem_tuples) == 1:
            return cls(MCFGRuleElement(elem_tuples[0][0],
                                   tuple(w for w in elem_tuples[0][1])))

        else:
            strvars = [v for _, sv in elem_tuples[1:] for v in sv]

            # no duplicate string variables
            try:
                assert len(strvars) == len(set(strvars))
            except AssertionError:
                msg = 'variables duplicated on right side of '+rule_string
                raise ValueError(msg)

            
            elem_left = MCFGRuleElement(elem_tuples[0][0],
                                    *[tuple([strvars.index(v)
                                             for v in re.findall('('+'|'.join(strvars)+')', vs)])
                                      for vs in elem_tuples[0][1]])

            elems_right = [MCFGRuleElement(var, *[(strvars.index(sv),)
                                              for sv in svs])
                           for var, svs in elem_tuples[1:]]

            return cls(elem_left, *elems_right)
        
    def string_yield(self):
        if self.is_epsilon:
            return self._left_side.variable
        else:
            raise ValueError(
                'string_yield is only implemented for epsilon rules'
            )
    
    def validate(self, alphabet: set[str], variables: set[str], normal_form: NormalForm = NormalForm.CNF):
        """validate the rule

        Args:
            alphabet (set[str]): the alphabet of the grammar
            variables (set[str]): the variables of the grammar
            normal_form (NormalForm, optional): the normal form of the grammar. Defaults to NormalForm.CNF.

        Returns:
            _type_: nothing
        """
        if self.left_side.variable not in variables:
            msg = "left side of rule must be a variable"
            raise ValueError(msg)
        
        acceptable = alphabet | variables | {''}
        
        if not all(s.variable in acceptable for s in self.right_side):
            msg = "right side of rule must contain only" +\
                  "a variable, a symbol, or the empty string"
            raise ValueError(msg)
        
        if normal_form == NormalForm.CNF:
            try:
                if self.is_epsilon:
                    for v in self.right_side[0].string_variables:
                        assert v in alphabet
                elif len(self.right_side) == 2:
                    assert all([s.variable in variables for s in self.right_side])
                else:
                    raise AssertionError

            except AssertionError:
                raise ValueError(f"{self} is not in CNF")
            
Mode = Literal["recognize", "parse"]

class MultipleContextFreeGrammar:

    """
    A multiple context free grammar

    Parameters
    ----------
    alphabet : set(str)
    variables : set(str)
    rules : set(MCFGRule)
    start_variable : str

    Attributes
    ----------
    alphabet : set(str)
    variables : set(str)
    rules : set(MCFGRule)
    start_variable : str

    Methods
    -------
    reduce(left_side)
    """
    parser_class = None
    
    def __init__(self, alphabet: set[str], variables: set[str], rules: set[MCFGRule], start_variable: str):
        self._alphabet = alphabet
        self._variables = variables
        self._rules = rules
        self._start_variable = start_variable
        
        self._validate_variables()
        self._validate_rules()

        if self.parser_class is not None:
            self._parser = self.parser_class(self)
        else:
            self._parser = None
    
    def init_parser(self):
        if self.parser_class is not None:
            self._parser = self.parser_class(self, self._start_variable)
        else:
            self._parser = None

    def __call__(self, string: str | list[str], mode: Mode = "recognize"):
        if self._parser is not None:
            return self._parser(string, mode)
        else:
            raise AttributeError("no parser is specified")
        
    def _validate_variables(self):
        if self._alphabet & self._variables:
            raise ValueError('alphabet and variables must not share elements')
        
        if self._start_variable not in self._variables:
            raise ValueError('start variable must be in set of variables')

    def _validate_rules(self):
        if self.parser_class is not None:
            for r in self._rules:
                r.validate(self._alphabet, self._variables,
                           self.parser_class.normal_form)

    @property            
    def alphabet(self) -> set[str]:
        return self._alphabet

    @property    
    def variables(self) -> set[str]:
        return self._variables
   
    @lru_cache(2**10)
    def rules(self, left_side: str | None = None) -> set[MCFGRule]:
        if left_side is None:
            return self._rules
        else:
            return {rule for rule in self._rules 
                    if rule.left_side.variable == left_side}

    @property
    def start_variable(self) -> str:
        return self._start_variable

    @lru_cache(2**14)
    def parts_of_speech(self, word: str | None = None) -> set[str]:
        if word is None:
            # for rule in self._rules:
            #     if rule.is_epsilon:
            #         for v in rule.left_side.string_variables:
            #             print(rule)
            #             print(v)
            #             print(v[0])
            #             print(v[0] in self._alphabet)
            return {rule.left_side.variable for rule in self._rules 
                    if rule.is_epsilon
                    for v in rule.left_side.string_variables
                    if v[0] in self._alphabet}
        
        else:
            return {rule.left_side.variable for rule in self._rules 
                    if rule.is_epsilon
                    for v in rule.left_side.string_variables
                    if v[0] == word}
  
    @property
    def phrase_variables(self) -> set[str]:
        try:
            return self._phrase_variables
        except AttributeError:
            self._phrase_variables = {rule.left_side.variable for rule in self._rules 
                                      if not rule.is_epsilon}
            return self._phrase_variables

    @lru_cache(2^15)
    def reduce(self, *right_side: MCFGRuleElementInstance) -> set[MCFGRuleElementInstance]:
        """
        the nonterminals that can be rewritten as right_side

        Parameters
        ----------
        right_side

        Returns
        -------
        set(str)
        """
        output = set()
        for r in self._rules:
            # print(r)
            if r._right_side_aligns(right_side):
                SpanMap = r._build_span_map(right_side)
                # print(right_side)
                # print(r)
                # print(SpanMap)
                check = True
                for i in r.left_side.string_variables:
                    # print(i)
                    for j in range(1,len(i)):
                        # print(j)
                        end_prev = SpanMap[i[j-1]][1]
                        begin_curr = SpanMap[i[j]][0]
                        if end_prev != begin_curr:
                            check = False
                    
                if check:
                    output.add(r.instantiate_left_side(right_side))
        return output
        # return {r.instantiate_left_side(right_side) for r in self._rules
        #         if r._right_side_aligns(right_side)}