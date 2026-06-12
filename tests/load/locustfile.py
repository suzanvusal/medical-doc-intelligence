"""Locust load test for Medical Document Intelligence API."""
import random
from locust import HttpUser, between, task

CLINICAL_QUESTIONS = [
    "What is the patient's primary diagnosis?",
    "What medications is the patient currently taking?",
    "What were the lab results?",
    "What is the treatment plan?",
    "Are there any allergies documented?",
    "What were the vital signs on admission?",
    "What procedures were performed?",
    "What is the discharge summary?",
]


class MedicalDocUser(HttpUser):
    wait_time = between(1, 3)

    @task(10)
    def query_document(self):
        payload = {
            "question": random.choice(CLINICAL_QUESTIONS),
            "doc_type": "default",
            "patient_id": f"PAT-{random.randint(1,999):06d}",
        }
        with self.client.post("/query", json=payload, catch_response=True) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if "answer" not in data:
                    resp.failure("Missing answer in response")
            elif resp.status_code == 503:
                resp.failure("RAG pipeline not ready")

    @task(3)
    def health_check(self):
        self.client.get("/health")

    @task(1)
    def metrics_check(self):
        self.client.get("/metrics")

# 12:47:24 — refactor: switch synchronous embedding calls to async

# 13:34:29 — docs: fix typo in inline comment in locustfile
