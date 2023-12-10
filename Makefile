lint:
	djlint . --lint
	djlint . --reformat --format-css --format-js
	echo line-length = 120 > ruff.toml
	ruff check .
	ruff format .
	echo { "extends": ["stylelint-config-standard"] } > .stylelintrc.json
	npx stylelint "**/*.css"
	yamllint -d "{extends: relaxed, rules: {new-lines: {type: platform}}}" ./.github/workflows/
	npx eslint .

test:
	pdm run python -m coverage run -m unittest discover tests


test-coverage:
	pdm run python -m coverage report --format="markdown"