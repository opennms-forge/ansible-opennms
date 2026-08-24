.PHONY: help deps lint check-urls verify

help:
	@echo "Targets:"
	@echo "  deps        Install the Ansible collections this repo depends on"
	@echo "  lint        Run ansible-lint against the production profile"
	@echo "  check-urls  Resolve every composed download URL in role defaults"
	@echo "  verify      lint + check-urls"

deps:
	ansible-galaxy collection install -r requirements.yml

lint:
	ansible-lint

# Catches a version variable and its URL template disagreeing about a tag
# prefix — a defect ansible-lint cannot see, since the YAML is valid either way.
check-urls:
	ansible-playbook tests/check-download-urls.yml

verify: lint check-urls
