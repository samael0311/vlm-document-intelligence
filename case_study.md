# Portfolio Case Study: Project 1
**Title:** Multimodal Document & Invoice Extraction Engine (Vision-Language AI)
**Category:** Artificial Intelligence & Machine Learning > Computer Vision / NLP
**Role:** Lead AI Architect & Machine Learning Engineer
**Skills:** Large Language Model, Computer Vision, Python, FastAPI, Amazon Web Services (AWS), Hugging Face, OCR Algorithm

---

### Upwork Overview Box (< 600 characters):
```text
Built an enterprise multimodal AI pipeline using Vision-Language Models (Qwen 2.5-VL) to automate structured data extraction from complex invoices and scanned forms.

• Architecture: Deployed SOTA VLMs with strict JSON/Pydantic schema validation to extract tabular line items, dates, and totals without hallucinations.
• Production: Optimized AWS GPU inference via a modular FastAPI microservice with dynamic batching.
• Impact: Achieved sub-minute extraction latency and eliminated manual transcription errors across downstream databases.
```

---

### Upwork Case Study Section Boxes (if using Case Study template):

#### 1. The Challenge (Problem Statement)
```text
Manual transcription of 100+ multi-format supplier invoices, bills, and claims created high error rates and processing bottlenecks. Legacy OCR engines frequently failed on low-resolution scans (150 DPI) and varied tabular layouts, causing schema drift and database ingestion errors.
```

#### 2. The Solution (Your Approach)
```text
Architected an automated multimodal pipeline using Vision-Language Models (Qwen 2.5-VL 7B) on AWS GPU infrastructure. Enforced strict Pydantic/JSON schema validation to extract key-value pairs, dates (YYYY-MM-DD), and line items without hallucinations, packaged as a FastAPI microservice.
```

#### 3. Results & Deliverables
```text
• Sub-minute per-document processing speed across multi-page files.
• 100% deterministic, validated JSON output ready for direct database storage.
• Modular Python source code, containerized API, and automated test suite.
```

---

### Media & Deliverables:
- **Architecture Diagram:** [`architecture_diagram.png`](./architecture_diagram.png) *(Real, clean 1600x900 enterprise system architecture diagram)*
- **Public GitHub Repository:** [https://github.com/samael0311/vlm-document-intelligence](https://github.com/samael0311/vlm-document-intelligence) *(Complete FastAPI, Pydantic V2, Docker, & Pytest codebase)*
