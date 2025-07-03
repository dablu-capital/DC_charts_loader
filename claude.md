# Bash commands
- use gh cli for all github related commands

# Code style
## Formatting
use PEP 8 guidelines (source: https://peps.python.org/pep-0008/)
## Naming conventions

local variables: snake_case
```python
bb_period = 10
```
global variables: UPPPER_SNAKE_CASE
```python
INITIAL_CAPITAL = 100_000
```
function methods: snake_case
```python
def my_function()
```
classes: PascalCase
```python
class MyCustomClass()
```
## Testing
tests will be run using pytest. use the following command for complete test
```bash
python -m pytest --cov 
```

# Workflow (MODIFY)
- Be sure to typecheck when you’re done making a series of code changes
- Prefer running single tests, and not the whole test suite, for performance