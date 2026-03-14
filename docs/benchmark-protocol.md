# Benchmark Protocol v1

## Goal
Compare candidate conversion routes using the same fixture set, scoring rubric, and output packaging rules.

## Candidate classes
- Hancom native workflow
- Microsoft HWP converter
- web converter services
- LibreOffice import-based route
- Pandoc-based route
- hwp-parser route
- pypandoc-hwpx route
- openhwp-based route
- SHawn-hwp route

## Required benchmark metadata
For every run, record:
- candidate name
- candidate version or commit
- source fixture
- source format
- target format
- route description
- execution date
- operator notes

## Required outputs
Store for each run:
- converted file
- round-trip file if applicable
- QA report (markdown or json)
- summary score
- risk notes

## Minimum benchmark loop
1. select fixture
2. convert source -> target
3. inspect output
4. score with rubric
5. if route is bidirectional, convert back
6. score round-trip stability
7. record risks and notes

## v1 scoring dimensions
- text preservation
- structure preservation
- table preservation
- image/caption preservation
- footnote/numbering preservation
- submission suitability
- round-trip stability

## Decision rule
A route is considered practically superior only if it improves either:
- overall score, or
- submission suitability, or
- loss explainability

without introducing unacceptable regressions in text retention.
