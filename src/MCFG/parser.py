from src.MCFG import grammar
from src.MCFG import tree

from enum import Enum

from abc import ABC
from typing import Union

BackPointer = grammar.MCFGRuleElementInstance

class Entry():
    
    def __init__(self, rule: grammar.MCFGRuleElementInstance, *backpointers: BackPointer) -> None:
        self._rule = rule
        self._backpointers = backpointers
        
    def to_tuple(self) -> tuple[grammar.MCFGRuleElementInstance, tuple[BackPointer, ...]]:
        return self._rule, self._backpointers

    def __hash__(self) -> int:
        return hash(self.to_tuple())

    def __eq__(self, other) -> bool:
        return self.to_tuple() == other.to_tuple() # .__key()

    def __repr__(self) -> str:
        return self._rule.__repr__()

    def __str__(self) -> str:
        return self.__repr__()
    
    @property
    def backpointers(self) -> tuple[BackPointer, ...]:
        return self._backpointers

    @property
    def rule(self):
        return self._rule
    
    def reduce_with(self, other, grammar: grammar.MultipleContextFreeGrammar) -> set:
        return grammar.reduce(self.rule, other.rule)

class Agenda():
    
    def __init__(self) -> None:
        self._stack = []
    
    def add(self, item: Entry) -> None:
        self._stack.append(item)
    
    def pop(self) -> Entry:
        return self._stack.pop()
    
    def add_string(self, string: str, *spans: tuple[int, ...]) -> None:
        item = grammar.MCFGRuleElementInstance(string, spans[0])
        self.add(Entry(item))
    
    def add_strings(self, strings: list[str]) -> None:
        for i in range(len(strings)):
            self.add_string(strings[len(strings) - i - 1], (len(strings) - i - 1, len(strings) - i))
    
    def is_empty(self) -> bool:
        return len(self._stack) == 0

class Chart():
    
    def __init__(self, gram: grammar.MultipleContextFreeGrammar) -> None:
        self._list = []
        self.gram = gram
    
    def add(self, item: Entry) -> set[grammar.MCFGRuleElementInstance]:
        output = set()
        for i in self.gram.parts_of_speech(item.rule.variable):
            output.add(Entry(grammar.MCFGRuleElementInstance(i, item.rule.string_spans[0]), item.rule))
        for i in self._list:
            re_set = self.gram.reduce(item.rule, i.rule)
            re_set_revise = self.gram.reduce(i.rule, item.rule)
            if len(re_set) != 0:
                for j in re_set:
                    output.add(Entry(j, item.rule, i.rule))
            if len(re_set_revise) != 0:
                for j in re_set_revise:
                    output.add(Entry(j, i.rule, item.rule))
        self._list.append(item)
        return output
    
    def has(self, item: grammar.MCFGRuleElementInstance) -> bool:
        for i in self._list:
            if i.rule == item:
                return True
        return False
    
    # def build_tree(self, node: Entry) -> tree.Tree:
    #     if len(Entry.backpointers) == 0:
    #         return tree.Tree(Entry.rule)
    #     else:
    #         return tree.Tree(Entry.rule, self.build_tree())
    
    # def parses(self, root: grammar.MCFGRuleElementInstance):
    #     output = tree.Tree(root, list())

class NormalForm(Enum):
    CNF = 0
    BNF = 1
    GNF = 2

class AgendaParser():
    
    def __init__(self, gram: grammar.MCFGRuleElementInstance, final_var: str) -> None:
        self._agenda = Agenda()
        self._chart = Chart(gram)
        self._gram = gram
        self._final_var = final_var
    
    def __call__(self, string, mode="recognize"):
        if mode == "recognize":
            return self._recognize(string)
        elif mode == "parse":
            return self._parse(string)
        else:
            msg = 'mode must be "parse" or "recognize"'
            raise ValueError(msg)
    
    normal_form = NormalForm.CNF

    def _fill_chart(self, string: list[str]) -> None:
        self._agenda.add_strings(string)
        while not self._agenda.is_empty():
            new_items = self._chart.add(self._agenda.pop())
            for i in new_items:
                self._agenda.add(i)
            # print(self._agenda._stack)
            # print(self._chart._list)
            # print(self._chart._list[-1].backpointers)
            # print(self._agenda.is_empty())

    def _parse(self, string):
        self._fill_chart(string)
        target = grammar.MCFGRuleElementInstance(self._final_var, (0, len(string)))
        # print(target)
        if self._chart.has(target):
            return self._chart.parses(target)
        else:
            return False

    def _recognize(self, string):
        self._fill_chart(string)
        target = grammar.MCFGRuleElementInstance(self._final_var, (0, len(string)))
        # print(target)
        return self._chart.has(target)