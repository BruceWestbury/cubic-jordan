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

Schema and Convention Audit

### 1. Certificate top-level keys — **identical**

Both: `format`, `version`, `source`, `relation`, `initial`, `steps`, `final`, `source_key`

---

### 2. `source` object — **one semantic difference**

| field | F4 | E6 |
|-------|----|----|
| `graph` | open DartGraph | open DartGraph |
| `site` | `[int, int, int, int]` (length 4) | `[int, int, int, int, int]` (length 5) |

**Site length differs** (4-valent vs 5-valent theory). Same element type `int` in both. No `null` entries in either. Lean can read `site.length` to know the theory, or dispatch on the `theory` field from the index.

---

### 3. Open DartGraph schema (`source.graph`) — **identical**

Keys: `format`, `version`, `num_darts`, `num_vertices`, `num_boundary`, `darts`, `vertices`, `vertex_of`, `partner`, `boundary`

- `format` = `"dart_graph"` in both
- `darts`: `list[int]` — dart labels, **not necessarily 0…N−1**
- `vertices`: `list[int]`
- `vertex_of`: `dict[str → int]` — keys are stringified dart labels
- `partner`: `dict[str → int|null]` — `null` for boundary (site) darts, `int` for paired darts
- `boundary`: `list[int]` — ordered boundary dart labels

---

### 4. Closed DartGraph (`initial`/`final`/`step.after` terms) — **identical schema, non-contiguous dart labels**

Keys: `format`, `version`, `num_darts`, `num_vertices`, `num_boundary`, `darts`, `vertices`, `vertex_of`, `partner`  *(no `boundary` key)*

- `format` = `"closed_dart_graph"` in both
- `partner`: `dict[str → int]` only — **no `null` values** (closed graph, no boundary)
- **`darts` are NOT guaranteed to be `0…N−1`** in either theory. This appears from the first reduction step onward as dart labels accumulate from surgery. Lean must index darts via the `darts` list, not by assuming a range.

---

### 5. LC term schema — **identical**

```
{"coefficient": {"coefficients": [str, ...]},
 "graph":       {<DartGraph>},
 "metadata":    {"key": str}}
```

Coefficients are always strings (Sage rationals like `"-1/2"` are not JSON numbers). Constants are `"0"`, `"-2"`, etc. — no variable appears. The variable name only appears inside non-trivial polynomial coefficients and in rule strings.

---

### 6. Reduction step schema — **identical**

Keys: `term_index` (int), `rule` (str), `occurrence` (dict), `after` (dict)

---

### 7. Occurrence schema — **identical**

```json
{"dart_map": [[int, int], ...]}
```

Each pair is `[pattern_dart, host_dart]`. Both entries are `int` in both theories.

---

### 8. `rule` string — **same format, different variable name**

Both are Python `repr()` of a `rule_key` tuple:

```
"(<lhs_graph6_key>, ((<rhs_graph6_key>, '<coeff_str>'), ...))"
```

| | F4 | E6 |
|-|----|----|
| polynomial variable in coeff strings | `n` | `nn` |
| example | `"... '-1/2*n + 1' ..."` | `"... '6*nn + 18' ..."` |

Lean should parse rule coefficients using the variable name implied by `theory`. The rule string is a lookup key, not trusted mathematical data.

---

### 9. `source_relation_index.json` — **identical schema**

Top-level keys: `format`, `version`, `theory`, `t`, `sources`

| field | type | note |
|-------|------|------|
| `format` | `str` | `"source_closed_relation_index"` |
| `version` | `int` | `1` |
| `theory` | `str` | `"f4"` or `"e6"` — dispatch key |
| `t` | `int` | vertex count |
| `sources` | `list[object]` | ordered by certificate file |

Per-source record: `source_key` (str), `certificate` (str), `steps` (int), `relation` (list)

`relation` entries: `[closed_graph_key: str, {"coefficients": [str]}]`

---

### Summary: what Lean needs to handle polymorphically

| item | handled by |
|------|-----------|
| Site length 4 vs 5 | `theory` field or `site.length` |
| Variable name `n` vs `nn` in rule/coefficient strings | `theory` field |
| Non-contiguous dart labels | Always index darts via `darts` list; never assume `0…N−1` |
| `partner` nullable | Only for open DartGraphs (`format = "dart_graph"`); never for closed |
| Polynomial coefficients are strings, not numbers | Parse as rational strings in all cases |

Everything else is structurally identical and a single Lean reader handles both without branching.
