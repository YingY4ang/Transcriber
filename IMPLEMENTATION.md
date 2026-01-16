# Consultation Artifact System

Complete implementation of single-pass AI extraction with deterministic automation.

## Quick Start

### Run Tests

```bash
python test_consultation_system.py
```

This will validate:
- Prompt generation
- Bedrock request structure
- Artifact schema compliance
- PDF generation
- DynamoDB item preparation
- Single Bedrock call constraint

### Build Docker Image

```bash
cd docker/whipser_api
docker build -t clinical-worker:latest .
```

### Deploy

See `NewState.md` for complete deployment instructions.

## Architecture

```
Audio → Whisper → Bedrock (ONCE) → [PDF, FHIR, DynamoDB] (Deterministic)
```

## Key Files

- `CurrentState.md` - Analysis of baseline system
- `NewState.md` - Complete implementation documentation
- `shared/schemas/consultation_artifact_schema.json` - JSON schema
- `analysis/prompts/bedrock_prompt.py` - Bedrock prompt template
- `storage/dynamodb/consultation_storage.py` - DynamoDB helpers
- `pdf/templates/consultation_pdf.py` - PDF generator
- `test_consultation_system.py` - Test suite

## Features

✓ Single Bedrock call per transcript
✓ Comprehensive SOAP notes
✓ Hospital/nursing handover
✓ Automated task extraction
✓ PDF generation (deterministic)
✓ FHIR export
✓ Backward compatible storage

## Documentation

Read `NewState.md` for:
- Complete process flow
- JSON schema details
- Bedrock prompt explanation
- DynamoDB schema
- PDF generation
- Testing instructions
- Task automation examples
- Migration notes
