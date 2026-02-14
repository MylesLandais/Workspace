# Frontend Preview Guide

## Available Pages

Your D&D 5e Character Creator has a complete frontend with the following pages:

### 1. Home Page - Dice Roller
**URL:** `http://localhost:4000/`

**Features:**
- Interactive dice roller with expression input
- Quick roll buttons (d20, d12, d10, d8, d6, d4, 4d6)
- Real-time dice results with detailed breakdown
- Shows individual rolls, dropped dice, modifiers, and total
- Navigation to character management

**What to Test:**
- Roll various dice expressions
- Try quick roll buttons
- Test error handling with invalid expressions

### 2. Character Creation Wizard
**URL:** `http://localhost:4000/characters/new`

**Features:**
- **Step 1:** Roll and assign ability scores (4d6 drop lowest)
- **Step 2:** Enter character details (name, race, class, background)
- **Step 3:** Review character before creation
- Real-time stat calculations
- Visual score assignment interface

**What to Test:**
- Complete character creation flow
- Test different race/class combinations
- Verify stat calculations are correct

### 3. Character List
**URL:** `http://localhost:4000/characters`

**Features:**
- Grid view of all created characters
- Character cards showing name, level, race, class
- Quick access to view or create new characters
- Empty state when no characters exist

**What to Test:**
- View all characters
- Navigate to individual character sheets
- Create multiple characters and verify they all appear

### 4. Character Sheet
**URL:** `http://localhost:4000/characters/:id`

**Features:**
- Full character display with all stats
- Ability scores with modifiers
- Combat stats (AC, HP, Proficiency Bonus)
- Character information (race, class, background, level)
- Delete functionality

**What to Test:**
- Verify all stats display correctly
- Check calculations (modifiers, AC, HP)
- Test delete functionality

## UI Features

### Navigation
- Header navigation bar on all pages
- Links: Home, Characters, New Character
- Consistent layout across all pages

### Styling
- Custom CSS with responsive design
- Clean, modern interface
- Color-coded elements (buttons, alerts, cards)
- Mobile-friendly layout

### LiveView Features
- Real-time updates without page refresh
- Interactive forms with live validation
- Flash messages for success/error feedback
- Smooth page transitions

## Quick Test Checklist

### Basic Functionality
- [ ] Home page loads
- [ ] Can roll dice
- [ ] Can create a character
- [ ] Can view character list
- [ ] Can view character sheet
- [ ] Can delete a character

### Dice Rolling
- [ ] Simple rolls work (1d20)
- [ ] Multiple dice work (4d6)
- [ ] Modifiers work (1d20+5)
- [ ] Drop lowest works (4d6dl1)
- [ ] Error messages show for invalid input

### Character Creation
- [ ] Can roll ability scores
- [ ] Can assign scores to abilities
- [ ] Can enter character details
- [ ] Can review character
- [ ] Can save character
- [ ] Race bonuses apply correctly

### Character Display
- [ ] All stats display correctly
- [ ] Modifiers calculate correctly
- [ ] AC and HP are correct
- [ ] Proficiency bonus is correct

## Screenshots Locations

When testing, you can take screenshots of:
1. Home page with dice roller
2. Character creation - Step 1 (ability scores)
3. Character creation - Step 2 (details form)
4. Character creation - Step 3 (review)
5. Character list with multiple characters
6. Character sheet with full stats

## Browser Developer Tools

Open browser DevTools (F12) to:
- **Console:** Check for JavaScript errors
- **Network:** Monitor API calls and asset loading
- **Elements:** Inspect HTML structure
- **LiveView:** Monitor WebSocket connections (in Network tab)

## Common Issues

### Assets Not Loading
- Check that `mix phx.server` is running
- Verify assets are compiled: `mix assets.deploy`
- Check browser console for 404 errors

### LiveView Not Working
- Check WebSocket connection in Network tab
- Verify no JavaScript errors in console
- Check that Phoenix server is running

### Styles Not Applied
- Verify `app.css` is loading
- Check browser console for CSS errors
- Clear browser cache

## Next Steps

1. **Start the server** (see `START_SERVER.md`)
2. **Open browser** to `http://localhost:4000`
3. **Follow UAT guide** (see `UAT_GUIDE.md`)
4. **Test all features** systematically
5. **Report any issues** with screenshots and steps to reproduce





