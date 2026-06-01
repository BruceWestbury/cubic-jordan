# Certificate Format

## Goal

The repository cubic-jordan implements a calculation with graphs. The goal is to write json to files which will be read by the certificates repository to generate a Lean 4 certificate of these calculations.

The repository cubic-jordan depends on trivalent-graphs. The repository trivalent-graphs implements the graph data structures and operations used in cubic-jordan. There are two theories used in cubic-jordan, F4_series and E6_series.

The calculations consist of a sequence of reduction steps performed on linear combinations of graphs. The role of Lean is very limited. Each json file has an initial relation and a sequence of reduction steps. The certificates repository will use Lean to verify the correctness of each step.

The structures in Lean are:

- `ClosedGraph`: the graphs being reduced
- `OpenGraph`: the graphs in reduction rules
- `Occurrence`: where an OpenGraph appears in the ClosedGraph

In cubic-jordan a reduction step consists of taking a linear combination of DartGraphs, a reduction rule, and an occurrence of the LHS of the rule in one of the terms of the linear combination. The result is a new linear combination with the LHS substituted by the RHS of the rule.

The role of Lean is not to perform the substitutions; just to verify them. In cubic-jordan a reduction rule has a LHS which is a `DartGraph` and the replacement which is a linear combination of `DartGraphs`. In the certificate, the LHS is an `OpenGraph` and the replacement is a linear combination of `OpenGraphs`. These are fixed in each calculation and have been written.

The first step is to take a linear combination of `DartGraphs` with empty boundary and write to a json file so that Lean can read this as a linear combination of `ClosedGraphs`.

The core operation in trivalent-graphs is to replace an occurrence of a pattern in a host by another pattern with the same boundary. In the certificate, the information needed to verify this is the before occurrence and the after occurrence.

There should be a json file for each source. The initial linear combination is obtained by substituting a relation (six-term or seven-term)into the source graph. Subsequently, each before linear combination is the previous after linear combination. This means that the json schema should be:

{
  "term_index": 0,
  "rule": "rule_name",
  "before_occurrence": {...},
  "after_occurrences": [...],
  "after": {...}
}

For both the F4 and the E6 theories the base ring is the polynomial ring in one variable with rational coefficients. These should be written to the json file as dense polynomials (so the sequence of coefficients).

A `DartGraph` with empty boundary is written to json in cubic-jordan. Later it will be read in certificates as a `ClosedGraph`. Lean does not use the canonical form (as this is not needed for certificate verification). Therefore, the json schema should not assume darts or vertices are numbered sequentially. Here is the schema

{
  "format": "closed_graph",
  "version": 1,
  "darts": [0, 1, 2, 3, 4, 5],
  "vertices": [0, 1],
  "vertex_of": {
    "0": 0,
    "1": 0,
    "2": 0,
    "3": 1,
    "4": 1,
    "5": 1
  },
  "partner": {
    "0": 3,
    "1": 4,
    "2": 5,
    "3": 0,
    "4": 1,
    "5": 2
  }
}

The evaluations of closed graphs are already cached in json files. The sequence of reductions ends with a linear combination of closed graphs. The final step is to take the canonical form of each closed graph and read its evaluation from the cache.

Do not invent mathematics.

## Version 1 scope

Version 1 certifies the reduction trace only.

Included:
- initial linear combination of closed DartGraphs
- reduction steps
- final linear combination of closed DartGraphs

Excluded:
- verification of source expansion
- verification of canonicalisation
- verification of evaluation cache lookup

Those may be added later.
