# Production Deployment Plan

**Voice-to-Health-Record Clinical Extraction Pipeline**
**Version:** 1.0
**Date:** January 30, 2026

---

## 1. Executive Summary

This document provides operational guidance for deploying the v2hr clinical extraction pipeline in production healthcare environments. Three deployment models are supported: cloud-hosted, edge-deployed, and hybrid configurations.

**Key Decision Factors:**
| Factor | Cloud | Edge | Hybrid |
|--------|-------|------|--------|
| Initial Cost | Low ($0) | High ($2-5K) | Medium ($2-5K) |
| Operating Cost | Per-use ($0.03-0.05/extraction) | Fixed ($50-100/mo electricity) | Mixed |
| Data Residency | External (BAA required) | On-premises | Configurable |
| Latency | 2-5 seconds | 0.5-2 seconds | Variable |
| Scalability | Unlimited | Fixed capacity | Burst to cloud |
| Best For | Variable workload, low volume | Privacy-critical, high volume | Enterprise |

---

## 2. Architecture Overview

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           v2hr Production Stack                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │   Ingress    │───▶│   v2hr API   │───▶│   MedGemma   │───▶│  Output   │ │
│  │  (HTTPS)     │    │  (FastAPI)   │    │  Inference   │    │  (FHIR)   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └───────────┘ │
│         │                   │                   │                   │       │
│         ▼                   ▼                   ▼                   ▼       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │   WAF/DDoS   │    │  Post-Proc   │    │  Model Cache │    │  EHR API  │ │
│  │ (Cloudflare) │    │  (RxNorm/ICD)│    │  (GPU VRAM)  │    │(Epic/Cerner)│
│  └──────────────┘    └──────────────┘    └──────────────┘    └───────────┘ │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    Observability Stack                                │   │
│  │  Logging (structured JSON) │ Metrics (Prometheus) │ Tracing (Jaeger) │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
1. Transcript Ingestion
   └── HTTPS POST to /api/v1/extract
       └── Request validation (Pydantic)
           └── Workflow selection (general, emergency, intake, etc.)

2. MedGemma Extraction
   └── Prompt construction (workflow-specific)
       └── Inference call (HuggingFace or local)
           └── JSON response parsing

3. Post-Processing
   └── RxNorm medication validation (89% match rate)
       └── ICD-10-CM diagnosis coding (92% match rate)
           └── Order-diagnosis linking (clinical rules)
               └── Uncertainty flagging (*_matched: false)

4. Output Generation
   └── Format selection (fhir-r4, cda, hl7v2)
       └── FHIR Bundle / CDA Document / HL7 Message
           └── Response to client

5. EHR Integration (optional)
   └── FHIR POST to EHR server
       └── Or: CDA import / HL7 interface engine
```

---

## 3. Cloud Deployment

### 3.1 Reference Architecture (Azure)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Azure Subscription                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐         ┌──────────────────────────────────┐  │
│  │  Cloudflare  │────────▶│     Azure Container Apps         │  │
│  │  (DNS/WAF)   │         │  ┌────────────────────────────┐  │  │
│  └──────────────┘         │  │     v2hr-api container     │  │  │
│                           │  │     (2 vCPU, 4GB RAM)      │  │  │
│                           │  │     Scale: 0-10 replicas   │  │  │
│                           │  └────────────────────────────┘  │  │
│                           └──────────────────────────────────┘  │
│                                         │                        │
│                                         ▼                        │
│  ┌──────────────┐         ┌──────────────────────────────────┐  │
│  │  Key Vault   │         │     External: HuggingFace        │  │
│  │  (Secrets)   │         │     Inference Endpoint           │  │
│  └──────────────┘         │     (NVIDIA L4 GPU)              │  │
│                           └──────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────┐         ┌──────────────────────────────────┐  │
│  │ Log Analytics│◀────────│     Application Insights          │  │
│  │  (Logging)   │         │     (Metrics/Tracing)            │  │
│  └──────────────┘         └──────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Cloud Cost Model

| Component | Service | Monthly Cost |
|-----------|---------|--------------|
| API Hosting | Azure Container Apps | $20-40 |
| Secrets | Azure Key Vault | $3 |
| Logging | Log Analytics (5GB) | $12 |
| DNS/WAF | Cloudflare Free | $0 |
| **Infrastructure Subtotal** | | **$35-55/mo** |
| | | |
| MedGemma Inference | HuggingFace Endpoint | $0.03-0.05/request |
| | | |
| **Example: 1,000 extractions/month** | | **$65-105/mo** |
| **Example: 10,000 extractions/month** | | **$335-555/mo** |

### 3.3 Cloud Deployment Steps

```bash
# 1. Prerequisites
az login
az account set --subscription "your-subscription"

# 2. Create resource group
az group create --name v2hr-prod --location eastus

# 3. Create Container Registry
az acr create --resource-group v2hr-prod --name v2hracr --sku Basic

# 4. Build and push container
az acr build --registry v2hracr --image v2hr:latest .

# 5. Create Container Apps environment
az containerapp env create \
  --name v2hr-env \
  --resource-group v2hr-prod \
  --location eastus

# 6. Deploy container app
az containerapp create \
  --name v2hr-api \
  --resource-group v2hr-prod \
  --environment v2hr-env \
  --image v2hracr.azurecr.io/v2hr:latest \
  --target-port 8001 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 10 \
  --env-vars \
    MEDGEMMA_ENDPOINT=secretref:medgemma-endpoint \
    HF_TOKEN=secretref:hf-token

# 7. Configure secrets (from Key Vault)
az containerapp secret set \
  --name v2hr-api \
  --resource-group v2hr-prod \
  --secrets \
    medgemma-endpoint=keyvaultref:https://v2hr-kv.vault.azure.net/secrets/medgemma-endpoint \
    hf-token=keyvaultref:https://v2hr-kv.vault.azure.net/secrets/hf-token
```

---

## 4. Edge Deployment

### 4.1 Hardware Specifications

**Option A: Dedicated GPU Server**
| Component | Specification | Cost |
|-----------|---------------|------|
| GPU | NVIDIA L4 (24GB VRAM) | $900-1,200 |
| CPU | Intel Xeon / AMD EPYC (8+ cores) | $400-600 |
| RAM | 32GB DDR5 | $150-200 |
| Storage | 512GB NVMe SSD | $80-120 |
| **Total** | | **$1,530-2,120** |

**Option B: NVIDIA Jetson AGX Orin**
| Component | Specification | Cost |
|-----------|---------------|------|
| Jetson AGX Orin 64GB | 275 TOPS, 64GB unified memory | $1,999 |
| Power supply | Included | - |
| Enclosure | Fanless industrial (optional) | $200-400 |
| **Total** | | **$2,000-2,400** |

**Option C: Consumer GPU (Development/Small Practice)**
| Component | Specification | Cost |
|-----------|---------------|------|
| GPU | NVIDIA RTX 4090 (24GB VRAM) | $1,600-2,000 |
| Workstation | Dell/HP tower | $800-1,200 |
| **Total** | | **$2,400-3,200** |

### 4.2 Edge Software Stack

```bash
# Operating System
Ubuntu 22.04 LTS Server (NVIDIA drivers pre-installed)

# Container Runtime
Docker 24.x with NVIDIA Container Toolkit

# Inference Server
vLLM 0.3.x or Text Generation Inference (TGI)

# Model
google/medgemma-4b-it (8GB disk, 16GB VRAM at runtime)
```

### 4.3 Edge Deployment Steps

```bash
# 1. Install NVIDIA drivers (if not pre-installed)
sudo apt update
sudo apt install -y nvidia-driver-535 nvidia-container-toolkit

# 2. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 3. Configure NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 4. Pull MedGemma model (requires HuggingFace token)
export HF_TOKEN=hf_your_token
docker run --gpus all -e HF_TOKEN=$HF_TOKEN \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id google/medgemma-4b-it \
  --port 8080

# 5. Deploy v2hr API
docker run -d \
  --name v2hr-api \
  -p 8001:8001 \
  -e MEDGEMMA_BACKEND=local \
  -e MEDGEMMA_LOCAL_URL=http://host.docker.internal:8080 \
  v2hr:latest

# 6. Configure systemd for auto-start
sudo tee /etc/systemd/system/v2hr.service << EOF
[Unit]
Description=v2hr Clinical Extraction API
After=docker.service

[Service]
Restart=always
ExecStart=/usr/bin/docker start -a v2hr-api
ExecStop=/usr/bin/docker stop v2hr-api

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable v2hr
```

### 4.4 Edge Performance Benchmarks

| Hardware | Latency (p50) | Latency (p99) | Throughput |
|----------|---------------|---------------|------------|
| L4 GPU | 0.8s | 1.6s | 45 req/min |
| RTX 4090 | 0.6s | 1.2s | 55 req/min |
| Jetson Orin | 1.2s | 2.4s | 30 req/min |
| Cloud (L4) | 2.1s | 4.8s | Unlimited |

---

## 5. Hybrid Deployment

### 5.1 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Hybrid Architecture                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        API Gateway (Nginx/Traefik)                   │    │
│  │                     Routes based on request priority                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                    │                                    │                    │
│                    ▼                                    ▼                    │
│  ┌──────────────────────────────┐    ┌──────────────────────────────┐       │
│  │       Edge Cluster            │    │       Cloud Burst             │       │
│  │  ┌────────────────────────┐  │    │  ┌────────────────────────┐  │       │
│  │  │  v2hr + Local MedGemma │  │    │  │  v2hr + HF Endpoint    │  │       │
│  │  │  Priority: STAT/Real-time│  │    │  │  Priority: Batch/Overflow│  │       │
│  │  └────────────────────────┘  │    │  └────────────────────────┘  │       │
│  └──────────────────────────────┘    └──────────────────────────────┘       │
│                                                                              │
│  Routing Rules:                                                              │
│  - workflow=emergency → Edge (lowest latency)                               │
│  - workflow=batch → Cloud (cost-effective)                                  │
│  - Edge at capacity → Overflow to Cloud                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Routing Configuration

```yaml
# traefik.yml
http:
  routers:
    v2hr-edge:
      rule: "PathPrefix(`/api/v1/extract`) && HeadersRegexp(`X-Workflow`, `emergency|stat`)"
      service: v2hr-edge
      priority: 100

    v2hr-cloud:
      rule: "PathPrefix(`/api/v1/extract`)"
      service: v2hr-cloud
      priority: 50

  services:
    v2hr-edge:
      loadBalancer:
        servers:
          - url: "http://edge-server:8001"
        healthCheck:
          path: /health
          interval: 10s

    v2hr-cloud:
      loadBalancer:
        servers:
          - url: "https://v2hr-api.azurecontainerapps.io"
```

---

## 6. EHR Integration

### 6.1 Epic Integration

**FHIR R4 REST API:**
```bash
# Submit extracted data as FHIR Bundle
curl -X POST https://epic-fhir-server/api/FHIR/R4/Bundle \
  -H "Authorization: Bearer $EPIC_TOKEN" \
  -H "Content-Type: application/fhir+json" \
  -d @extracted_bundle.json
```

**CDA Import (Chart Import):**
- Configure Epic Chart Import to watch designated folder
- v2hr outputs CDA documents to import folder
- Epic processes on schedule (typically every 5 minutes)

### 6.2 Cerner/Oracle Health Integration

**HL7 v2.x Interface:**
```bash
# Send HL7 message via MLLP
echo -e "\x0B$(cat extracted.hl7)\x1C\x0D" | nc cerner-interface 2575
```

**FHIR R4:**
```bash
curl -X POST https://cerner-fhir/r4/Bundle \
  -H "Authorization: Bearer $CERNER_TOKEN" \
  -H "Content-Type: application/fhir+json" \
  -d @extracted_bundle.json
```

### 6.3 Generic FHIR Server

Compatible with any FHIR R4 server:
- HAPI FHIR (open source)
- Microsoft Azure API for FHIR
- Google Cloud Healthcare API
- AWS HealthLake

---

## 7. Security & Compliance

### 7.1 HIPAA Technical Safeguards

| Safeguard | Implementation | Status |
|-----------|----------------|--------|
| **Access Control** | API key authentication, RBAC | ✅ Implemented |
| **Audit Controls** | Structured JSON logging, request tracing | ✅ Implemented |
| **Integrity Controls** | TLS 1.3 in transit, checksums | ✅ Implemented |
| **Transmission Security** | HTTPS only, certificate pinning | ✅ Implemented |
| **Encryption at Rest** | Edge: full disk encryption; Cloud: provider-managed | ✅ Configurable |

### 7.2 Data Handling

```
PHI Flow:
1. Transcript received via HTTPS (encrypted in transit)
2. Processed in memory (never written to disk)
3. Structured output returned via HTTPS
4. No PHI retained after request completion

Cloud Deployment:
- BAA required with HuggingFace (Inference Endpoints)
- BAA required with Azure (Container Apps, Key Vault)
- Consider edge deployment for maximum privacy

Edge Deployment:
- All processing on-premises
- No PHI leaves organization network
- Full control over data retention
```

### 7.3 Audit Logging

```json
{
  "timestamp": "2026-01-30T15:04:05.123Z",
  "request_id": "uuid-here",
  "endpoint": "/api/v1/extract",
  "workflow": "emergency",
  "user_id": "provider-123",
  "client_ip": "10.0.1.50",
  "response_status": 200,
  "latency_ms": 2341,
  "entities_extracted": {
    "conditions": 3,
    "medications": 5,
    "orders": 2
  }
}
```

---

## 8. Monitoring & Alerting

### 8.1 Key Metrics

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| API Latency (p99) | >5s | >10s | Scale up / investigate |
| Error Rate | >1% | >5% | Investigate logs |
| GPU Utilization | >80% | >95% | Add capacity |
| Memory Usage | >80% | >95% | Restart / investigate |
| Extraction Accuracy | <95% | <90% | Model investigation |

### 8.2 Health Checks

```bash
# API health endpoint
GET /health

# Expected response
{
  "status": "healthy",
  "medgemma_available": true,
  "version": "1.0.0"
}

# Kubernetes liveness probe
livenessProbe:
  httpGet:
    path: /health
    port: 8001
  initialDelaySeconds: 30
  periodSeconds: 10

# Kubernetes readiness probe
readinessProbe:
  httpGet:
    path: /health
    port: 8001
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## 9. Disaster Recovery

### 9.1 Backup Strategy

| Component | Backup Frequency | Retention | Method |
|-----------|------------------|-----------|--------|
| Configuration | On change | 90 days | Git repository |
| Secrets | On change | 90 days | Key Vault versioning |
| Audit Logs | Continuous | 7 years | Log Analytics / S3 |
| Model Weights | On update | 3 versions | Container registry |

### 9.2 Recovery Procedures

**Cloud Failure:**
1. Automatic failover to secondary region (if configured)
2. Manual: Re-deploy from container registry
3. RTO: 15 minutes

**Edge Failure:**
1. Automatic restart via systemd
2. Manual: Re-image from backup
3. RTO: 30 minutes (with spare hardware), 4 hours (procurement)

---

## 10. Capacity Planning

### 10.1 Sizing Guidelines

| Practice Size | Daily Extractions | Recommended Deployment |
|---------------|-------------------|------------------------|
| Solo practice | 25-50 | Cloud |
| Small clinic (5 providers) | 125-250 | Cloud or Edge |
| Medium clinic (20 providers) | 500-1,000 | Edge |
| Hospital department | 1,000-5,000 | Edge cluster |
| Enterprise (multi-site) | 10,000+ | Hybrid |

### 10.2 Cost Comparison (Monthly)

| Volume | Cloud Cost | Edge Cost | Break-even |
|--------|------------|-----------|------------|
| 500/mo | $50-75 | $2,000 (one-time) + $50 | 40 months |
| 2,000/mo | $95-155 | $2,000 (one-time) + $50 | 16 months |
| 10,000/mo | $335-555 | $2,000 (one-time) + $100 | 5 months |
| 50,000/mo | $1,535-2,555 | $5,000 (one-time) + $200 | 3 months |

---

## 11. Support & Maintenance

### 11.1 Update Schedule

| Component | Update Frequency | Process |
|-----------|------------------|---------|
| v2hr API | Monthly | Rolling deployment |
| MedGemma model | Quarterly | Staged rollout with validation |
| OS/Dependencies | Monthly | Security patches |
| Terminology databases | Quarterly | RxNorm/ICD-10 annual releases |

### 11.2 Support Channels

- **Documentation:** https://github.com/paulgCleansheet/voice-to-health-record
- **Issues:** GitHub Issues
- **Security:** security@cleansheet.info

---

## Appendix A: Quick Reference Commands

```bash
# Health check
curl http://localhost:8001/health

# Extract from transcript
curl -X POST http://localhost:8001/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Patient has hypertension on lisinopril 10mg daily.", "workflow": "general"}'

# Transform to FHIR
curl -X POST http://localhost:8001/api/v1/transform \
  -H "Content-Type: application/json" \
  -d '{"extracted_data": {...}, "format": "fhir-r4"}'

# View logs
docker logs -f v2hr-api

# Restart service
sudo systemctl restart v2hr
```

---

**Document Version:** 1.0
**Last Updated:** January 30, 2026
**Author:** Cleansheet LLC
