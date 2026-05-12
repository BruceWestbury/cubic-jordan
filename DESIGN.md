# DESIGN.md

## Overview

This repository contains a public, reproducible, static-web presentation of the F4 and E6 trivalent graph computations.

The project has two aims:

1. provide a clean implementation of the computations independent of SageMath;
2. provide a static website which allows the computations to be explored step-by-step.

The repository is not intended to replace the original research codebase. The original SageMath project remains the primary environment for experimentation and development. This repository instead provides:

- cached graph data;
- cached reductions and evaluations;
- lightweight symbolic algebra using SymPy;
- rendering and visualisation;
- a browser-based presentation layer.

The emphasis is on transparency, reproducibility, and inspectability.

---

# High-Level Structure

The repository is organised as:

```text
trivalent-graphs/
  src/trivalent_graphs/     # shared engine
  projects/f4/              # F4-specific data and configuration
  projects/e6/              # E6-specific data and configuration
  web/                      # static website
  tests/
```

Conceptually there are two mathematical projects sharing a common computational framework.

The shared engine contains:

- DartGraph data structures;
- reduction machinery;
- symbolic linear combinations;
- rendering;
- trace generation;
- export utilities.

The individual projects contain:

- cached graphs;
- defining relations;
- reduction rules;
- cached evaluations;
- cached reduction traces.

---

# Mathematical Model

Each project is represented by a configuration object:

```python
@dataclass
class Project:
    name: str
    variable_name: str
    loop_value: Expr
    rules: list[ReductionRule]
    relation: LinearCombination
    closed_values: dict[DartGraph, Expr]
```

The shared engine should not contain any F4- or E6-specific logic.

Internally the polynomial variables should be distinct:

```text
n_f4
n_e6
```

even though both are displayed publicly as `n`.

---

# Base Ring

Both projects use a polynomial ring:

```text
Q[n]
```

implemented using SymPy.

The symbolic algebra requirements are intentionally modest:

- symbolic coefficients;
- simplification;
- substitution;
- factorisation;
- polynomial equality testing.

The project does not attempt to reproduce SageMath’s full algebra system.

---

# Graph Representation

Graphs are stored and cached as DartGraphs.

The public repository should not depend on runtime graph generation.

Instead, graph generation is performed offline in the research codebase and exported into cached files.

The canonical representation is therefore:

```text
cached canonical DartGraphs
```

rather than Sage graphs.

---

# Cached Data

The repository stores several kinds of cached data.

## Cached Graphs

```text
projects/f4/cache/graphs/
projects/e6/cache/graphs/
```

Examples:

```text
closed_cubic_girth5_t10.json
closed_cubic_girth5_t12.json
closed_cubic_girth5_t14.json
closed_cubic_girth5_t16.json
```

These contain canonical DartGraphs and metadata.

## Cached Evaluations

```text
projects/f4/cache/evaluations/
projects/e6/cache/evaluations/
```

These store evaluations of closed graphs obtained during the computation.

## Cached Reduction Traces

```text
projects/f4/cache/reduction_traces/
projects/e6/cache/reduction_traces/
```

These contain step-by-step reductions intended for visualisation on the website.

---

# Rules and Relations

Each project contains:

- a short list of reduction rules;
- one distinguished relation.

These should be defined as explicit project-level global data.

For example:

```python
rules = [
    lollipop_rule,
    bigon_rule,
    triangle_rule,
    square_rule,
]

relation = six_term_relation
```

The reduction engine operates entirely from these definitions.

---

# Closed Graph Evaluations

Closed graph evaluations are considered part of the computation itself.

They should therefore be cached explicitly rather than recomputed dynamically.

Example:

```json
{
  "graph": "g16_023",
  "value": "n**2 - 4*n + 2",
  "method": "singleton_relation"
}
```

Cached evaluations form part of the reproducible computational record.

---

# Reduction Engine

The key missing component is a reduction engine capable of producing a full trace suitable for visualisation.

The core interface should look like:

```python
def reduce_element_with_trace(element, presentation):
    ...
```

This returns:

```python
(final_result, trace)
```

where `trace` is a sequence of reduction steps.

---

# Reduction Steps

A reduction step records:

- the current expression;
- the chosen occurrence;
- the applied rule;
- the replacement;
- the resulting expression.

Suggested structure:

```python
@dataclass
class ReductionStep:
    before: LinearCombination
    rule_name: str
    occurrence: Occurrence
    host_graph: DartGraph
    lhs_graph: DartGraph
    replacement: LinearCombination
    after: LinearCombination
```

The reduction trace is intended both for debugging and for public presentation.

---

# Visualisation

Visualisation is a primary goal of the repository.

Each reduction step should be renderable as:

- the original graph;
- the highlighted occurrence;
- the applied rule;
- the resulting graph(s).

The renderer should support:

- SVG for the website;
- TikZ export for papers;
- possibly Typst/Cetz export later.

The website renderer should use SVG rather than TikZ.

---

# Static Website

The website is intended to be fully static.

No server-side computation should be required.

The website consumes cached JSON data generated offline.

Possible pages:

```text
/
  Overview

/f4
/e6

/f4/graphs
/f4/relations
/f4/evaluations
/f4/reductions

/e6/...
```

The website should allow:

- browsing graphs;
- browsing relations;
- stepping through reductions;
- viewing evaluations;
- inspecting dependency chains.

---

# Reduction Trace Format

Reduction traces should be exportable to JSON.

Example:

```json
{
  "project": "f4",
  "input": "g16_023",
  "steps": [
    {
      "rule": "square",
      "host": "g16_023",
      "occurrence": {
        "vertices": [1, 5, 6, 9]
      },
      "before": [["1", "g16_023"]],
      "after": [["n - 2", "g14_004"]]
    }
  ]
}
```

These traces form the basis of the interactive website.

---

# Separation of Responsibilities

The repository intentionally separates:

## Research Code

Experimental SageMath computations.

## Public Computational Record

Cached graphs, reductions, and evaluations.

## Presentation Layer

Static visualisation and browsing.

---

# Validation

The repository should contain regression tests checking:

- graph counts;
- canonicalisation;
- cached evaluations;
- relation consistency;
- agreement with SageMath computations.

Important benchmark counts include:

```text
t = 10: 1
t = 12: 2
t = 14: 9
t = 16: 49
```

for connected simple cubic girth ≥ 5 graphs.

---

# Milestones

## Milestone 1

Create repository structure.

## Milestone 2

Export cached DartGraphs from the research codebase.

## Milestone 3

Implement lightweight SymPy algebra layer.

## Milestone 4

Implement reduction tracing.

## Milestone 5

Implement SVG rendering.

## Milestone 6

Export cached F4 reductions and evaluations.

## Milestone 7

Export cached E6 reductions and evaluations.

## Milestone 8

Build static website.

## Milestone 9

Integrate TikZ export for papers.

## Milestone 10

Publish reproducible computational record.

---

# Design Principles

The repository should prioritise:

- transparency;
- reproducibility;
- inspectability;
- simplicity;
- stable cached data;
- separation of computation and presentation.

The public website should not merely display final answers.

It should expose the computations themselves.