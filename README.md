# AI Platform Reference Architecture + AI Gateway implementation

This repository contains both the reference architecture and the initial implementation of an AI Governance Gateway, which serves as the first executable component of the platform.

The reference architecture use is to set a foundation to designing and building a modern AI platform, focused on patterns such as Retrieval-Augmented Generation (RAG), orchestration, model routing, and observability.

The goal is to understand how AI systems evolve from simple applications into reusable, scalable platforms.

- docs/   → architecture and design artifacts
- app/    → gateway service implementation
- infra/  → Terraform infrastructure for GCP

---

## 🛣️ Roadmap

- [x] Phase 1: Reference architecture  
  - [x] Define platform layers (infra → app)  
  - [x] Map request flow end-to-end  
  - [x] Control plane vs data plane  
  - [x] Design principles and tradeoffs  

- [x] Phase 2: Dev setup (local run + config)  
  - [x] Python environment + dependencies  
  - [x] Local config (.env)  
  - [x] Docker local run  
  - [x] Repo structure + workflow  

- [x] Phase 3: Infra (GCP + Terraform + Cloud Run + secrets)  
  - [x] GCP project + service enablement  
  - [x] IAM + service accounts  
  - [x] Secret Manager wiring  
  - [x] Cloud Run base service  
  - [x] Terraform-managed resources  

- [x] Phase 4: Gateway skeleton (FastAPI baseline deployed)  
  - [x] FastAPI app scaffold  
  - [x] `/health` endpoint  
  - [x] `/query` endpoint (placeholder)  
  - [x] Dockerfile + container build  
  - [x] Deploy to Cloud Run  

- [x] Phase 5: Model integration (LLM call working end-to-end)  
  - [x] Provider abstraction layer  
  - [x] API key via secrets  
  - [x] Prompt → response flow  
  - [x] Response parsing + error handling  
  - [x] End-to-end validation  

- [x] Phase 6: Routing (model selection + basic policies)  
  - [x] Model selection logic  
  - [x] Request classification  
  - [x] Default + fallback behavior  
  - [x] Approved model list  
  - [x] Cost/latency-aware decisions  

- [x] Phase 7: Governance (validation + PII/basic filtering)  
  - [x] Input validation  
  - [x] PII detection (regex)  
  - [x] Masking / redaction  
  - [x] Prompt inspection  
  - [x] Unsafe input handling  

- [ ] Phase 8: Observability (logs + error visibility)  
  - [ ] Structured logging  
  - [ ] Request/response logs  
  - [ ] Error tracking  
  - [ ] Basic tracing  
  - [ ] Audit logs  

- [ ] Phase 9: Hardening (env config + reliable deploys)  
  - [ ] Env configs (dev/prod)  
  - [ ] Config validation  
  - [ ] Retries + timeouts  
  - [ ] Deploy consistency  
  - [ ] Cleanup + refactor  

- [ ] Phase 10: UI / Visual Dashboard
  - [ ] Real-time query visualiser
  - [ ] Animated architecture diagram
  - [ ] Each platform layer highlights as request flows through
  - [ ] Model selection shown inline
  - [ ] Policy decisions surfaced visually
  - [ ] Latency per layer displayed
  - [ ] Built with Claude Code

- [ ] Phase 11: RAG + Vector DB
  - [ ] Vector DB (Vertex AI Vector Search)
  - [ ] Document ingestion pipeline
  - [ ] Chunking + embeddings
  - [ ] Retrieval layer wired into gateway
  - [ ] UI extended to show retrieval flow

---

## 🧠 Overview

Modern AI systems are increasingly structured as **distributed platforms** rather than isolated applications.

They combine multiple capabilities:

- Retrieval systems (vector databases, embeddings)
- Model inference (LLMs)
- Orchestration workflows
- Model routing and policies
- Observability and evaluation
- Governance and security

This repository explores how these components fit together in a **layered architecture**.

---

## 🏗️ Architecture

![AI Platform Architecture](./docs/diagrams/reference-architecture-layers.png)

The platform is organized into four main layers:

- **AI Application Layer** → user experience, prompts, agents  
- **AI System Layer** → orchestration, RAG workflows, tools  
- **AI Platform Layer** → model routing, inference, retrieval, data platform  
- **Infrastructure Layer** → cloud, compute, security, observability  

---

## 🔑 Key Concepts

### Retrieval-Augmented Generation (RAG)
Combining LLMs with external knowledge sources to improve accuracy and grounding.

### Orchestration
Coordinating workflows between retrieval, models, and tools.

### Model Gateway / Routing
Selecting models dynamically based on cost, latency, or capability.

### Observability & Evaluation
Monitoring prompts, responses, and system behavior to improve quality and reliability.

---

## 📚 Documentation

Full reference architecture:

👉 [docs/reference-architecture.md](./docs/reference-architecture.md)

---

## 🎯 Goals

This project focuses on:

- Understanding AI platform architecture patterns
- Exploring how systems evolve from prototype → production → platform
- Designing reusable infrastructure for multiple AI use cases

---

## 🚀 Future Work

- Agentic workflows and tool usage
- Multi-model routing strategies
- Evaluation frameworks for LLM systems
- Advanced retrieval (hybrid, graph-based)

---

## 👋 About

This repository is part of a series exploring how to design and build AI platforms from the ground up.

Follow the journey on LinkedIn: https://www.linkedin.com/in/paugonzalezr/
