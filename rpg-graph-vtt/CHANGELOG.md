# Changelog

## [0.1.0] - December 2024

### Added
- Initial MVP implementation of graph-powered D&D 5e character management system
- Neo4j graph database schema with constraints and indexes
- Character, Party, and Game System data models (Pydantic)
- Graph query builders for all CRUD operations
- D&D 5e data seeding (12 classes, 15+ races, 12 backgrounds, sample spells)
- Character creation workflow (Jupyter notebook)
- Party viewing and management
- Foundry VTT import/export converters
- Game Master (GM) Agent for rules lookup
- Character Assistant Agent for character creation help
- FastAPI web server with REST API
- HTML/CSS/JS frontend for character sheet viewing
- Docker integration and deployment scripts

### Fixed
- Neo4j transaction scope issues (ResultConsumedError)
- Neo4j API compatibility (updated to use `execute_read()` and `execute_write()`)
- Docker mount path resolution
- Module import paths for web server

### Changed
- Renamed "Rules Lookup Agent" to "Game Master (GM) Agent" for better D&D terminology
- Compacted setup notebook into single cell for easier execution
- Updated dependencies to include FastAPI and uvicorn

### Technical Details
- Neo4j 6.x API compatibility
- Python 3.10+ support
- FastAPI async endpoints
- Pydantic v2 data validation
- Google ADK integration for AI agents

### Known Issues
- Port 8000 needs to be exposed in docker-compose.yml for external access
- Comprehensive test suite not yet implemented
- Performance optimization pending

### Next Steps
- Add comprehensive unit and integration tests
- Implement character editing interface
- Add spell management UI
- Implement inventory management
- Add dice roller integration
- Real-time collaboration features

