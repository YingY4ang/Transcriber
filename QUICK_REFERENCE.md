# Quick Reference Card

## What Was Built

**Single-pass AI extraction** → **Deterministic automation**

One Bedrock call produces complete `ConsultationArtifact` (v2.0) used for:
- SOAP notes
- PDF generation
- Task extraction
- FHIR export
- Handover notes

## Key Files

| File | Purpose |
|------|---------|
| `CurrentState.md` | Baseline system analysis |
| `NewState.md` | Complete implementation docs |
| `SUMMARY.md` | Implementation summary |
| `IMPLEMENTATION.md` | Quick start guide |
| `test_consultation_system.py` | Test suite |

## Quick Commands

```bash
# Run tests
python test_consultation_system.py

# Build Docker
cd docker/whipser_api && docker build -t clinical-worker .

# Deploy
docker push <ecr-url>/clinical-worker:latest
```

## JSON Structure

```json
{
  "version": "2.0",
  "metadata": { /* context */ },
  "patient_context": { /* de-identified */ },
  "soap_notes": {
    "subjective": { /* history, symptoms, meds, allergies */ },
    "objective": { /* vitals, exam, investigations */ },
    "assessment": { /* diagnosis, differentials, problems */ },
    "plan": { /* treatment, investigations, referrals */ }
  },
  "clinical_safety": { /* red flags, risks, missing info */ },
  "follow_up_tasks": [ /* structured tasks with automation data */ ],
  "handover": { /* SBAR format */ }
}
```

## DynamoDB Item

```json
{
  "audio_key": "uploads/xxx.webm",
  "consultation_artifact": { /* nested structure */ },
  "follow_up_tasks": [ /* tasks */ ],
  "pending_task_count": 5,
  "urgent_task_count": 2,
  // Legacy fields for backward compatibility
  "diagnosis": "...",
  "medications": [...],
  "tasks": [...]
}
```

## Task Structure

```json
{
  "task_id": "task-001",
  "task_type": "prescription",
  "description": "Administer aspirin 300mg",
  "owner_role": "nurse",
  "urgency": "stat",
  "due_at": "immediately",
  "status": "proposed",
  "required_inputs": {
    "prescription": {
      "medication": "Aspirin",
      "dose": "300mg",
      "route": "PO",
      "frequency": "stat",
      "duration": "once"
    }
  }
}
```

## Cost

- Old: $0.016/consultation
- New: $0.026/consultation
- Increase: $0.010 for complete structured output

## Constraints Enforced

✓ Single Bedrock call per transcript
✓ PDF generation is deterministic (no AI)
✓ FHIR generation uses artifact (no AI)
✓ DynamoDB storage preserves structure
✓ All downstream steps are deterministic

## Next Steps

1. Test with real transcripts
2. Review PDF output
3. Deploy to staging
4. Enable PDF S3 upload (uncomment code)
5. Build task automation
6. Monitor costs

## Support

- Read `NewState.md` for details
- Run tests to validate setup
- Check CloudWatch logs for errors
- Review DynamoDB items for structure
