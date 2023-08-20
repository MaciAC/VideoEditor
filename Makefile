##@ Label sections
.PHONY: help
help:  ## Display this help
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

##@ Build commands
.PHONY: lint
lint: # run linters and commit
	black .
	poetry run isort .
	git commit -am 'run linters'
