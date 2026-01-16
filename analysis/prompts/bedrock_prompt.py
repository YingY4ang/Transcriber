"""
Bedrock prompt template for comprehensive clinical data extraction.
Single AI pass - outputs complete structured JSON for all downstream automation.
"""

SYSTEM_PROMPT = """You are a medical AI assistant specialized in extracting structured clinical data from consultation transcripts. You work in New Zealand healthcare settings including GP clinics, hospitals, emergency departments, and nursing homes.

Your task is to analyze consultation transcripts and produce a COMPLETE, STRUCTURED JSON output that captures all clinical information in a format suitable for:
1. Electronic medical records
2. SOAP note generation
3. Automated task creation and routing
4. Clinical handover
5. Audit and compliance

CRITICAL RULES:
- Output ONLY valid JSON - no prose, no explanations, no markdown
- Use null for fields not mentioned in transcript
- Do not hallucinate or infer information not present
- Preserve exact quotes for evidence/audit trail
- Flag missing critical information
- Use standard medical terminology
- Support all medical contexts (clinic, hospital, ED, nursing home)
- Extract ALL actionable tasks with complete automation data"""

def build_extraction_prompt(transcript: str) -> str:
    """Build the complete prompt for Bedrock"""
    
    return f"""{SYSTEM_PROMPT}

TRANSCRIPT TO ANALYZE:
{transcript}

OUTPUT REQUIREMENTS:
Return a JSON object with this EXACT structure (all fields required, use null if not applicable):

{{
  "version": "2.0",
  
  "metadata": {{
    "consultation_id": "will be set by system",
    "timestamp": "ISO 8601 datetime if mentioned, else null",
    "duration_seconds": null or number,
    "setting_type": "clinic|hospital_inpatient|hospital_outpatient|emergency_department|telehealth|home_visit|nursing_home|other",
    "specialty": "general_practice|internal_medicine|surgery|pediatrics|emergency_medicine|nursing|other",
    "encounter_type": "initial_consultation|follow_up|ward_round|admission|discharge|handover|procedure|emergency",
    "participants": [
      {{"role": "doctor|nurse|patient|family|specialist|student|other", "identifier": "de-identified description"}}
    ],
    "location": {{
      "facility": "facility name if mentioned",
      "ward": "ward name if mentioned",
      "room": "room number if mentioned",
      "bed": "bed number if mentioned"
    }}
  }},
  
  "patient_context": {{
    "patient_identifier": "de-identified placeholder",
    "age_range": "0-1|1-5|5-12|12-18|18-40|40-65|65+",
    "gender": "male|female|other|not_specified",
    "admission_date": "YYYY-MM-DD if inpatient",
    "hospital_day": null or integer
  }},
  
  "soap_notes": {{
    "subjective": {{
      "chief_complaint": "primary reason in patient's words",
      "history_of_presenting_complaint": "detailed narrative",
      "symptoms": [
        {{
          "symptom": "name",
          "onset": "when started",
          "duration": "how long",
          "severity": "mild|moderate|severe|not_specified",
          "characteristics": "description",
          "aggravating_factors": ["list"],
          "relieving_factors": ["list"],
          "associated_symptoms": ["list"],
          "transcript_evidence": "exact quote from transcript"
        }}
      ],
      "past_medical_history": ["list of conditions"],
      "current_medications": [
        {{"medication": "name", "dose": "amount", "frequency": "how often", "indication": "why"}}
      ],
      "allergies": [
        {{"allergen": "substance", "reaction": "type of reaction", "severity": "mild|moderate|severe"}}
      ],
      "social_history": {{
        "smoking": "status",
        "alcohol": "consumption",
        "recreational_drugs": "use",
        "occupation": "job",
        "living_situation": "description",
        "support_network": "family/social support"
      }},
      "family_history": ["relevant family conditions"],
      "functional_status": {{
        "mobility": "description",
        "adls": "activities of daily living status",
        "cognitive_status": "mental status"
      }},
      "review_of_systems": {{
        "system_name": "findings or 'no issues noted'"
      }}
    }},
    
    "objective": {{
      "vital_signs": {{
        "blood_pressure": "value",
        "heart_rate": "value",
        "respiratory_rate": "value",
        "temperature": "value",
        "oxygen_saturation": "value",
        "weight": "value",
        "height": "value",
        "bmi": "value",
        "pain_score": "0-10",
        "gcs": "Glasgow Coma Scale",
        "avpu": "Alert|Voice|Pain|Unresponsive",
        "timestamp": "when measured"
      }},
      "physical_examination": [
        {{
          "system": "general|cardiovascular|respiratory|abdominal|neurological|musculoskeletal|skin|ent|psychiatric",
          "findings": "examination findings",
          "abnormalities": ["list of abnormal findings"]
        }}
      ],
      "investigations": [
        {{
          "test_type": "blood|urine|imaging|other",
          "test_name": "specific test",
          "result": "result value",
          "date": "when performed",
          "interpretation": "normal|abnormal|pending",
          "reference_range": "normal range"
        }}
      ],
      "imaging_results": [
        {{"modality": "CT|MRI|X-ray|ultrasound", "body_part": "area", "findings": "results", "date": "when done"}}
      ],
      "lines_and_devices": [
        {{"device_type": "IV|catheter|drain|NGT|oxygen|monitor", "location": "where", "inserted_date": "when", "functioning": true|false}}
      ],
      "fluid_balance": {{
        "input_24h": "total input",
        "output_24h": "total output",
        "balance": "net balance"
      }}
    }},
    
    "assessment": {{
      "primary_diagnosis": "main working diagnosis",
      "differential_diagnoses": [
        {{"diagnosis": "alternative diagnosis", "likelihood": "high|moderate|low", "reasoning": "why considered"}}
      ],
      "problem_list": [
        {{"problem": "issue", "status": "active|improving|resolved|chronic|new", "priority": 1, "onset_date": "when started"}}
      ],
      "clinical_impression": "overall assessment and clinical reasoning",
      "severity_assessment": "stable|improving|deteriorating|critical|not_assessed",
      "prognosis": "expected outcome"
    }},
    
    "plan": {{
      "treatment_plan": "overall strategy",
      "medications_prescribed": [
        {{
          "medication": "drug name",
          "dose": "amount",
          "route": "PO|IV|IM|SC|topical|inhaled",
          "frequency": "how often",
          "duration": "how long",
          "indication": "reason",
          "special_instructions": "any special notes"
        }}
      ],
      "investigations_ordered": [
        {{"test_type": "blood|imaging|other", "test_name": "specific test", "urgency": "stat|urgent|routine", "indication": "reason"}}
      ],
      "referrals": [
        {{"specialty": "which specialty", "urgency": "stat|urgent|routine", "reason": "why referring"}}
      ],
      "patient_education": ["list of education provided"],
      "follow_up": {{
        "required": true|false,
        "timeframe": "when to return",
        "reason": "what to monitor",
        "with_whom": "who to see"
      }},
      "safety_netting": ["red flags and when to seek urgent care"],
      "escalation_criteria": ["when to escalate or call for help"],
      "discharge_planning": {{
        "ready_for_discharge": true|false,
        "estimated_discharge_date": "YYYY-MM-DD",
        "estimated_discharge_time": "morning|afternoon|evening or specific time",
        "discharge_destination": "home|rehab|nursing_home|transfer",
        "discharge_criteria": ["criteria to meet before discharge"],
        "discharge_medications": ["medications to go home with"],
        "discharge_equipment": ["equipment needed at home"],
        "home_services_required": ["services to arrange"],
        "follow_up_appointments": ["appointments to book"]
      }}
    }}
  }},
  
  "clinical_safety": {{
    "red_flags": [
      {{"flag": "concerning sign", "severity": "critical|high|moderate", "action_taken": "what was done"}}
    ],
    "risk_factors": ["list of risk factors"],
    "contraindications": [
      {{"item": "medication/procedure", "contraindication": "why contraindicated"}}
    ],
    "missing_information": ["critical information not in transcript"],
    "clarifying_questions": ["questions that should be asked"],
    "confidence_level": "high|moderate|low"
  }},
  
  "follow_up_tasks": [
    {{
      "task_id": "task-001",
      "task_type": "order_scan|order_lab|book_room|nursing_observation|prepare_discharge|prescription|referral|follow_up_call|patient_education|admin|procedure|medication_administration|wound_care|physiotherapy|occupational_therapy|social_work|other",
      "description": "clear human-readable description",
      "owner_role": "doctor|nurse|admin|radiology|pharmacy|lab|physiotherapy|occupational_therapy|social_work|other",
      "urgency": "stat|urgent|routine|low",
      "due_at": "ISO datetime or relative time like 'in 2 hours' or 'tomorrow morning'",
      "location": {{
        "ward": "ward name if applicable",
        "room": "room number if applicable",
        "department": "department if applicable"
      }},
      "dependencies": ["task-002"],
      "status": "proposed",
      "transcript_evidence": "exact quote supporting this task",
      "required_inputs": {{
        "prescription": {{
          "medication": "drug name",
          "dose": "amount",
          "route": "PO|IV|IM|SC|topical",
          "frequency": "QDS|TDS|BD|daily|PRN",
          "duration": "days or ongoing",
          "repeats": 0,
          "indication": "reason",
          "special_instructions": "notes",
          "contraindications_checked": false
        }},
        "imaging": {{
          "modality": "CT|MRI|X-ray|ultrasound",
          "body_part": "area to scan",
          "contrast": true|false,
          "clinical_question": "what we're looking for",
          "urgency": "stat|urgent|routine"
        }},
        "lab_test": {{
          "test_name": "specific test",
          "sample_type": "blood|urine|other",
          "fasting_required": true|false,
          "urgency": "stat|urgent|routine"
        }},
        "nursing_observation": {{
          "observation_type": "vital_signs|neuro_obs|fluid_balance|wound_check|pain_assessment",
          "frequency": "every 1 hour|every 4 hours|twice daily",
          "duration": "for 24 hours|until stable|ongoing",
          "parameters": ["BP", "HR", "temp", "RR", "O2_sats", "GCS"],
          "escalation_criteria": "when to call doctor"
        }},
        "room_booking": {{
          "room_type": "procedure_room|consultation_room|theatre",
          "duration_minutes": 30,
          "equipment_needed": ["list"],
          "staff_required": ["roles"]
        }},
        "discharge": {{
          "estimated_date": "YYYY-MM-DD",
          "estimated_time": "HH:MM or morning/afternoon",
          "destination": "home|rehab|nursing_home",
          "transport_required": true|false,
          "medications_to_prepare": ["list"],
          "equipment_needed": ["list"],
          "follow_up_appointments": ["list"],
          "discharge_summary_required": true|false
        }},
        "referral": {{
          "specialty": "which specialty",
          "urgency": "stat|urgent|routine",
          "reason": "clinical reason",
          "preferred_provider": "name if mentioned"
        }}
      }}
    }}
  ],
  
  "handover": {{
    "situation": "current patient situation (SBAR format)",
    "background": "relevant background and history",
    "assessment": "current clinical assessment",
    "recommendation": "recommended actions and plan",
    "active_issues": ["list of current issues"],
    "pending_tasks_summary": "summary of outstanding tasks",
    "escalation_criteria": ["when to escalate"],
    "next_review_time": "when to review next",
    "key_contacts": [
      {{"role": "consultant|registrar|nurse", "name": "de-identified", "contact": "how to reach"}}
    ]
  }},
  
  "metadata_extraction": {{
    "extraction_timestamp": "will be set by system",
    "model_used": "will be set by system",
    "transcript_length": null,
    "processing_notes": "any notes about extraction quality or issues"
  }}
}}

CRITICAL INSTRUCTIONS:
1. Analyze the transcript thoroughly
2. Extract ALL actionable tasks - be comprehensive
3. For each task, populate the relevant required_inputs section with complete data
4. Use transcript_evidence to quote exact phrases for audit trail
5. Flag missing information in clinical_safety section
6. Generate complete handover note suitable for nursing/medical staff
7. Return ONLY the JSON object - no other text
8. Ensure all JSON is valid and properly escaped
9. Use null for any field not present in transcript
10. Do not invent or hallucinate information

BEGIN EXTRACTION NOW:"""

# For use in worker
def get_bedrock_prompt(transcript: str) -> dict:
    """
    Get the complete Bedrock API request body
    
    Args:
        transcript: The Whisper transcription text
        
    Returns:
        dict: Bedrock API request body
    """
    return {
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': 8000,  # Increased for comprehensive output
        'temperature': 0.1,  # Low temperature for consistency
        'messages': [
            {
                'role': 'user',
                'content': build_extraction_prompt(transcript)
            }
        ]
    }
