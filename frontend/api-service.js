// API service for backend communication
class APIService {
    constructor(baseURL) {
        this.baseURL = baseURL || 'https://your-api-gateway-url.execute-api.ap-southeast-2.amazonaws.com';
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }

        return response.json();
    }

    // Configuration
    async getConfig() {
        return this.request('/config');
    }

    // Upload
    async getUploadURL(patientId) {
        return this.request(`/get-upload-url?patientId=${patientId}`);
    }

    async uploadAudio(url, audioBlob) {
        const response = await fetch(url, {
            method: 'PUT',
            body: audioBlob,
            headers: { 'Content-Type': 'application/octet-stream' }
        });
        return response.ok;
    }

    async triggerProcessing(key) {
        return this.request('/upload-complete', {
            method: 'POST',
            body: JSON.stringify({ key })
        });
    }

    // Results
    async getResult(key) {
        return this.request(`/result/${encodeURIComponent(key)}`);
    }

    // Approvals
    async getPendingApprovals() {
        return this.request('/approvals/pending');
    }

    async approveConsultation(audioKey, approvedBy, notes = null, modifiedArtifact = null) {
        return this.request('/approvals/approve', {
            method: 'POST',
            body: JSON.stringify({
                audio_key: audioKey,
                approved_by: approvedBy,
                notes,
                modified_artifact: modifiedArtifact
            })
        });
    }

    async rejectConsultation(audioKey, rejectedBy, reason) {
        return this.request('/approvals/reject', {
            method: 'POST',
            body: JSON.stringify({
                audio_key: audioKey,
                rejected_by: rejectedBy,
                reason
            })
        });
    }

    // Patient History
    async getPatientHistory(patientId) {
        return this.request(`/patient/${encodeURIComponent(patientId)}`);
    }

    // Tasks
    async getPendingTasks() {
        return this.request('/tasks/pending');
    }

    async updateTask(audioKey, taskId, status, completedBy = null, notes = null) {
        return this.request('/tasks/update', {
            method: 'POST',
            body: JSON.stringify({
                audio_key: audioKey,
                task_id: taskId,
                status,
                completed_by: completedBy,
                notes
            })
        });
    }

    // Handover
    async getHandover(clinicianId, date = null) {
        const params = new URLSearchParams({ clinician_id: clinicianId });
        if (date) params.append('date', date);
        return this.request(`/handover?${params}`);
    }

    // Consent
    async recordConsent(patientId, consentType, granted, recordedBy, notes = null) {
        return this.request('/consent/record', {
            method: 'POST',
            body: JSON.stringify({
                patient_id: patientId,
                consent_type: consentType,
                granted,
                recorded_by: recordedBy,
                notes
            })
        });
    }

    async checkConsent(patientId, consentType) {
        return this.request(`/consent/check?patient_id=${patientId}&consent_type=${consentType}`);
    }

    // Integration Status
    async getIntegrationStatus() {
        return this.request('/integration/status');
    }
}

// Export for use in other files
window.APIService = APIService;
