.DEFAULT_GOAL := help

UV ?= uv
PYTEST_ARGS ?=
UV_EXPORT_ARGS := --frozen --no-dev --no-emit-project --no-hashes --output-file=requirements.txt --quiet

.PHONY: check clean help lint lock lock-check package package-check package-distribution package-upload requirements requirements-check sync sync-runtime test upgrade

lock:  ## Update the lockfile without upgrading locked dependencies
	$(UV) lock

lock-check:  ## Verify that the lockfile is up to date
	$(UV) lock --check

upgrade:  ## Upgrade all locked dependencies
	$(UV) lock --upgrade

requirements:  ## Regenerate requirements.txt from uv.lock
	$(UV) export $(UV_EXPORT_ARGS)

requirements-check: requirements  ## Verify that requirements.txt matches uv.lock
	@git diff --exit-code -- requirements.txt || { \
		echo "requirements.txt is out of date; run 'make requirements' and commit the result." >&2; \
		exit 1; \
	}

sync:  ## Sync the project and development dependencies
	$(UV) sync --locked

sync-runtime:  ## Sync only the project and runtime dependencies
	$(UV) sync --locked --no-dev

lint:  ## Run all pre-commit checks
	$(UV) run --locked pre-commit run --all-files --show-diff-on-failure

check: lock-check lint  ## Verify the lockfile and run all checks

test:  ## Run the test suite; pass options with PYTEST_ARGS
	$(UV) run --locked pytest $(PYTEST_ARGS)

package-distribution: clean  ## Create distribution packages
	$(UV) build

package-check: package-distribution  ## Check the distribution is valid
	$(UV) tool run twine check --strict dist/*

package-upload: package-check  ## Upload distribution packages
	$(UV) tool run twine upload dist/* --repository-url https://upload.pypi.org/legacy/

package: package-upload

clean:  ## Clean the package directory
	rm -rf fixity.egg-info/
	rm -rf build/
	rm -rf dist/

help:  ## Print this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
