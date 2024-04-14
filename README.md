# promplate-inspect

Inspect input variables used in a `promplate` template.

Useful when instructing an LLM to produce structural data with certain fields,
or for you to quickly understand the data structure a template expects.

```sh
pip install promplate-inspect
```

## Usage

```py
from promplate import Template
from promplate_inspect import find_input_variables_in_template

t = Template("""

    {#
        import a as b
        from c import d
    #}

    {{ e }}

    {{ f.strip() }}

    {{ list }}

    {#
        g += 1
        h = { **h }
    #}

    {% for i in func() %}

        {{ [ j for j in range(i) ] }}

    {% endfor %}

""")

find_input_variables_in_template(t)  # {'e', 'f', 'g', 'h'}
```

Note that it excludes builtin names by default.
If you allow LLM to output variables like `dict` or `list`,
you can specify the second parameter `exclude_builtins`:

```py
find_input_variables_in_template(t, exclude_builtins=False)  # {'e', 'f', 'g', 'h', 'list'}
```

As you see, variables that defined explicitly in the templates are not filtered out as expected.
And functions above like `func` and `range` are always excluded because LLM can never out callable instances typically.

## Limitations

1. This parser is still **work in progress**. If you includes any of these code in your `{{ }}`/`{# #}` tags, the result may be wrong:
   - Parameters of function. Inspecting `{{ (lambda x: x + 1)(y) }}` should output `{'y'}` but outputs `{'x', 'y'}` for now.
   - Similarly, variables defined in `with` statements and `except` statements are not excluded for now.
2. This implementation use `ast` to parse the template. It never run the code, so these monkey patches won't be tracked:
   - Getting variables from `globals()`/`locals()`/`__main__` won't be finded. Such as `name` won't be found in `{{ locals()["name"] }}`.
   - Assigning values to `globals()`/`locals()`/`__main__` won't be excluded. Even if you wrote `{# globals().setdefault("name", "value") #}`, `name` will still be found in `{{ name }}`.
3. For now it only find variables in the given template itself. It don't find variables needed in the components used by it.
