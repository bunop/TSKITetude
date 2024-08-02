
# Build the documentation

## Build the documentation with `jupyter-book`

Inside a *poetry shell* or using the `poetry run` command, you can build the
documentation with:

```bash
poetry run jupyter-book build docs/
```

## Clean up the documentation build

To clean up *all* the documentation build, you can use:

```bash
poetry run jupyter-book clean --all docs/
```

* `--all` will remove the `_build` directory and the `.jupyter_cache` directory.

In alternative, you can remove the `html` or `latex` build directories with
these options:

* `--html` will remove the `html` directory only.
* `--latex` will remove the `latex` directory only.

## Publish the documentation on GH pages

After a successful build, you can publish the documentation on GitHub pages
using `ghp-import` and by selecting the `html` build directory:

```bash
poetry run ghp-import -n -p -f docs/_build/html
```

* `-n` Include a `.nojekyll` file in the branch.
* `-p` Push the branch to origin/{branch} after committing.
* `-f` Force the push.
