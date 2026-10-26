---
id: sciref-sympy-code-generation-printing
name: "Scientific Ref: SymPy Code Generation and Printing"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (sympy): SymPy Code Generation and Printing"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "sympy code generation printing"
  - "sympy codigo generation printing"
  - "sympy code generation and printing"
keywords:
  - "sympy"
  - "code"
  - "generation"
  - "printing"
  - "codigo"
  - "specialized"
  - "scientific"
  - "reference"
---

# SymPy Code Generation and Printing

Examples in this reference are ordered session fragments: run earlier imports and
setup first. Tested with SymPy 1.14.0; exceptions are explicitly marked illustrative.

This document covers SymPy's capabilities for generating executable code in various languages, converting expressions to different output formats, and customizing printing behavior.

`lambdify` generates and executes Python code internally. Use trusted expressions
and symbol names only. Select a backend explicitly, check all free symbols are
arguments, and test scalar/array shapes and singularities after conversion.

## Code Generation

### Converting to NumPy Functions

```python
from sympy import symbols, sin, cos, lambdify
import numpy as np

x, y = symbols('x y')
expr = sin(x) + cos(y)

# Create NumPy function
f = lambdify((x, y), expr, 'numpy')

# Use with NumPy arrays
x_vals = np.linspace(0, 2*np.pi, 100)
y_vals = np.linspace(0, 2*np.pi, 100)
result = f(x_vals, y_vals)
```

### Lambdify Options

```python
from sympy import lambdify, exp, sqrt
expr = exp(x) + sqrt(x)

# Different backends
f_numpy = lambdify(x, expr, 'numpy')      # NumPy
f_scipy = lambdify(x, expr, 'scipy')      # SciPy
f_mpmath = lambdify(x, expr, 'mpmath')    # mpmath (arbitrary precision)
f_math = lambdify(x, expr, 'math')        # Python math module

# Custom function mapping
custom_funcs = {'sin': lambda x: x}  # Replace sin with identity
f = lambdify(x, sin(x), modules=[custom_funcs, 'numpy'])

# Multiple expressions
exprs = [x**2, x**3, x**4]
f = lambdify(x, exprs, 'numpy')
# Returns a list of results; list nesting is preserved
```

### Generating C/C++ Code

```python
from sympy.utilities.codegen import codegen
from sympy import symbols

x, y = symbols('x y')
expr = x**2 + y**2

# Generate C code
[(c_name, c_code), (h_name, h_header)] = codegen(
    ('distance_squared', expr),
    'C',
    header=False,
    empty=False
)

print(c_code)
# Outputs valid C function
```

### Generating Fortran Code

```python
from sympy.utilities.codegen import codegen

[(f_name, f_code), (h_name, h_interface)] = codegen(
    ('my_function', expr),
    'F95',  # Fortran 95
    header=False
)

print(f_code)
```

### Advanced Code Generation

```python
from sympy.utilities.codegen import CCodeGen, make_routine
from sympy import MatrixSymbol, Matrix

# Matrix operations
A = MatrixSymbol('A', 3, 3)
expr = A + A.T

# Create routine
routine = make_routine('matrix_sum', expr)

# Generate code
gen = CCodeGen()
code = gen.write([routine], prefix='my_module')
```

### Code Printers

```python
from sympy.printing.c import C99CodePrinter, C89CodePrinter
from sympy.printing.fortran import FCodePrinter
from sympy.printing.cxx import CXX11CodePrinter
expr = x**2 + y**2  # Scalar expression; matrix code needs explicit assignments

# C code
c_printer = C99CodePrinter()
c_code = c_printer.doprint(expr)

# Fortran code
f_printer = FCodePrinter()
f_code = f_printer.doprint(expr)

# C++ code
cxx_printer = CXX11CodePrinter()
cxx_code = cxx_printer.doprint(expr)
```

## Printing and Output Formats

### Pretty Printing

```python
from sympy import init_printing, pprint, pretty, symbols
from sympy import Integral, sqrt, pi

# Initialize pretty printing (for Jupyter notebooks and terminal)
init_printing()

x = symbols('x')
expr = Integral(sqrt(1/x), (x, 0, pi))

# Pretty print to terminal
pprint(expr)
#   π
#   ⌠
#   ⎮   1
#   ⎮  ───  dx
#   ⎮  √x
#   ⌡
#   0

# Get pretty string
s = pretty(expr)
print(s)
```

### LaTeX Output

```python
from sympy import latex, symbols, Integral, sin, sqrt, pi

x, y = symbols('x y')
expr = Integral(sin(x)**2, (x, 0, pi))

# Convert to LaTeX
latex_str = latex(expr)
print(latex_str)
# \int\limits_{0}^{\pi} \sin^{2}{\left(x \right)}\, dx

# Custom LaTeX formatting
latex_str = latex(expr, mode='equation')  # Wrapped in equation environment
latex_str = latex(expr, mode='inline')    # Inline math

# For matrices
from sympy import Matrix
M = Matrix([[1, 2], [3, 4]])
latex(M)  # \left[\begin{matrix}1 & 2\\3 & 4\end{matrix}\right]
```

### MathML Output

```python
from sympy.printing.mathml import mathml, print_mathml
from sympy import sin, pi

expr = sin(pi/4)

# Content MathML
mathml_str = mathml(expr)

# Presentation MathML
mathml_str = mathml(expr, printer='presentation')

# Print to console
print_mathml(expr)
```

### String Representations

```python
from sympy import symbols, sin, pi, srepr, sstr

x = symbols('x')
expr = sin(x)**2

# Standard string (what you see in Python)
str(expr)  # 'sin(x)**2'

# String representation (prettier)
sstr(expr)  # 'sin(x)**2'

# Reproducible representation
srepr(expr)  # "Pow(sin(Symbol('x')), Integer(2))"

# Trusted local round-trip only: sympify on a string can execute code
from sympy import sympify
restored = sympify(srepr(expr))
```

### Custom Printing

```python
from sympy.printing.str import StrPrinter

class MyPrinter(StrPrinter):
    def _print_Symbol(self, expr):
        return f"<{expr.name}>"

    def _print_Add(self, expr):
        return " PLUS ".join(self._print(arg) for arg in expr.args)

printer = MyPrinter()
x, y = symbols('x y')
print(printer.doprint(x + y))  # "<x> PLUS <y>"
```

## Python Code Generation

### autowrap - Compile and Import

Illustrative: compilation was not executed in this review. Install Cython and a C
compiler for `backend="cython"`; the f2py backend needs NumPy, a Fortran compiler,
and platform build dependencies. Source emission with `codegen` needs no compiler.

```python
from sympy.utilities.autowrap import autowrap
from sympy import symbols

x, y = symbols('x y')
expr = x**2 + y**2

# Automatically compile C code and create Python wrapper
f = autowrap(expr, backend='cython')
# or backend='f2py' for Fortran

# Use like a regular function
result = f(3, 4)  # 25
```

### ufuncify - Create NumPy ufuncs

Illustrative: native compilation was not executed. The default NumPy backend
requires NumPy headers and a C compiler. Other backends have different array
contracts; broadcasting here refers to the default NumPy ufunc.

```python
from sympy.utilities.autowrap import ufuncify
import numpy as np

x, y = symbols('x y')
expr = x**2 + y**2

# Create universal function
f = ufuncify((x, y), expr)

# Works with NumPy broadcasting
x_arr = np.array([1, 2, 3])
y_arr = np.array([4, 5, 6])
result = f(x_arr, y_arr)  # [17, 29, 45]
```

## Expression Tree Manipulation

### Walking Expression Trees

```python
from sympy import symbols, sin, cos, preorde

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

