# Unblob report handling

These commands and fields target **26.6.4**. Check `unblob --version` and
`unblob --help` when using another release; website examples may describe an older
schema or call `-n` by the older `--entropy-depth` name.

## Installation and dependencies

Follow the [upstream installation guide](https://unblob.org/installation/) for
your environment. For an existing Linux analysis environment with pipx:

```bash
pipx install 'unblob==26.6.4'
unblob --show-external-dependencies
```

Install the external extractors needed for the image using the upstream guide.
The dependency check can return nonzero for tools unrelated to a particular
image. Record relevant missing tools and inspect extraction errors; do not treat
partial dependency availability as full format coverage. The bundled summary
helper itself uses only Python's standard library and does not import unblob.

## Schema and interpretation

The JSON report is a list of task results, each with `task`, `reports` and
`subtasks`. `task.path` is the source, `task.depth` is the processing depth, and
`blob_id` connects subtasks to a chunk or multi-file report's `id`. Older reports
used `chunk_id`; the helper accepts that link spelling as well.

| Report | Meaning |
| --- | --- |
| `StatReport`, `HashReport`, `FileMagicReport` | File properties, hashes and libmagic identification. A file type does not imply extractable content. |
| `ChunkReport` | Recognized format, start/end offsets, size, encryption flag and nested `extraction_reports`. Padding uses `handler_name: "padding"`. |
| `UnknownChunkReport` | Unrecognized region with optional `randomness`. Keep the original source and bounds. |
| `RandomnessReport` | Statistics for an entire file with no recognized chunks. This can occur without an `UnknownChunkReport`. |
| `CarveDirectoryReport` | Actual directory containing carved components. |
| `MultiFileReport` | A handler's group of input files; inspect its own extraction reports and output subtasks. |
| Reports carrying `severity`, `problem`, or an unrecognized type | Surface for review, including nested errors, warnings and extraction adjustments. |

`end_offset` is exclusive. For a region `[start_offset, end_offset)`, length is
`end_offset - start_offset`. Offsets apply to `task.path`, including when that is
an already decompressed file. The summary records links to output paths rather
than inferring a physical address through transformed content.

Unblob normalizes Shannon entropy to 0–100 percent. `mean` is weighted by bytes;
`percentages` contains per-block samples with `block_size` in bytes. The helper
keeps the mean, extrema and block size and omits the arrays. Chi-square values
are also percentages and are not an encryption confidence score. An absent
randomness report remains null.

The report alone does not record every reason processing stopped. In 26.6.4,
reaching the depth limit can leave just a `StatReport`, and magic/extension skip
rules can leave metadata without chunks. Pass the exact `-d` value as the
helper's `--extract-depth`; it flags matching tasks without inventing a successful
extraction or a diagnosis for unclassified files. Inspect the log for skip reasons.

## Keep agent input small

The helper prints JSON with aggregate counts and independently paginated sections.
`--limit` defaults to 10, `--offset` defaults to 0, and `--path` filters by source
path substring. Each section reports its total, matched and omitted counts.
Issue pages are independent of file pages, so a large file inventory does not
displace an extraction error. Long strings and lists are clipped explicitly;
JSON pointers identify where to inspect the full original value.

```bash
python3 "$SKILL_DIR/scripts/summarize_unblob.py" "$RUN_DIR/report.json" \
  --extract-depth 10 --path nested.tar --limit 10
```

The helper does not execute extractors, open extracted paths, decode archive
contents, or declare overall extraction success. It reads the report into memory;
bounded output reduces agent context, not the report's disk or parsing cost.
If a schema or JSON error is reported, inspect the tool version and raw report.
Retain error evidence even when unblob exits zero. In 26.6.4, command failure
`stdout`/`stderr` fields are base64; inspect them only for the selected error rather
than dumping every log into the agent context.

## Source references

- [Tagged CLI](https://github.com/onekey-sec/unblob/blob/26.6.4/python/unblob/cli.py)
- [Report types](https://github.com/onekey-sec/unblob/blob/26.6.4/python/unblob/report.py)
- [Task links and exclusive chunk bounds](https://github.com/onekey-sec/unblob/blob/26.6.4/python/unblob/models.py)
- [Recursion, skip conditions and randomness calculation](https://github.com/onekey-sec/unblob/blob/26.6.4/python/unblob/processing.py)
