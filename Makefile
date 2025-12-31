.PHONY: help init update export serve build clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

init: ## Initialize git submodules
	git submodule update --init --recursive

update: ## Update content submodule to latest main
	cd content && git pull origin main && cd ..

export: ## Export published content from notes to site-content
	python3 scripts/export_content.py

serve: export ## Run local Hugo server with draft content
	hugo server -D

build: export ## Build the static site for production
	bash scripts/build.sh

clean: ## Remove generated files
	rm -rf public/ site-content/

sync: update export ## Update content and export in one step
	@echo "Content updated and exported"
