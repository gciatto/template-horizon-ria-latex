PYTHON ?= python3
# Unspecified funding means standard RIA. An empty PAGE_LIMIT uses metadata.tex
# and the selected profile's default.
# Overrides affect both PDFs and their checks.
FUNDING ?= standard
PAGE_LIMIT ?=
VERSION ?=
export FUNDING PAGE_LIMIT VERSION

.PHONY: all guidance submission b2 counts pages chars check test dist clean distclean help

all: guidance submission

guidance:
	$(PYTHON) scripts/build.py guidance

submission:
	$(PYTHON) scripts/build.py submission

b2: submission

counts: submission
	$(PYTHON) scripts/count_pdf.py build/submission/part-b2.pdf --json build/counts.json

pages chars: counts

check: submission
	$(PYTHON) scripts/count_pdf.py build/submission/part-b2.pdf --check --json build/counts.json

test:
	$(PYTHON) -m unittest discover -s tests -v

dist: all check test
	$(PYTHON) scripts/package.py --require-pdfs

clean:
	$(PYTHON) -c "import shutil; shutil.rmtree('build', ignore_errors=True)"

distclean: clean
	$(PYTHON) -c "import shutil; shutil.rmtree('dist', ignore_errors=True)"

help:
	@echo "make                 Build guidance and submission PDFs"
	@echo "make guidance        Build the template with coloured guidance"
	@echo "make submission      Build without guidance"
	@echo "make pages / chars   Report whole-PDF pages and extracted text counts"
	@echo "make check           Enforce page cap, A4 size and guidance off"
	@echo "make test            Test PDF layout, guidance, counts and packaging"
	@echo "make dist            Validate, then package source ZIP and both PDFs"
	@echo "make FUNDING=lump-sum  Use the metadata lump-sum page limit"
	@echo "make PAGE_LIMIT=30     Override a call-specific cap everywhere"
	@echo "make dist VERSION=2026.11.25-14-07  Set an explicit UTC release version"
