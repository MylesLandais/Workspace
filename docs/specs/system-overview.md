# System Specifications Overview

**Last Updated:** 2025-01-27  
**Version:** 1.0  
**Status:** Production-Ready Specifications

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Specifications](#component-specifications)
3. [Integration Requirements](#integration-requirements)
4. [Performance Specifications](#performance-specifications)
5. [Security Specifications](#security-specifications)

---

## System Overview

The Nebula Jupyter System is a comprehensive AI/ML development environment comprising four primary components:

### Primary Components

1. **ASR Evaluation Framework**
   - Purpose: Production-ready speech recognition model benchmarking
   - Models: FasterWhisper, OLMoASR, OpenAI Whisper via OpenRouter
   - Metrics: WER, CER, BLEU scores, processing time analysis
   - Storage: PostgreSQL with pgvector for results and leaderboards

2. **E-commerce Product Tracking System**
   - Purpose: Multi-platform product monitoring and garment style detection
   - Platforms: Depop, Shopify (planned: eBay, Poshmark, Mercari)
   - Features: Price tracking, style detection, product matching
   - Storage: Neo4j graph database for relationships

3. **Media Platform**
   - Purpose: High-performance media management and serving
   - Architecture: Express API + Neo4j + Valkey cache + S3 storage
   - Performance: <1ms cached responses, 100x throughput improvement
   - Scaling: Horizontal scaling with Valkey cluster

4. **ComfyUI Integration**
   - Purpose: Automated image generation workflows
   - Infrastructure: RunPod GPU instances with Google ADK orchestration
   - Features: Batch testing, infrastructure-as-code deployment
   - Management: Automated instance lifecycle management

---

## Component Specifications

### ASR Evaluation Framework

#### Technical Requirements
- **Container Environment:** Docker with CUDA support
- **Python Version:** 3.9+
- **Dependencies:** faster-whisper, transformers, torch, psycopg2-binary
- **Database:** PostgreSQL 14+ with pgvector extension
- **Test Dataset:** Vaporeon Copypasta (164 seconds, known transcription)

#### API Specification
```python
# Model Adapter Interface
class ASRModelAdapter:
    def transcribe(self, audio_path: str) -> TranscriptionResult
    def get_model_info(self) -> ModelInfo
    def is_available(self) -> bool

# Evaluation Metrics
class EvaluationMetrics:
    wer: float  # Word Error Rate
    cer: float  # Character Error Rate
    bleu: float  # BLEU score
    processing_time: float  # Seconds
    audio_duration: float  # Seconds
```

#### Performance Targets
- **Real-time Factor (RTF):** <0.5x (faster than real-time)
- **Memory Usage:** <2GB per model instance
- **Concurrent Evaluations:** 4+ models simultaneously
- **Accuracy Target:** WER <25% on test dataset

### E-commerce Product Tracking

#### Technical Requirements
- **Graph Database:** Neo4j 5.0+ with APOC plugins
- **Web Scraping:** BeautifulSoup4, requests, selenium
- **Image Processing:** Pillow, OpenCV for style detection
- **Storage:** MinIO/GCP Cloud Storage for images
- **Cache:** Valkey for product data caching

#### Data Model Specification
```cypher
// Product Schema
CREATE (p:Product {
    id: String,
    title: String,
    price: Float,
    currency: String,
    platform: String,
    url: String,
    image_url: String,
    created_at: DateTime,
    updated_at: DateTime
})

// Price History Schema
CREATE (ph:PriceHistory {
    price: Float,
    currency: String,
    recorded_at: DateTime
})

// Garment Style Schema
CREATE (gs:GarmentStyle {
    id: String,
    name: String,
    category: String,
    features: [String],
    confidence: Float
})
```

#### Platform Specifications
- **Depop:** Product scraping, price history, image extraction
- **Shopify:** Store integration, product catalog sync
- **Reddit:** Gallery post extraction, link analysis
- **Future:** eBay, Poshmark, Mercari API integration

### Media Platform

#### Architecture Stack
- **API Layer:** Express.js with async/await
- **Authentication:** JWT-based auth with refresh tokens
- **Database:** Neo4j with relationship queries
- **Cache:** Valkey with 5-minute default TTL
- **Storage:** S3-compatible (MinIO dev, R2 staging, GCP prod)

#### API Endpoints Specification
```javascript
// Media Management
GET    /api/media/:id              // Get media with metadata
POST   /api/media                  // Upload new media
PUT    /api/media/:id              // Update media metadata
DELETE /api/media/:id              // Delete media

// Collections
GET    /api/collections/:id        // Get collection
POST   /api/collections            // Create collection
PUT    /api/collections/:id        // Update collection
DELETE /api/collections/:id        // Delete collection

// Search & Discovery
GET    /api/search/media           // Search media
GET    /api/search/collections     // Search collections
```

#### Performance Specification
- **Cache Hit Rate:** >90% in production
- **Response Time:** <1ms cached, <200ms uncached
- **Throughput:** 5,000+ requests/second
- **Storage Scalability:** 1TB+ with automatic migration

### ComfyUI Integration

#### Infrastructure Requirements
- **GPU Providers:** RunPod with on-demand instances
- **Models:** Custom checkpoints, LoRA embeddings, ControlNet
- **Orchestration:** Google ADK for agent workflows
- **Storage:** Network volumes for model persistence
- **Monitoring:** Real-time pod status and job tracking

#### Workflow Specification
```python
# Deployment Configuration
@dataclass
class ComfyUIConfig:
    gpu_type: str  # "RTX_3090", "RTX_4090", "A100"
    gpu_count: int
    storage_volume: str
    docker_image: str
    environment_variables: Dict[str, str]
    
# Agent Workflow
class ComfyUIAgent:
    def generate_image(self, prompt: str, workflow: dict) -> ImageResult
    def schedule_batch(self, prompts: List[str]) -> BatchResult
    def monitor_jobs(self) -> JobStatus
```

---

## Integration Requirements

### Data Flow Architecture

```
ASR Framework → PostgreSQL (Leaderboard Data)
                   ↓
E-commerce → Neo4j (Product Graph) → Valkey (Cache) → S3 Storage (Images)
                   ↓
Media Platform → Express API → Client Applications
                   ↓
ComfyUI → RunPod GPU → Results Storage → Media Platform
```

### Authentication & Authorization
- **ASR Framework:** Local development, no auth required
- **E-commerce Tracking:** Neo4j auth with role-based permissions
- **Media Platform:** JWT tokens with refresh mechanism
- **ComfyUI Integration:** RunPod API key + Google ADK auth

### API Integration Points
- **Neo4j as Central Graph:** Product relationships, media metadata
- **PostgreSQL for Analytics:** ASR results, performance metrics
- **Valkey for Performance:** Cross-system caching layer
- **S3 for Media:** Unified storage for images, videos, models

---

## Performance Specifications

### Response Time Targets

| Component | Target | Current | Notes |
|-----------|--------|---------|-------|
| ASR Transcription | <2x real-time | ~2-3s | RTX 3090, base models |
| Product Search | <100ms | <1ms (cached) | Neo4j + Valkey |
| Media Serving | <50ms | <1ms (cached) | Direct S3 serving |
| Image Generation | <30s | 15-45s | Depends on complexity |

### Scalability Targets

| Metric | Target | Implementation |
|--------|--------|----------------|
| Concurrent Users | 10,000+ | Valkey clustering |
| ASR Evaluations | 50/hour | GPU instance scaling |
| Product Tracking | 1M products | Neo4j Aura scaling |
| Media Storage | 10TB+ | S3 auto-scaling |

### Availability Requirements

| Component | Target Uptime | Monitoring |
|-----------|---------------|------------|
| ASR Framework | 99% (dev) | Manual checks |
| Neo4j Graph | 99.9% | Aura monitoring |
| Media API | 99.95% | Health checks |
| ComfyUI Jobs | 95% completion | Job tracking |

---

## Security Specifications

### Data Protection
- **Encryption:** TLS 1.3 for all external connections
- **Storage Encryption:** S3-managed keys at rest
- **API Security:** Rate limiting, input validation
- **Secrets Management:** Environment variables, no hardcoded secrets

### Access Control
- **Development:** Local access only, no authentication
- **Staging:** Role-based access with audit logging
- **Production:** OAuth 2.0 + RBAC with principle of least privilege

### Compliance Requirements
- **Data Privacy:** No PII storage, user data anonymization
- **API Rate Limits:** 100 req/min per user, 1000 req/min global
- **Data Retention:** 90 days for logs, configurable for user data
- **Security Scanning:** Talisman pre-commit hooks for secrets

---

## Quality Assurance

### Testing Requirements
- **Unit Tests:** >80% code coverage for critical paths
- **Integration Tests:** API endpoints, database operations
- **Performance Tests:** Load testing for 1000+ concurrent users
- **Security Tests:** Automated vulnerability scanning

### Monitoring & Observability
- **Health Checks:** /health endpoints for all services
- **Performance Metrics:** Response times, error rates, cache hit ratios
- **Resource Monitoring:** CPU, memory, disk, network utilization
- **Business Metrics:** User engagement, feature usage, error patterns

---

## Implementation Status

| Component | Status | Completion | Next Steps |
|-----------|--------|------------|------------|
| ASR Framework | Production Ready | 100% | Phase 2 testing |
| E-commerce Core | Implemented | 80% | CV model integration |
| Media Platform | Production Ready | 100% | Scale monitoring |
| ComfyUI Integration | Beta | 70% | Production deployment |

---

**Document Version:** 1.0  
**Last Reviewed:** 2025-01-27  
**Next Review:** 2025-02-10  
**Reviewers:** Development Team, Architecture Committee