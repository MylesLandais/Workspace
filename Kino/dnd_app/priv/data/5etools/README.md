# 5etools Data Files

This directory contains JSON data files from the 5etools project for importing D&D 5e game content into Neo4j.

## Obtaining Data Files

The 5etools data files can be obtained from:

- **GitHub Repository**: https://github.com/5etools-mirror-3/5etools-src
- **Data Directory**: The JSON files are located in the `data/` directory of the repository

### Required Files

For the character builder, you'll need:
- `races.json` - Race and subrace data
- `classes.json` - Class and subclass data
- `backgrounds.json` - Background data
- `spells.json` - Spell data (optional, for future features)
- `items.json` - Equipment/item data (optional, for future features)

### Download Instructions

1. Clone or download the 5etools repository
2. Copy the JSON files from `data/` to this directory
3. Run the import task: `mix import.5etools`

Alternatively, the import task can download files automatically if they're not present.

## SRD-Only Mode

For testing and legal compliance, you can filter to SRD (Systems Reference Document) content only:

```bash
mix import.5etools --srd-only
```

This will only import content with `source: "PHB"` or other SRD sources, excluding proprietary content.

## Automated Syncs

The import system is designed to support automated syncs:
- **Nightly**: Full import of all data
- **Weekly**: Incremental updates
- **Monthly**: Full refresh

The import process is idempotent and safe to run multiple times.

