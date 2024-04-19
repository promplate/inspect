from pathlib import Path
from re import DOTALL, findall

from promplate_inspect import find_input_variables_in_template


def test_readme_example():
    [template] = findall(r'"""(.+?)"""', Path("README.md").read_text(), DOTALL)

    assert find_input_variables_in_template(template) == {"e", "f", "g", "h"}

    assert find_input_variables_in_template(template, False) == {"e", "f", "g", "h", "list"}
