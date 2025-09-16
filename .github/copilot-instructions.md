# Time Tracker Application

**ALWAYS reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

This is a Flask-based time tracking web application with Python backend and Redis JSON storage. The target platform is Ubuntu 24.04.  This package does not manage
the redis backend server itself.  The application deployer is expected to setup a proper redis server with JSON and SEARCH backend.   The docker container provides the needed
functionality.

## Critical Requirements

- **NEVER CANCEL long-running operations**: Docker pulls take ~18 seconds, dependency installs take ~5 seconds
- **ALWAYS preserve Redis JSON calls**: The application relies on Redis JSON functionality which requires Redis Stack
- **ALWAYS test complete user workflows**: Syntax checks and API tests are not sufficient - run end-to-end scenarios


## Quick Setup and Build (VALIDATED COMMANDS)

### 1. Install System Dependencies
```bash
# Start Redis Stack with JSON support using docker as the Ubuntu local packages do not support the JSON backend (takes ~18 seconds, NEVER CANCEL)
docker run -d -p 6379:6379 -p 8001:8001 redis/redis-stack:latest

# Wait for Redis Stack to be ready (ALWAYS wait 5+ seconds)
sleep 5 && redis-cli ping
```

### 2. Install Python Dependencies
```bash
# Install all required packages (takes ~5 seconds)
pip3 install -r requirements.txt
```

### 3. Run the Application
```bash
# Start the development server
python3 app.py
```
**Application will be available at: http://localhost:5000**

## Validation and Testing

### ALWAYS run these validation steps after making changes:

1. **API Test Suite** (takes <1 second):
```bash
python3 test_api.py
```
**Expected output**: All endpoints tested successfully

2. **Syntax Validation**:
```bash
python3 -c "import app; print('Syntax check passed')"
python3 -c "import test_api; print('Test syntax check passed')"
```

3. **Manual User Scenario Testing** (CRITICAL):
- Load web interface: `curl -s http://localhost:5000/`
- Test health endpoint: `curl http://localhost:5000/health`
- **ALWAYS manually test task creation workflow in the web UI**

### Redis JSON Verification
```bash
# Test Redis JSON functionality (REQUIRED for application to work)
redis-cli JSON.SET test $ '{"hello":"world"}' && redis-cli JSON.GET test
```
**Expected output**: OK followed by {"hello":"world"}

## Project Structure and Navigation

### Key Files (FREQUENTLY REFERENCED):
```
timetracker/
├── app.py                 # Main Flask application - ALL API routes and TimeTracker class
├── requirements.txt       # Python dependencies (Flask, Redis, CORS, etc.)
├── .env.example          # Environment configuration template
├── templates/index.html   # Complete web interface (HTML/CSS/JS in one file)
├── static/css/style.css   # Application styling
├── static/js/app.js       # Frontend JavaScript for task management
├── test_api.py           # Comprehensive API test suite
└── README.md             # User documentation
```

### Important Code Locations:
- **API Routes**: app.py lines 120-196 (GET/POST/PUT/DELETE /api/tasks, /health)
- **Redis JSON operations**: app.py lines 35-45 (create_task), 58-65 (update_task)
- **TimeTracker class**: app.py lines 17-100 (all database operations)
- **Frontend task management**: static/js/app.js (modal forms, API calls)

## Database and Storage

### Redis Stack Configuration:
- **Host**: localhost:6379 (Redis database)
- **JSON Module**: REQUIRED - uses JSON.SET, JSON.GET commands
- **Key Pattern**: `timetracker:tasks:{uuid}` for task storage
- **Index**: `timetracker:task_ids` set for task ID tracking

### Environment Variables (.env):
```bash
# Optional Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
# REDIS_PASSWORD=password  # Uncomment if authentication required

# Flask development settings
FLASK_DEBUG=True
FLASK_ENV=development
```

## Common Development Tasks

### After Making Changes to Backend (app.py):
1. **ALWAYS restart Flask application**
2. **ALWAYS run API test suite**: `python3 test_api.py`
3. **ALWAYS test at least one complete user scenario**

### After Making Changes to Frontend (templates/, static/):
1. **ALWAYS refresh browser and test task creation workflow**
2. **ALWAYS verify JavaScript console has no errors**

### Debugging Redis Issues:
```bash
# Check Redis Stack container status
docker ps | grep redis

# Access Redis CLI for debugging
redis-cli

# View RedisInsight for visual debugging
# Navigate to http://localhost:8001
```

## Application Features (USER SCENARIOS TO TEST)

### Complete Task Management Workflow:
1. **Access web interface**: http://localhost:5000
2. **Create task**: Click "Add New Task", fill form, submit
3. **View tasks**: Tasks appear in calendar/list view
4. **Edit task**: Click task, modify fields, save
5. **Filter tasks**: Use date range filters
6. **Delete task**: Delete button confirmation

### API Endpoints (FOR TESTING):
- `GET /health` - System health check
- `GET /api/tasks` - List all tasks
- `GET /api/tasks?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Filter by date
- `POST /api/tasks` - Create new task
- `GET /api/tasks/{id}` - Get specific task
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task

## Troubleshooting Common Issues

### "unknown command 'JSON.SET'" Error:
- **Cause**: Standard Redis running instead of Redis Stack
- **Solution**: Ensure Redis is install via docker container during copilot developement

### Application Won't Start:
- **Check**: Redis Stack is running (`docker ps | grep redis`)
- **Check**: Port 5000 is available (`lsof -i :5000`)
- **Check**: Dependencies installed (`pip3 list | grep Flask`)

### Tests Fail:
- **Check**: Application is running on localhost:5000
- **Check**: Redis JSON functionality (`redis-cli JSON.GET test`)

## Performance and Timing Expectations

- **Initial Docker pull Redis Stack**: ~18 seconds first time (NEVER CANCEL, allow 120+ second timeout)
- **Docker start Redis Stack**: <1 second for subsequent starts  
- **Python dependency install**: ~1-5 seconds (already installed: ~1 second, fresh install: ~5 seconds)
- **Application startup**: <3 seconds
- **API test suite**: ~0.13 seconds (comprehensive test of all endpoints)
- **Redis operations**: <100ms each
- **System package updates**: ~2-10 seconds (varies by network)

## Development Best Practices

- **ALWAYS test both API and web interface** after changes
- **ALWAYS preserve Redis JSON functionality** - do not modify JSON.SET/GET calls
- **ALWAYS use the complete test workflow** - API tests + manual scenarios
- **NEVER remove Docker setup** - Redis Stack is essential for JSON support
- **ALWAYS validate that RedisInsight is accessible** for debugging

## Files NOT to Modify (CORE FUNCTIONALITY):
- Redis JSON operations in TimeTracker class methods
- Docker Redis Stack configuration  
- API endpoint structure and return formats
