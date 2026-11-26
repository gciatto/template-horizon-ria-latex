PYTHON ?= python3
# Unspecified funding means standard RIA. An empty PAGE_LIMIT uses metadata.sty
# and the selected profile's default.
# FUNDING affects both parts. PAGE_LIMIT applies only to Part B.
FUNDING ?= standard
PAGE_LIMIT ?=
VERSION ?=
BUDGET_XLSX ?= $(wildcard budget.xlsx)
export FUNDING PAGE_LIMIT VERSION BUDGET_XLSX

.PHONY: all guidance submission guidance-a guidance-b submission-a submission-b \
        a part-a b part-b counts pages chars check check-admin check-budget \
        strict test ci dist clean distclean help budget-tables budget-sync

all: guidance submission

guidance: guidance-a guidance-b

submission: submission-a submission-b

guidance-a:
	$(PYTHON) scripts/build.py guidance --document part-a

guidance-b:
	$(PYTHON) scripts/build.py guidance --document part-b

submission-a:
	$(PYTHON) scripts/build.py submission --document part-a

submission-b:
	$(PYTHON) scripts/build.py submission --document part-b

a part-a: guidance-a submission-a

b part-b: guidance-b submission-b

counts: submission
	$(PYTHON) scripts/count_pdf.py build/submission/part-a.pdf --json build/part-a-counts.json
	$(PYTHON) scripts/count_pdf.py build/submission/part-b.pdf --json build/counts.json

pages: counts

chars: counts check-admin

check-admin:
	$(PYTHON) scripts/check_admin.py --json build/admin-checks.json

check-budget:
	$(PYTHON) scripts/check_budget.py --json build/budget-checks.json

budget-tables:
	$(PYTHON) scripts/budget_excel.py "$(BUDGET_XLSX)" --output build/excel-budget

budget-sync:
	$(PYTHON) scripts/budget_workbook.py "$(BUDGET_XLSX)"

check: check-admin check-budget submission
	$(PYTHON) scripts/count_pdf.py build/submission/part-a.pdf --check --json build/part-a-counts.json
	$(PYTHON) scripts/count_pdf.py build/submission/part-b.pdf --check --json build/counts.json

# Completeness is a separate author-requested check, never a blank-template CI gate.
strict: check
	$(PYTHON) scripts/check_admin.py --strict --json build/admin-strict-checks.json
	$(PYTHON) scripts/check_budget.py --strict --json build/budget-strict-checks.json

test:
	$(PYTHON) -m unittest discover -s tests -v

ci:
	$(PYTHON) scripts/ci.py run

dist: all check test
	$(PYTHON) scripts/package.py --require-pdfs

clean:
	$(PYTHON) -c "import shutil; shutil.rmtree('build', ignore_errors=True)"

distclean: clean
	$(PYTHON) -c "import shutil; shutil.rmtree('dist', ignore_errors=True)"

help:
	@echo "make                 Build Part A and B, each with and without guidance"
	@echo "make a / b           Build both modes of the selected part"
	@echo "make guidance        Build both parts with coloured guidance"
	@echo "make submission      Build both parts without guidance"
	@echo "make pages / chars   Report PDF counts / source-field character checks"
	@echo "make check           Check fields, budgets, A4 pages and the Part B cap"
	@echo "make check-admin     Check Part A field types, lengths and partner records"
	@echo "make check-budget    Check partner budgets and consortium totals"
	@echo "make BUDGET_XLSX=budget.xlsx  Read Excel budgets and staff effort for both parts"
	@echo "make budget-tables BUDGET_XLSX=budget.xlsx  Export standalone LaTeX tables"
	@echo "make budget-sync     Rebuild Excel summaries after changing work packages"
	@echo "make strict          Also require completed administrative/budget fields"
	@echo "make test            Run layout, validation, build and packaging tests"
	@echo "make ci              Run every CI check, with logs and a Markdown summary"
	@echo "make dist            Validate, then package source, four PDFs and reports"
	@echo "make FUNDING=lump-sum  Select lump-sum rules and the 45-page Part B cap"
	@echo "make PAGE_LIMIT=30     Override a call-specific Part B page cap"
	@echo "make dist VERSION=2026.11.25-14-07  Set an explicit UTC release version"
