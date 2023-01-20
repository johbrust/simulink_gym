test:
	TERM=unknown pytest --cov-report term-missing --cov-report lcov --cov=simulink_gym tests/ -vv
test-html:
	TERM=unknown pytest --cov-report html:cov_html --cov=simulink_gym tests/
test-no-cov:
	TERM=unknown pytest tests/ -vv
lint:
	ruff .
format-check:
	black --check .
format:
	black .