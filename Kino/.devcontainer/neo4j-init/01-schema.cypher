// Neo4j Schema Initialization Script
// This script creates constraints for the D&D Character Creator application
// It is idempotent and safe to run multiple times

// Unique constraint on character ID
CREATE CONSTRAINT character_id_unique IF NOT EXISTS
FOR (c:Character) REQUIRE c.id IS UNIQUE;

// Unique constraint on race name
CREATE CONSTRAINT race_name_unique IF NOT EXISTS
FOR (r:Race) REQUIRE r.name IS UNIQUE;

// Unique constraint on class name
CREATE CONSTRAINT class_name_unique IF NOT EXISTS
FOR (cl:Class) REQUIRE cl.name IS UNIQUE;

// Unique constraint on background name
CREATE CONSTRAINT background_name_unique IF NOT EXISTS
FOR (b:Background) REQUIRE b.name IS UNIQUE;

