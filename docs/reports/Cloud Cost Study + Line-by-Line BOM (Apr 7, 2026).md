# SmartLawer_V2 Cloud Cost Study + Line-by-Line BOM

Date: April 7, 2026
Author: Codex
Purpose: Estimate monthly hosting costs for SmartLawer_V2 as-is and with Docling integrated, with line-by-line bill of materials by cloud.

## 1) Scope and Assumptions

This report estimates infrastructure cost only.

Included:
- Frontend hosting
- Backend API runtime
- Worker runtime (Celery/background jobs)
- Managed PostgreSQL
- Managed Redis
- Object storage
- Monitoring/logging baseline
- Network/egress reserve

Excluded:
- LLM/API consumption (OpenAI/OpenRouter/Azure OpenAI)
- Human support/operations salaries
- Taxes and currency fluctuation effects

General assumptions:
- Baseline geography: US East / us-east-1 / us-central1 pricing classes.
- 730 hours/month for compute.
- Small production pilot for legal workflows (not large enterprise scale).
- Values are budgetary ranges for planning, not formal quotes.

## 2) Summary of Monthly Cost Ranges (USD)

### 2.1 SmartLawer_V2 without Docling

| Cloud | Lean/MVP | Safer Pilot/Production-Ready |
|---|---:|---:|
| Azure | $180 - $320 | $320 - $550 |
| AWS | $160 - $290 | $290 - $500 |
| GCP | $150 - $270 | $260 - $460 |

### 2.2 SmartLawer_V2 with Docling (CPU mode)

| Cloud | Additional Cost from Docling | Total Cost |
|---|---:|---:|
| Azure | +$120 - $260 | $440 - $810 |
| AWS | +$110 - $240 | $400 - $740 |
| GCP | +$100 - $230 | $360 - $690 |

### 2.3 SmartLawer_V2 with Docling (GPU-assisted mode)

| Cloud | Additional Cost from Docling GPU Layer | Total Cost |
|---|---:|---:|
| Azure | +$380 - $900 | $800 - $1,700+ |
| AWS | +$350 - $850 | $750 - $1,550+ |
| GCP | +$320 - $800 | $680 - $1,450+ |

## 3) Line-by-Line BOM

## 3.1 Azure BOM (USD/month)

### A) Without Docling

| Item | MVP | Pilot |
|---|---:|---:|
| Frontend host (Static Web Apps / App Service small) | $10 - $25 | $20 - $50 |
| API compute (Container Apps or VM/App Service) | $40 - $90 | $80 - $160 |
| Worker compute (Celery) | $35 - $80 | $70 - $150 |
| Azure Database for PostgreSQL (managed) | $30 - $70 | $60 - $140 |
| Azure Cache for Redis (managed) | $20 - $45 | $35 - $80 |
| Blob Storage (docs + generated files) | $10 - $35 | $25 - $70 |
| Monitoring + logs (Azure Monitor/App Insights) | $10 - $25 | $20 - $50 |
| Egress/network reserve | $10 - $20 | $15 - $30 |
| Total | $180 - $320 | $320 - $550 |

### B) With Docling CPU

Add:

| Item | MVP Add | Pilot Add |
|---|---:|---:|
| Docling service compute (CPU) | $70 - $150 | $120 - $220 |
| Extra storage/logging from conversions | $15 - $40 | $20 - $40 |
| Total Add | $120 - $260 | $140 - $260 |

### C) With Docling GPU

Replace CPU add with:

| Item | MVP Add | Pilot Add |
|---|---:|---:|
| GPU node/runtime for Docling workloads | $320 - $760 | $450 - $900 |
| Extra storage/logging | $20 - $40 | $25 - $50 |
| Total Add | $380 - $800 | $500 - $950 |

## 3.2 AWS BOM (USD/month)

### A) Without Docling

| Item | MVP | Pilot |
|---|---:|---:|
| Frontend host (S3 + CloudFront or Amplify) | $8 - $25 | $15 - $45 |
| API compute (ECS/Fargate or EC2) | $35 - $85 | $70 - $150 |
| Worker compute (ECS/EC2) | $30 - $75 | $60 - $140 |
| RDS PostgreSQL | $25 - $65 | $50 - $130 |
| ElastiCache Redis | $20 - $45 | $35 - $75 |
| S3 storage | $8 - $30 | $20 - $60 |
| CloudWatch logs/metrics | $10 - $25 | $20 - $45 |
| Egress/network reserve | $10 - $20 | $15 - $30 |
| Total | $160 - $290 | $290 - $500 |

### B) With Docling CPU

Add:

| Item | MVP Add | Pilot Add |
|---|---:|---:|
| Docling service compute (CPU) | $60 - $140 | $100 - $200 |
| Extra storage/logging from conversions | $15 - $35 | $20 - $40 |
| Total Add | $110 - $220 | $130 - $240 |

### C) With Docling GPU

Replace CPU add with:

| Item | MVP Add | Pilot Add |
|---|---:|---:|
| GPU node/runtime for Docling workloads | $300 - $720 | $420 - $850 |
| Extra storage/logging | $20 - $35 | $20 - $40 |
| Total Add | $350 - $760 | $450 - $890 |

## 3.3 GCP BOM (USD/month)

### A) Without Docling

| Item | MVP | Pilot |
|---|---:|---:|
| Frontend host (Firebase Hosting/Cloud Run static) | $8 - $20 | $15 - $40 |
| API compute (Cloud Run/GCE) | $30 - $80 | $65 - $140 |
| Worker compute (Cloud Run Jobs/GCE) | $30 - $70 | $55 - $130 |
| Cloud SQL PostgreSQL | $25 - $60 | $50 - $120 |
| Memorystore Redis | $20 - $40 | $30 - $70 |
| Cloud Storage | $8 - $25 | $15 - $55 |
| Cloud Logging/Monitoring | $10 - $20 | $15 - $35 |
| Egress/network reserve | $10 - $15 | $15 - $25 |
| Total | $150 - $270 | $260 - $460 |

### B) With Docling CPU

Add:

| Item | MVP Add | Pilot Add |
|---|---:|---:|
| Docling service compute (CPU) | $55 - $130 | $90 - $190 |
| Extra storage/logging from conversions | $15 - $30 | $20 - $40 |
| Total Add | $100 - $200 | $120 - $230 |

### C) With Docling GPU

Replace CPU add with:

| Item | MVP Add | Pilot Add |
|---|---:|---:|
| GPU node/runtime for Docling workloads | $280 - $680 | $380 - $800 |
| Extra storage/logging | $20 - $30 | $20 - $35 |
| Total Add | $320 - $710 | $400 - $835 |

## 4) LLM Cost Layer (Important, Separate)

Infrastructure is not your only cost. AI model usage can become the biggest line item quickly.

Practical planning reserve:
- Light pilot: $100 - $300/month
- Moderate pilot: $300 - $900/month
- Heavy production usage: $900 - $3,000+/month

This depends on:
- Number of documents/month
- Average pages per document
- Prompt size and response size
- Chosen model/provider

## 5) Budgeting Recommendation

For immediate hosting decisions:

1. If launching now without Docling:
- Plan budget at $300 - $500/month for safer pilot operation.

2. If launching with Docling CPU:
- Plan budget at $450 - $750/month.

3. If considering Docling GPU:
- Plan budget at $800 - $1,600+/month.

4. Add model usage budget reserve:
- Start with +$300/month and adjust after first 2 to 4 weeks of telemetry.

## 6) Sources Used

Docling:
- https://github.com/docling-project/docling
- https://docling-project.github.io/docling/v2/
- https://github.com/docling-project/docling-serve
- https://pypi.org/project/docling/

Cloud pricing references:
- Azure pricing pages (VM/PostgreSQL/Redis/Storage/ML)
- AWS pricing pages (EC2/RDS/ElastiCache/S3)
- GCP pricing pages (Compute Engine/Cloud SQL/Memorystore/Cloud Storage)

Note:
- Prices vary by exact region/SKU, committed use, and discounts.
- This study should be refined into a quote with exact SKUs before procurement.
