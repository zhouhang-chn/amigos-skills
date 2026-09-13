# git

The pre-commit hook is **generated**, not shipped from this directory:

```bash
amigos hooks install     # writes .git/hooks/pre-commit
amigos hooks status
amigos hooks uninstall
```

Installation resolves the Python interpreter and the package location and bakes
them into the hook, so it works in a repository that is not the amigos-skills
checkout and does not depend on `amigos` being on `PATH`:

```python
#!/path/to/python
# installed by amigos-skills
import sys
sys.path.insert(0, "/path/to/amigos/src")
from amigos.cli import main
sys.exit(main(["gate", "--staged"]))
```

Installation refuses to overwrite a pre-commit hook amigos did not write, and
uninstall refuses to remove one. Pass `--force` to replace it deliberately.

There is deliberately no copy of the hook kept here to be edited by hand. Two
copies of one rule drift.
