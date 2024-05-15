import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from src.MCFG import grammar
from src.MCFG import parser

text = """S(uv) -> NP(u) VP(v)
S(uv) -> NPwh(u) VP(v)
S(vuw) -> Aux(u) Swhmain(v, w)
S(uwv) -> NPdisloc(u, v) VP(w)
S(uwv) -> NPwhdisloc(u, v) VP(w)
Sbar(uv) -> C(u) S(v)
Sbarwh(v, uw) -> C(u) Swhemb(v, w)
Sbarwh(u, v) -> NPwh(u) VP(v)
Swhmain(v, uw) -> NP(u) VPwhmain(v, w)
Swhmain(w, uxv) -> NPdisloc(u, v) VPwhmain(w, x)
Swhemb(v, uw) -> NP(u) VPwhemb(v, w)
Swhemb(w, uxv) -> NPdisloc(u, v) VPwhemb(w, x)
Src(v, uw) -> NP(u) VPrc(v, w)
Src(w, uxv) -> NPdisloc(u, v) VPrc(w, x)
Src(u, v) -> N(u) VP(v)
Swhrc(u, v) -> Nwh(u) VP(v)
Swhrc(v, uw) -> NP(u) VPwhrc(v, w)
Sbarwhrc(v, uw) -> C(u) Swhrc(v, w)
VP(uv) -> Vpres(u) NP(v)
VP(uv) -> Vpres(u) Sbar(v)
VPwhmain(u, v) -> NPwh(u) Vroot(v)
VPwhmain(u, wv) -> NPwhdisloc(u, v) Vroot(w)
VPwhmain(v, uw) -> Vroot(u) Sbarwh(v, w)
VPwhemb(u, v) -> NPwh(u) Vpres(v)
VPwhemb(u, wv) -> NPwhdisloc(u, v) Vpres(w)
VPwhemb(v, uw) -> Vpres(u) Sbarwh(v, w)
VPrc(u, v) -> N(u) Vpres(v)
VPrc(v, uw) -> Vpres(u) Nrc(v, w)
VPwhrc(u, v) -> Nwh(u) Vpres(v)
VPwhrc(v, uw) -> Vpres(u) Sbarwhrc(v, w)
NP(uv) -> D(u) N(v)
NP(uvw) -> D(u) Nrc(v, w)
NPdisloc(uv, w) -> D(u) Nrc(v, w)
NPwh(uv) -> Dwh(u) N(v)
NPwh(uvw) -> Dwh(u) Nrc(v, w)
NPwhdisloc(uv, w) -> Dwh(u) Nrc(v, w)
Nrc(v, uw) -> C(u) Src(v, w)
Nrc(u, vw) -> N(u) Swhrc(v, w)
Nrc(u, vwx) -> Nrc(u, v) Swhrc(w, x)
Dwh(which)
Nwh(who)
D(the)
D(a)
N(greyhound)
N(human)
Vpres(believes)
Vroot(believe)
Aux(does)
C(that)"""

assert grammar.MCFGRuleElement('VPwhemb', (0,), (1,)) == grammar.MCFGRuleElement('VPwhemb', (0,), (1,)), "MCFGRuleElement is unhashable"

assert str(grammar.MCFGRuleElement('VPwhemb', (0,), (1,))) + " -> " + str(grammar.MCFGRuleElement('NPwh', (0,))) + " " + str(grammar.MCFGRuleElement('Vpres', (1,))) == "VPwhemb(0, 1) -> NPwh(0) Vpres(1)", "Errors occur during representing rules"

rule = grammar.MCFGRule.from_string('A(w1u, x1v) -> B(w1, x1) C(u, v)')

assert str(rule) == "A(02, 13) -> B(0, 1) C(2, 3)", "Error occurs when stating a rule"

rules = set()
for i in text.split("\n"):
    rules.add(grammar.MCFGRule.from_string(i))

alphabet_set = set()
for i in rules:
    if i.is_epsilon:
        alphabet_set.add(i.left_side.string_variables[0][0])

variables_set = set()
for i in rules:
    variables_set.add(i.left_side.variable)
    
test_grammar = grammar.MultipleContextFreeGrammar(alphabet=alphabet_set, 
                                     variables=variables_set, 
                                     rules=rules, 
                                     start_variable='S')

test_grammar.parser_class = parser.AgendaParser
test_grammar.init_parser()

assert test_grammar.rules() == rules, "Error occurs during calling rules() function"
assert test_grammar.parts_of_speech() == {'C', 'Nwh', 'Aux', 'N', 'D', 'Vroot', 'Vpres', 'Dwh'}, "Error occurs during calling parts_of_speech funciton"
assert str(test_grammar.parts_of_speech('a')) == "{'D'}", "Error occurs during finding rules that contains 'a'"

A = grammar.MCFGRuleElementInstance('D', (1, 2))
B = grammar.MCFGRuleElementInstance('Nrc', (2, 3), (3, 5))
C = grammar.MCFGRuleElementInstance('NP', (1, 5))
D = grammar.MCFGRuleElementInstance('NPdisloc', (1, 3), (3, 5))
assert test_grammar.reduce(A, B) == {C, D}, "Error occurs when reducing the example rules"

assert test_grammar(['a', 'human', 'believes', 'a', 'human']) == True, "Error occurs when parsing the sentence"