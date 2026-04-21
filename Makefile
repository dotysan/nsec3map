#! /usr/bin/env -S make -f

PY := 3.14.4
VB := .venv/bin
UV_BIN := $(shell command -v uv 2>/dev/null)

$(VB)/n3map: $(VB)/activate
	@uv pip install --editable .[predict]

.PHONY: tests
tests: $(VB)/pytest
	@uv run pytest --cov

$(VB)/pytest: $(VB)/activate
	@uv pip install .[test]

$(VB)/activate: |uv
	@uv venv --managed-python --python=$(PY)

.PHONY: uv
uv:
ifeq ($(UV_BIN),)
	curl --location https://doty.org/gist/uv-install |bash
endif

.PHONY: clean
clean:
	rm --recursive --force .venv build n3map.egg-info
	find n3map -type d -name __pycache__ -print0 \
	    |xargs -r0 rm --force --recursive
	find n3map -type f -name '*.so' -delete
