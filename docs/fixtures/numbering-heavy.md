# Fixture Spec: numbering-heavy

## Purpose
Test multilevel numbering and list restart behavior.

## Required elements
- section numbering: 1 / 1.1 / 1.1.1
- nested ordered lists
- unordered list nested under ordered list
- restarted numbering block
- prose between numbered blocks

## Evaluation focus
- numbering continuity
- hierarchy preservation
- restart correctness
- nested list shape

## Failure examples
- flattened numbering
- restarted lists continuing from prior values
- hierarchy collapse
- mixed list bullets becoming numbers or vice versa
