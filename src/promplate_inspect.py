from ast import Assign, AsyncFor, AugAssign, Call, For, ListComp, Load, Name, NodeVisitor, Store, Subscript, parse
from textwrap import dedent
from typing import Set, Union

from promplate import Template
from promplate.prompt.utils import get_builtins, split_template_tokens


class VariableVisitor(NodeVisitor):
    def __init__(self):
        self.necessary_vars = set()
        self.unnecessary_vars = set()

    def visit_Name(self, node: Name):
        if isinstance(node.ctx, Load) and node.id not in self.unnecessary_vars:
            self.necessary_vars.add(node.id)
        elif isinstance(node.ctx, Store):
            self.unnecessary_vars.add(node.id)

    def visit_Assign(self, node: Assign):
        # right first
        self.visit(node.value)

        for target in node.targets:
            self.visit(target)

    def visit_AugAssign(self, node: AugAssign):
        # left first
        target = node.target
        if isinstance(target, Name) and target.id not in self.unnecessary_vars:
            self.necessary_vars.add(target.id)  # because it's a store
        else:
            self.visit(target)

        self.visit(node.value)

    def visit_ListComp(self, node: ListComp):
        # right first
        for generator in node.generators:
            self.visit(generator)

        self.visit(node.elt)

    def visit_Call(self, node: Call):
        sub_node = node.func

        while isinstance(sub_node, Subscript):
            sub_node = sub_node.value

        if isinstance(sub_node, Name):
            # LLM never provides a Callable
            self.unnecessary_vars.add(sub_node.id)

        self.generic_visit(node)

    def _visit_for(self, node: Union[For, AsyncFor]):
        self.visit(node.target)
        self.visit(node.iter)

    visit_For = visit_AsyncFor = _visit_for


builtins = set(get_builtins())


def find_input_variables_in_code(source: str, exclude_builtins=True) -> Set[str]:
    tree = parse(source)
    visitor = VariableVisitor()
    visitor.visit(tree)
    if exclude_builtins:
        return visitor.necessary_vars - builtins
    return visitor.necessary_vars


def find_input_variables_in_template(template: Union[Template, str], exclude_builtins=True) -> Set[str]:
    text = template if isinstance(template, str) else template.text

    tokens = []

    for token in split_template_tokens(text):
        if token is None:
            continue
        token = token.strip()
        if (
            (token.startswith("{{") and token.endswith("}}"))
            or (token.startswith("{#") and token.endswith("#}"))
            or (token.startswith("{%") and token.endswith("%}") and token[2:].strip().split(" ", 1)[0] in {"if", "for", "while", "elif", "else", "endif", "endfor", "endwhile"})
        ):
            tokens.append(token if token[-3] != "-" else f"{token[:-3]}{token[-2:]}")

    source = Template("".join(tokens)).get_script()
    source = source[source.index("\n") + 1 : source.rindex("return")]  # remove render function definition
    source = dedent(source)

    return find_input_variables_in_code(source, exclude_builtins)
