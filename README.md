Course: LING224
Final Project

Name: QianXiang Shen
Email: qshen11@u.rochester.edu

There are three .py files in my source code: "grammar.py", "parser.py", "tree.py".
grammar.py holds all the rules and elements classes that build the unit element of a MCFG grammar.
parser.py does all the parsing work based on functions provided by grammar.py
tree.py holds a basic tree structure class that is used to represent the structure of parsing and the sentence inputing.

grammar:
- MCFGRuleElement
The basic unit element of a rule. Holds a string vairable and several simble representing the string in an abstract way.
- MCFGRuleElementInstance
The basic unit element of a real rule. Holds a string variable and several pairs of indices.
- MCFGRule
It represent the a rule in MCFG. take both MCFGRuleElement and MCFGRuleElementInstance as components. It works both for abstract and representing a real one.
- MultipleContextFreeGrammar
The grammart which holds several rules. It also contains an important reduce function which helps categorize strings and parsing.

parser:
- Entry
A basic unit during the calculation of parsing. It contains a rule and pointers that points to previous rules
- Agenda
A list of entry that read waited to be loaded into the chart to calculate. New entries create from claculation in chart will added into this list.
- Chart
A list of entry that has been calculated. They might join further calculation.
- AgendaParser
The class that does the parsing. It holds an agenda and a chart.
