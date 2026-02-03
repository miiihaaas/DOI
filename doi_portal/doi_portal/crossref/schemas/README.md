# Crossref XSD Schema Files

## Version: 5.4.0

This directory contains the Crossref Metadata Input Schema v5.4.0 and its dependencies,
bundled for local XSD validation without requiring network access.

## Schema Files

### Main Schema
- `crossref5.4.0.xsd` - Main Crossref deposit schema (v5.4.0)
- `common5.4.0.xsd` - Common type definitions
- `languages5.4.0.xsd` - Language code definitions
- `mediatypes5.4.0.xsd` - Media type definitions

### Crossref Extension Schemas
- `fundref.xsd` - FundRef (funding) data
- `fundingdata5.4.0.xsd` - Funding data v5.4.0
- `clinicaltrials.xsd` - Clinical trials metadata
- `AccessIndicators.xsd` - Access/license indicators
- `relations.xsd` - Relationship metadata

### External Dependencies (Local Stubs)
These are simplified stub schemas that allow Crossref schema loading
without network access to W3C/NCBI resources:

- `JATS-journalpublishing1-3d2-mathml3.xsd` - JATS driver (modified for local use)
- `JATS-journalpublishing1-3d2-mathml3-elements.xsd` - JATS element stubs
- `standard-modules/xml.xsd` - W3C XML namespace stub
- `standard-modules/xlink.xsd` - XLink namespace stub
- `standard-modules/module-ali.xsd` - NISO ALI namespace stub
- `standard-modules/mathml3/mathml3.xsd` - MathML 3.0 stub

## Source

Original schemas downloaded from:
- https://www.crossref.org/schemas/
- GitLab: https://gitlab.com/crossref/schema

## Usage

```python
from lxml import etree
from pathlib import Path

schema_path = Path(__file__).parent / "crossref5.4.0.xsd"
schema_doc = etree.parse(str(schema_path))
schema = etree.XMLSchema(schema_doc)

# Validate XML
xml_doc = etree.fromstring(xml_string.encode("utf-8"))
is_valid = schema.validate(xml_doc)
```

## Limitations

The local stub schemas provide minimal definitions for:
- JATS abstract/title elements
- MathML math element
- XLink attributes

Full JATS/MathML validation would require complete schemas from
NCBI (JATS) and W3C (MathML). For DOI Portal purposes, the main
Crossref structure validation is sufficient.

## Last Updated

2026-02-03 (Story 5.4: XSD Validation)
