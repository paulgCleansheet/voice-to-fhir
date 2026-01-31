# Deployment Architecture

**Voice-to-Health-Record Clinical Extraction Pipeline**

---

## Overview

This document outlines deployment options for the clinical extraction pipeline, ranging from cloud-based inference to edge deployment for privacy-sensitive environments.

---

## Deployment Options

### Option 1: Cloud Deployment (HuggingFace Inference Endpoint)

**Best for:** Organizations with cloud connectivity, variable workloads, minimal IT infrastructure

```
┌─────────────┐     HTTPS      ┌─────────────────────┐     HTTPS      ┌───────────────────┐
│   Client    │───────────────▶│  v2hr FastAPI       │───────────────▶│  HuggingFace      │
│  (EHR/App)  │◀───────────────│  (Container Apps)   │◀───────────────│  Inference API    │
└─────────────┘                └─────────────────────┘                └───────────────────┘
                                        │
                                        ▼
                               ┌─────────────────────┐
                               │  Post-Processing    │
                               │  (RxNorm, ICD-10)   │
                               └─────────────────────┘
```

**Infrastructure:**
| Component | Service | Estimated Cost |
|-----------|---------|----------------|
| API Server | Azure Container Apps | $20-40/mo |
| MedGemma | HuggingFace Inference Endpoint | $0.03-0.05/request |
| Storage | Azure Table Storage | $5-10/mo |
| **Total** | | **$50-100/mo + usage** |

**Characteristics:**
- **Latency:** 2-5 seconds per extraction
- **Scalability:** Auto-scales to 1000s concurrent requests
- **HIPAA:** Data processed in-transit, not stored; BAA available from HuggingFace
- **Setup time:** 2-4 hours

**Configuration:**
```bash
# .env
MEDGEMMA_ENDPOINT=https://your-endpoint.endpoints.huggingface.cloud
MEDGEMMA_BACKEND=dedicated
HF_TOKEN=hf_your_token
```

---

### Option 2: Edge Deployment (On-Premises GPU)

**Best for:** Privacy-sensitive environments, regulatory constraints, offline operation

```
┌─────────────┐                ┌─────────────────────────────────────┐
│   Client    │───────────────▶│         On-Premises Server          │
│  (EHR/App)  │◀───────────────│  ┌───────────┐    ┌──────────────┐  │
└─────────────┘                │  │  v2hr     │───▶│  MedGemma    │  │
                               │  │  FastAPI  │◀───│  (Local GPU) │  │
                               │  └───────────┘    └──────────────┘  │
                               │         │                           │
                               │         ▼                           │
                               │  ┌──────────────┐                   │
                               │  │ Post-Process │                   │
                               │  └──────────────┘                   │
                               └─────────────────────────────────────┘
```

**Hardware Requirements:**
| Component | Specification | Estimated Cost |
|-----------|---------------|----------------|
| GPU | NVIDIA L4 (24GB) or RTX 4090 | $500-1,500 |
| Server | 32GB RAM, 8-core CPU | $800-1,500 |
| Storage | 256GB SSD | $50-100 |
| **Total** | | **$1,350-3,100 one-time** |

**Alternative: NVIDIA Jetson Orin**
| Component | Specification | Estimated Cost |
|-----------|---------------|----------------|
| Jetson AGX Orin | 64GB, 275 TOPS | $1,999 |
| Power supply | Included | - |
| **Total** | | **$2,000 one-time** |

**Characteristics:**
- **Latency:** 0.5-2 seconds per extraction
- **Scalability:** Fixed capacity (add more devices for scale)
- **HIPAA:** Full on-premises control; no data leaves network
- **Setup time:** 1-2 days

**Configuration:**
```bash
# .env
MEDGEMMA_BACKEND=local
MEDGEMMA_LOCAL_URL=http://localhost:8080
```

**Local Model Setup:**
```bash
# Using vLLM or TGI for local inference
pip install vllm
vllm serve google/medgemma-4b-it --port 8080 --gpu-memory-utilization 0.9
```

---

### Option 3: Hybrid Deployment

**Best for:** Organizations needing both real-time and batch processing, cost optimization

```
┌─────────────┐                              ┌───────────────────┐
│  Real-time  │──────────────────────────────│  Edge Server      │
│  Requests   │                              │  (Local GPU)      │
└─────────────┘                              └───────────────────┘
                                                      │
                                                      ▼
                    ┌─────────────────────────────────────────────────┐
                    │              v2hr API Gateway                    │
                    │  Routes: real-time → edge, batch → cloud        │
                    └─────────────────────────────────────────────────┘
                                                      │
                                                      ▼
┌─────────────┐                              ┌───────────────────┐
│   Batch     │──────────────────────────────│  Cloud Endpoint   │
│  Processing │                              │  (HuggingFace)    │
└─────────────┘                              └───────────────────┘
```

**Use Cases:**
- **Real-time (Edge):** Active clinical documentation, point-of-care extraction
- **Batch (Cloud):** Historical record processing, overnight reconciliation

**Cost Optimization:**
- Edge handles high-frequency, low-latency requests (daytime clinical work)
- Cloud handles burst capacity and overnight batch jobs
- Estimated 60-70% cost reduction vs. cloud-only for high-volume sites

---

## EHR Integration Paths

### Epic Integration

**FHIR R4 REST API:**
```
v2hr → FHIR R4 Bundle → Epic FHIR Server
                         └── POST /Bundle
```

**CDA Import:**
```
v2hr → CDA R2 Document → Epic CDA Importer
                          └── Clinical Document Architecture
```

### Cerner (Oracle Health) Integration

**HL7 v2.x Interface:**
```
v2hr → HL7 v2.x ORU^R01 → Cerner HL7 Interface Engine
                          └── TCP/MLLP connection
```

**FHIR R4:**
```
v2hr → FHIR R4 Bundle → Cerner Millennium FHIR API
```

### Generic FHIR Server

Compatible with any FHIR R4 server:
- HAPI FHIR
- Microsoft Azure FHIR
- Google Cloud Healthcare API
- AWS HealthLake

---

## Security Architecture

### Data Flow Security

```
┌──────────────┐    TLS 1.3    ┌──────────────┐    TLS 1.3    ┌──────────────┐
│   Client     │──────────────▶│   v2hr API   │──────────────▶│  MedGemma    │
│              │               │              │               │  Endpoint    │
└──────────────┘               └──────────────┘               └──────────────┘
                                      │
                                      │ Encrypted at rest
                                      ▼
                               ┌──────────────┐
                               │  Audit Log   │
                               │  (AES-256)   │
                               └──────────────┘
```

### HIPAA Compliance Checklist

| Requirement | Cloud | Edge | Notes |
|-------------|-------|------|-------|
| **Encryption in transit** | ✅ TLS 1.3 | ✅ TLS 1.3 | All API communication encrypted |
| **Encryption at rest** | ✅ Provider-managed | ✅ Full disk encryption | Configure storage encryption |
| **Access controls** | ✅ API keys + RBAC | ✅ Network isolation | Implement authentication |
| **Audit logging** | ✅ Cloud logging | ✅ Local logging | All requests logged |
| **BAA** | ✅ HuggingFace, Azure | N/A | Obtain signed BAAs |
| **Data retention** | ✅ Configurable | ✅ Full control | Implement retention policy |
| **Breach notification** | ✅ Provider SLA | ✅ Internal process | Document procedures |

### PHI Handling

**Cloud Deployment:**
- Transcripts transmitted to inference endpoint
- No PHI stored by v2hr (stateless processing)
- HuggingFace Inference Endpoints offer HIPAA-eligible tiers

**Edge Deployment:**
- All PHI remains on-premises
- No external network communication required
- Full organizational control over data

---

## Performance Benchmarks

### Latency (per extraction)

| Deployment | p50 | p95 | p99 |
|------------|-----|-----|-----|
| Cloud (L4 GPU) | 2.1s | 3.8s | 5.2s |
| Edge (RTX 4090) | 0.8s | 1.4s | 2.1s |
| Edge (Jetson Orin) | 1.2s | 2.0s | 2.8s |

### Throughput

| Deployment | Requests/min | Notes |
|------------|--------------|-------|
| Cloud (single endpoint) | 25-30 | Auto-scales with demand |
| Edge (RTX 4090) | 40-50 | Fixed capacity |
| Edge (Jetson Orin) | 30-35 | Power-efficient |

### Cost per Extraction

| Deployment | Cost | Break-even |
|------------|------|------------|
| Cloud | $0.03-0.05 | N/A (pay-per-use) |
| Edge (one-time $2,000) | $0.00 | ~50,000 extractions |

---

## Deployment Checklist

### Cloud Deployment

- [ ] Create HuggingFace account
- [ ] Request MedGemma access
- [ ] Deploy Inference Endpoint (GPU instance)
- [ ] Configure Azure Container Apps
- [ ] Set environment variables
- [ ] Test health endpoint
- [ ] Configure monitoring/alerting
- [ ] Obtain BAA from providers

### Edge Deployment

- [ ] Procure GPU hardware
- [ ] Install CUDA drivers
- [ ] Download MedGemma model weights
- [ ] Install vLLM or TGI
- [ ] Deploy v2hr container
- [ ] Configure network security
- [ ] Test extraction pipeline
- [ ] Set up local monitoring

---

## Support Matrix

| Feature | Cloud | Edge | Hybrid |
|---------|-------|------|--------|
| **Setup complexity** | Low | Medium | High |
| **Operating cost** | Usage-based | Fixed | Mixed |
| **Latency** | 2-5s | 0.5-2s | Variable |
| **HIPAA compliance** | BAA required | Full control | Both |
| **Offline operation** | ❌ | ✅ | Partial |
| **Auto-scaling** | ✅ | ❌ | Partial |
| **Recommended for** | Variable workload | Privacy-critical | High-volume |

---

## Contact

For deployment assistance:
- **Repository:** https://github.com/paulgCleansheet/voice-to-health-record
- **Documentation:** See README.md for API usage

---

**Last Updated:** January 30, 2026
