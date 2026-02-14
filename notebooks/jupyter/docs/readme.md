# Nebula Documentation Index

**Last Updated:** 2025-01-27  
**Status:** Comprehensive documentation refresh in progress

## Navigation

### Core Documentation
- [Project Specifications](./specs/) - Technical specifications and requirements
- [Requirements & User Stories](./requirements/) - Business requirements and user narratives  
- [Risk Registry](./risks/) - Project risks and mitigation strategies
- [Development Guides](./development/) - Development workflows and standards

### System Architecture
- [Architecture Overview](./architecture/overview.md) - Complete system architecture
- [Infrastructure Decisions](./architecture/infrastructure.md) - Infrastructure and deployment choices
- [API Documentation](./architecture/api.md) - API specifications and usage

### Quick Starts
- [Development Setup](../README.md#development-environment-setup) - Get started in 5 minutes
- [ASR Evaluation Quick Start](../README.md#asr-evaluation-quick-start) - ASR benchmarking guide
- [Media Platform Quick Start](../media-platform/README.md) - Media platform setup

---

## Project Overview

The **Nebula Jupyter System** is a comprehensive development environment for AI/ML workflows with focus on:

1. **ASR (Automatic Speech Recognition) Evaluation** - Production-ready model benchmarking
2. **E-commerce Product Tracking** - Multi-platform product monitoring and style detection
3. **Media Platform** - Graph-based media management with caching
4. **ComfyUI Integration** - Automated image generation workflows

### Key Technologies

- **Data Layer:** Neo4j (graph), PostgreSQL + pgvector (relational), MinIO/S3 (object storage), Valkey (cache)
- **Development:** Docker DevContainers, JupyterLab, VS Code integration
- **Infrastructure:** RunPod GPU instances, OpenRouter API access
- **Monitoring:** Comprehensive caching and performance metrics

### Documentation Structure

```
docs/
├── README.md                    # This file - navigation index
├── specs/                       # Technical specifications
│   ├── system-overview.md       # Complete system specification
│   ├── asr-evaluation.md        # ASR evaluation specifications
│   ├── ecommerce-tracking.md    # E-commerce tracking specifications
│   └── media-platform.md        # Media platform specifications
├── requirements/                 # Business requirements
│   ├── overview.md              # Requirements overview and priorities
│   ├── functional.md            # Functional requirements
│   ├── non-functional.md        # Non-functional requirements
│   └── user-stories.md          # User stories and acceptance criteria
├── risks/                       # Risk management
│   ├── registry.md              # Master risk registry
│   ├── mitigation.md            # Mitigation strategies
│   └── monitoring.md            # Risk monitoring procedures
├── development/                 # Development guides
│   ├── workflow.md              # Development workflow and standards
│   ├── testing.md               # Testing strategies and procedures
│   ├── refactoring.md           # Refactoring guidelines
│   └── deployment.md            # Deployment procedures and checklists
└── architecture/                # Architecture documentation
    ├── overview.md              # System architecture overview
    ├── infrastructure.md        # Infrastructure decisions
    ├── data-model.md            # Data models and schemas
    └── api.md                   # API documentation
```

### Getting Started

1. **New Developers** - Start with [Development Setup](../README.md#development-environment-setup)
2. **Feature Development** - Begin with [Requirements Overview](./requirements/overview.md)
3. **Architecture Review** - Read [Architecture Overview](./architecture/overview.md)
4. **Risk Assessment** - Check [Risk Registry](./risks/registry.md)

### Documentation Standards

- **No Emojis** - Organization policy prohibits emoji usage
- **Consistent Formatting** - Markdown with clear section hierarchy
- **Regular Updates** - All docs dated and status-tracked
- **Cross-References** - Comprehensive linking between related docs

### Contribution Process

1. Create user stories for new features (see [User Stories Guide](./development/user-stories.md))
2. Update relevant specifications during development
3. Document architectural decisions (see [Architecture Decisions](../docs/ARCHITECTURE_DECISIONS.md))
4. Update risk registry for new issues identified
5. Keep documentation current with code changes

---

## System Status

### ASR Evaluation Framework
- **Status:** Production Ready
- **Models:** FasterWhisper, OLMoASR, OpenAI Whisper
- **Metrics:** WER, CER, BLEU scores, processing time
- **Roadmap:** 5 phases through production deployment (see [Main README](../README.md#asr-hearing-benchmark-roadmap))

### E-commerce Product Tracking
- **Status:** Core Features Implemented
- **Platforms:** Depop, Shopify (eBay/Poshmark planned)
- **Features:** Price tracking, style detection, product matching
- **User Stories:** 15 defined, 8 implemented (see [User Stories](../docs/USER_STORIES.md))

### Media Platform
- **Status:** Production-Ready Architecture
- **Performance:** <1ms cached responses, 100x throughput improvement
- **Storage:** Neo4j + Valkey + S3-compatible storage
- **Scaling:** Horizontal scaling path defined

### Risk Management
- **Critical Risks:** 2 identified (1 mitigated, 1 open)
- **High Risks:** 3 identified (1 mitigated, 2 open)
- **Registry Location:** [Risk Registry](../RISK_REGISTRY.md)
- **Monitoring:** Automated build health checks implemented

---

## Contact & Support

- **Issues:** GitHub Issues for bugs and feature requests
- **Documentation PRs:** Submit changes via pull requests
- **Architecture Questions:** Create GitHub issue with "architecture" label
- **Urgent Issues:** Contact team directly (see team chat)

**Last Reviewed:** 2025-01-27  
**Next Review:** 2025-02-03