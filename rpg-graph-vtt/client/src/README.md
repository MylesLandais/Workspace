# Client Source Directory

This directory is reserved for future build pipeline integration.

## Future Structure

When a build pipeline is added (e.g., webpack, vite, or rollup), source files will be organized here:

```
src/
├── components/        # Reusable UI components
│   ├── CharacterCard.js
│   ├── DiceRoller.js
│   └── PartyFilter.js
├── pages/            # Page-level components
│   └── CharacterSheet.js
├── services/          # API client services
│   └── api.js
├── styles/            # CSS/SCSS files
│   ├── main.css
│   └── components/
└── utils/             # Utility functions
```

## Current Status

Currently, all frontend code is in `static/` and served directly. No build step is required.

When ready to add a build pipeline:
1. Move source files from `static/` to `src/`
2. Configure build tool to output to `static/`
3. Update HTML files to reference built assets

