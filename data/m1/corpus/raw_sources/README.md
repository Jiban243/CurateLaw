# Raw document manifest, not document bytes

Every `.url` shortcut points to an original publicly accessible source as verified on **2026-11-08**. Original third-party PDFs/DOCX files have **not** been embedded in this ZIP because this execution environment could not fetch binary files and reuse permissions have not been confirmed. This means the *original-document acquisition* acceptance criterion remains open.

To acquire research copies on a machine with internet access, run from the package root:

```bash
python tools/fetch_sources.py --allow-uncleared
```

This is a conscious acknowledgement of the unknown permissions and for personal research acquisition only. Do **not** add originals to a public repository, redistribute them, or feed them verbatim into model training until the licence of each source is checked. Hashes for actually downloaded files will be recorded in `raw_sources/download_log.json`.

DOCX links may require login or may have moved; URLs are retained for provenance.
