# Current State Analysis

## Existing Pipeline Flow

### Entry Points

**1. API Gateway → Lambda (`backend/api_lambda_clean.py`)**
- `GET /get-upload-url` - Generates presigned S3 URL for audio upload
- `POST /upload-complete` - Triggers SQS message to start processing
- `GET /result/{key}` - Retrieves results from DynamoDB
- `GET /config` - Returns WebSocket URL for real-time updates

**2. EC2 Worker (`docker/whipser_api/worker_openai.py`)**
- Polls SQS queue continuously (20s wait time)
- Processes audio files when messages arrive

### Current Data Flow

```
1. Browser
   ↓ GET /get-upload-url
2. Lambda API
   ↓ Generate presigned S3 URL
   ↓ Return URL + key
3. Browser
   ↓ PUT audio file to S3
4. Browser
   ↓ POST /upload-complete with key
5. Lambda API
   ↓ Send SQS message
6. SQS Queue
   ↓ Message available
7. EC2 Worker (polls queue)
   ↓ Receive message
   ↓ Download audio from S3
8. Local file (/tmp/xxx.webm)
   ↓ Apply VAD (Voice Activity Detection) - removes silence
   ↓ Save as /tmp/xxx_vad.wav
9. Whisper API (OpenAI)
   ↓ Transcribe audio
   ↓ Return plain text transcript
10. Worker Memory (transcript string)
    ↓ Build prompt with transcript
11. AWS Bedrock (Claude Haiku)
    ↓ Extract structured data
    ↓ Return JSON text
12. Worker Memory (parse JSON)
    ↓ Generate FHIR bundle
13. DynamoDB
    ↓ Store flat item
14. WebSocket notification (optional)
    ↓ Notify connected clients
15. S3
    ↓ Delete audio file
16. SQS
    ↓ Delete message
17. Browser polls /result/{key}
    ↓ Lambda queries DynamoDB
    ↓ Return results
```

### Whisper Transcription Step

**Location:** `docker/whipser_api/worker_openai.py` (lines ~200-210)

**Process:**
1. Downloads audio from S3 to `/tmp/{basename}.webm`
2. Applies VAD using librosa to remove silence
3. Saves processed audio as `/tmp/{basename}_vad.wav`
4. Sends to OpenAI Whisper API
5. Receives plain text transcript

**Input:** Audio file (WebM format)
**Output:** Plain text string (transcript)
**Storage:** Transcript saved to DynamoDB as `transcript` field

### Bedrock Invocation Step

**Location:** `docker/whipser_api/worker_openai.py` (lines ~212-235)

**Current Prompt:**
```
Extract clinical data and return ONLY valid JSON in this format:
{
  "tasks": ["task1", "task2"],
  "diagnosis": "condition name",
  "medications": ["med1", "med2"],
  "follow_up": "follow up plan",
  "notes": "additional notes",
  "vital_signs": {"bp": "120/80", "hr": "72", "temp": "36.5"},
  "symptoms": ["symptom1", "symptom2"]
}

Clinical transcript: {transcript}
```

**Process:**
1. Builds prompt with transcript
2. Calls Bedrock with Claude Haiku model
3. Parses response using regex to extract JSON
4. Falls back to `{"notes": ai_text}` if parsing fails

**Input:** Transcript text
**Output:** Simple flat JSON object
**Model:** `anthropic.claude-3-haiku-20240307-v1:0`
**Max tokens:** 1024

### DynamoDB Storage

**Table Name:** `clinical-results` (from env var `TABLE_NAME`)

**Partition Key:** `audio_key` (string) - S3 key of audio file

**Current Item Structure (FLAT):**
```json
{
  "audio_key": "uploads/test_xxx.webm",
  "patient_id": "extracted_from_key",
  "transcript": "full transcript text",
  "timestamp": 1234567890,
  "fhir_bundle": { /* FHIR Bundle object */ },
  "tasks": ["task1", "task2"],
  "diagnosis": "condition name",
  "medications": ["med1", "med2"],
  "follow_up": "follow up plan",
  "notes": "additional notes",
  "vital_signs": {"bp": "120/80", "hr": "72"},
  "symptoms": ["symptom1", "symptom2"]
}
```

**Storage Method:** 
- Uses `**extracted` to spread Bedrock JSON fields directly into top-level item
- FHIR bundle stored as nested object
- No structured nesting for clinical data

### Existing JSON Artifact

**Yes, there is an existing JSON structure:**

1. **Bedrock Output JSON** (simple, flat):
   - `tasks` (array of strings)
   - `diagnosis` (string)
   - `medications` (array of strings)
   - `follow_up` (string)
   - `notes` (string)
   - `vital_signs` (flat object)
   - `symptoms` (array of strings)

2. **FHIR Bundle** (generated from Bedrock output):
   - Created by `generate_fhir_bundle()` function
   - Converts simple JSON to FHIR R4 resources
   - Stored as `fhir_bundle` field in DynamoDB

3. **DynamoDB Item** (flat structure):
   - Spreads Bedrock fields at top level
   - Adds metadata: `audio_key`, `patient_id`, `transcript`, `timestamp`
   - Includes `fhir_bundle` as nested object

### Key Observations

**Problems with Current Structure:**

1. **Flat DynamoDB schema** - Bedrock fields spread at top level makes it hard to:
   - Distinguish between metadata and clinical data
   - Version the schema
   - Query structured data
   - Preserve nested structures

2. **Limited Bedrock output** - Current JSON is too simple:
   - No SOAP structure
   - No follow-up task details (just string descriptions)
   - No hospital/nursing context
   - No confidence/evidence tracking
   - No handover information

3. **No PDF generation** - Results only stored in DynamoDB

4. **FHIR generation happens AFTER Bedrock** - Requires additional processing

5. **Single Bedrock call constraint is met** - Only called once per transcript ✓

### Versioning Strategy Recommendation

**Approach: Backward-compatible versioning with nested structure**

**Rationale:**
- Existing consumers expect flat fields at top level
- New structure should be nested under a single key
- Preserve old fields for backward compatibility during transition

**Proposed DynamoDB Item Structure:**
```json
{
  "audio_key": "uploads/test_xxx.webm",
  "patient_id": "ABC1234",
  "transcript": "full text",
  "timestamp": 1234567890,
  
  // NEW: Complete structured artifact
  "consultation_artifact": {
    "version": "2.0",
    "metadata": { /* ... */ },
    "soap_notes": { /* ... */ },
    "follow_up_tasks": [ /* ... */ ],
    "handover": { /* ... */ }
  },
  
  // LEGACY: Keep old flat fields for backward compatibility
  "tasks": ["task1"],
  "diagnosis": "...",
  "medications": ["..."],
  "fhir_bundle": { /* ... */ }
}
```

**Migration Path:**
1. Add new `consultation_artifact` field (nested)
2. Keep old flat fields populated from artifact
3. Update Bedrock prompt to output new structure
4. Update consumers to use `consultation_artifact` when available
5. Eventually deprecate flat fields

**Benefits:**
- No breaking changes for existing consumers
- Clear separation of metadata vs clinical data
- Preserves nested structures
- Easy to version (add `version` field)
- Can query both old and new items

### Summary

**Current State:**
- ✓ Single Bedrock call per transcript
- ✓ Whisper transcription working
- ✓ DynamoDB storage working
- ✗ Flat schema loses structure
- ✗ Limited clinical data extraction
- ✗ No PDF generation
- ✗ No hospital/nursing context
- ✗ No detailed follow-up tasks
- ✗ No handover notes

**Next Steps:**
1. Design comprehensive JSON schema for `consultation_artifact`
2. Update Bedrock prompt to output new structure
3. Modify worker to store nested artifact
4. Add PDF generation (deterministic, no AI)
5. Maintain backward compatibility with flat fields
