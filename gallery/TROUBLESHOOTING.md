# Gallery Troubleshooting Guide

## Connection Reset Error

If you see "The connection was reset" when trying to access the gallery, follow these steps:

### 1. Check if Server is Running

Open a terminal and run:
```bash
cd gallery
python start.py
```

If you see "Port 8001 is already in use", another process is using the port.

### 2. Kill Existing Process

Find and kill any process using port 8001:

```bash
# Linux/Mac
lsof -ti:8001 | xargs kill -9

# Or find and kill manually
ps aux | grep python
kill -9 <PID>
```

### 3. Try Standalone Server

The standalone server doesn't require the full feed architecture:

```bash
cd gallery/api
python main_standalone.py
```

Then open: http://localhost:8001

### 4. Check Dependencies

Make sure all dependencies are installed:

```bash
pip install fastapi uvicorn[standard]
```

### 5. Verify Directories

Check that cache directories exist:

```bash
ls -la ~/.cache/gallery/
```

Should show:
- `html/` - Cached HTML files
- `thumbnails/` - Thumbnail images
- `data/` - Sample data

If missing, they'll be created automatically on first run.

### 6. Test Health Endpoint

Open: http://localhost:8001/health

Should return JSON like:
```json
{
  "status": "healthy",
  "cache_dir": "/home/you/.cache/gallery/html",
  "thumbnail_dir": "/home/you/.cache/gallery/thumbnails",
  "sample_data": true
}
```

### 7. Check Firewall

Make sure your firewall allows connections to localhost:8001.

### 8. Try Different Port

If port 8001 is blocked:

```bash
cd gallery/api
python main_standalone.py
```

Edit the file and change the port:
```python
uvicorn.run(app, host="0.0.0.0", port=8002)  # Change port
```

### 9. Check Browser

- Try a different browser
- Clear browser cache
- Disable browser extensions
- Try in incognito/private mode

### 10. Check Logs

Look at the server logs for errors:

```
ERROR: Error getting sources: ...
ERROR: Error loading data: ...
```

## Common Issues

### "Templates not found"

Run the setup script:
```bash
cd gallery
python setup.py
```

### "CSS/JS not found"

Check that files exist:
```bash
ls gallery/styles/main.css
ls gallery/frontend/scripts/main.js
```

### "Sample data not found"

The server will create sample data automatically on first run.

### "Permission denied"

Check file permissions:
```bash
chmod -R 755 ~/.cache/gallery/
```

### Module not found errors

Install missing dependencies:
```bash
pip install fastapi uvicorn aiofiles requests Pillow
```

## Testing the Server

### Test with curl

```bash
# Test health endpoint
curl http://localhost:8001/health

# Test sources endpoint
curl http://localhost:8001/api/sources

# Test catalogue endpoint
curl http://localhost:8001/api/catalogue/python
```

### Test with Python

```python
import requests

# Test health
response = requests.get("http://localhost:8001/health")
print(response.json())

# Test sources
response = requests.get("http://localhost:8001/api/sources")
print(response.json())
```

## Quick Fix Commands

```bash
# Stop all Python processes
pkill -f python

# Clear cache
rm -rf ~/.cache/gallery/

# Reinstall dependencies
pip install --upgrade fastapi uvicorn aiofiles

# Start server
cd gallery/api && python main_standalone.py
```

## Getting Help

If issues persist:

1. Check server logs for errors
2. Test with curl to isolate browser issues
3. Try the standalone server
4. Check firewall settings
5. Verify all dependencies are installed

## Architecture Notes

### Standalone vs Integrated

**Standalone** (`main_standalone.py`)
- Works without feed architecture
- Uses sample data
- Simple setup
- Good for testing

**Integrated** (`main.py`)
- Requires feed architecture
- Uses Neo4j + Redis
- Full functionality
- Production-ready

Use standalone for initial testing, then switch to integrated when feed architecture is ready.

## Next Steps

Once server is working:

1. Open http://localhost:8001
2. Browse the sample catalogue
3. Try search functionality
4. Switch between grid/list views
5. Test filters (NSFW, cached-only)
