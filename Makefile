.PHONY: help deps lint check-urls check-render check-render-record verify

help:
	@echo "Targets:"
	@echo "  deps                 Install the Ansible collections this repo depends on"
	@echo "  lint                 Run ansible-lint against the production profile"
	@echo "  check-urls           Resolve every composed download URL in role defaults"
	@echo "  check-render         Compare rendered configuration to the recorded expectations"
	@echo "  check-render-record  Re-record those expectations after an intended change"
	@echo "  verify               lint + check-urls + check-render"

deps:
	ansible-galaxy collection install -r requirements.yml

lint:
	ansible-lint

# Catches a version variable and its URL template disagreeing about a tag
# prefix — a defect ansible-lint cannot see, since the YAML is valid either way.
check-urls:
	ansible-playbook tests/check-download-urls.yml

# Renders role templates against fixture inventories and compares the result to
# recorded expectations. Catches string-level defects in generated configuration
# — quoting, escaping, list joining, ordering, single-node versus cluster shape
# — which ansible-lint cannot see, because the YAML is valid either way.
#
# One ansible-playbook process per fixture, so no fixture can inherit another's
# variables through include_vars.
check-render:
	@set -e; \
	for fixture in tests/render/fixtures/*/; do \
		name=$$(basename "$$fixture"); \
		echo "== render fixture: $$name"; \
		ansible-playbook -i "$$fixture/hosts.yml" tests/check-rendered-config.yml -e "fixture=$$name"; \
	done

# Rewrites the expectations from what the roles currently render. Deliberately a
# separate target: an expectation that updated itself would make the check
# self-confirming, so re-recording is something a person chooses and a reviewer
# sees in the diff.
check-render-record:
	@set -e; \
	for fixture in tests/render/fixtures/*/; do \
		name=$$(basename "$$fixture"); \
		echo "== recording fixture: $$name"; \
		ansible-playbook -i "$$fixture/hosts.yml" tests/check-rendered-config.yml -e "fixture=$$name" -e render_record=true; \
	done

verify: lint check-urls check-render
