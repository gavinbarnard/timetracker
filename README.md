# Time Tracker

A Python Flask web application for tracking work time with Redis Stack Server backend. Features a calendar-based interface with adjustable start/end times, reference ticket management, and powerful querying capabilities.

## Features

- 📅 **Calendar-based Time Tracking**: Intuitive interface for tracking work sessions
- ⏰ **Precise Time Control**: Adjustable start and end times for accurate tracking  
- 🎫 **Reference Tickets**: Link tasks to multiple reference tickets/issues
- 📝 **Task Descriptions**: Add detailed descriptions and labels for each task
- 🔍 **Advanced Filtering**: Filter tasks by date range with easy querying
- 📊 **CSV Export**: Export tasks to spreadsheet format with hours calculation and totals for invoicing
- 🚀 **Redis Stack JSON**: Fast storage and retrieval using Redis JSON functionality
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices

## Architecture

- **Backend**: Python Flask with REST API
- **Database**: Redis Stack Server with JSON document storage
- **Frontend**: Vanilla JavaScript with modern ES6+ features
- **Styling**: Custom CSS with responsive design

## Prerequisites

- Python 3.8+
- Redis server (running locally or remotely)
- Modern web browser

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/gavinbarnard/timetracker.git
cd timetracker
```

### 2. Setup Redis Server

Make sure you have Redis server running. You can install and start Redis in several ways:

**Option A: Using system package manager (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

**Option B: Using Docker (if you prefer):**
```bash
docker run -d -p 6379:6379 redis:latest
```

**Option C: Using Redis Stack (for JSON functionality):**
```bash
docker run -d -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment (Optional)

Copy the example environment file and customize if needed:
```bash
cp .env.example .env
```

Edit `.env` to match your Redis configuration if it's not running with default settings.

### 5. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Adding a New Task

1. Click the "Add New Task" button
2. Fill in the task description
3. Set the start and end times (defaults to current time and one hour later)
4. Add reference tickets separated by commas (optional)
5. Click "Save Task"

### Editing a Task

1. Click the "Edit" button on any task card
2. Modify the details in the form
3. Click "Save Task" to update

### Filtering Tasks

1. Use the date range picker in the top controls
2. Click "Filter" to show tasks within the selected date range
3. Click "Clear" to reset the filter

### Exporting Tasks to Spreadsheet

1. Select your desired date range using the date picker controls
2. Click the "Export CSV" button
3. The system will automatically download a CSV file containing:
   - Task details (description, start/end times, reference tickets)
   - Hours worked for each task
   - Total hours for the selected time period (perfect for invoicing)
4. The exported file will be named `timetracker_export_[start_date]_to_[end_date].csv`

### Viewing Task Details

Each task card displays:
- Task description and duration
- Start and end times
- Reference tickets (if any)
- Edit and delete actions

## API Endpoints

The application provides a REST API for programmatic access:

### Get All Tasks
```http
GET /api/tasks
```

### Get Tasks by Date Range
```http
GET /api/tasks?start_date=2023-01-01&end_date=2023-01-31
```

### Create a New Task
```http
POST /api/tasks
Content-Type: application/json

{
  "description": "Task description",
  "start_time": "2023-12-01T09:00:00",
  "end_time": "2023-12-01T11:00:00",
  "reference_tickets": ["TASK-123", "BUG-456"]
}
```

### Get a Specific Task
```http
GET /api/tasks/{task_id}
```

### Update a Task
```http
PUT /api/tasks/{task_id}
Content-Type: application/json

{
  "description": "Updated description",
  "start_time": "2023-12-01T09:30:00",
  "end_time": "2023-12-01T11:30:00"
}
```

### Delete a Task
```http
DELETE /api/tasks/{task_id}
```

### Export Tasks to CSV
```http
GET /api/export/csv?start_date=2023-01-01&end_date=2023-01-31
```

Returns a CSV file containing tasks within the specified date range, including:
- Task descriptions and times
- Calculated hours for each task
- Reference tickets
- Total hours summary for invoicing

### Health Check
```http
GET /health
```

## Configuration

Environment variables can be set in the `.env` file:

```env
# Redis Configuration (only set if different from defaults)
REDIS_HOST=localhost
REDIS_PORT=6379
# REDIS_PASSWORD=your_password  # Uncomment if your Redis requires authentication

# Flask Configuration
FLASK_DEBUG=True
FLASK_ENV=development
```

### Redis Setup Notes

The application works with:
- **Standard Redis**: Basic Redis installation (most common)
- **Redis Stack**: Enhanced Redis with JSON functionality (recommended for better performance)
- **Redis Cloud**: Remote Redis instance

By default, the app connects to `localhost:6379` with no authentication. Adjust the `.env` file if your Redis setup differs.

## Data Storage

Tasks are stored as JSON documents in Redis with the following structure:

```json
{
  "id": "uuid-string",
  "description": "Task description",
  "start_time": "2023-12-01T09:00:00",
  "end_time": "2023-12-01T11:00:00",
  "reference_tickets": ["TASK-123", "BUG-456"],
  "created_at": "2023-12-01T08:45:00",
  "updated_at": "2023-12-01T08:45:00"
}
```

## Redis Features

The application leverages Redis functionality for:

- **Document Storage**: Tasks stored as JSON documents using Redis JSON commands
- **Efficient Querying**: Fast retrieval and filtering capabilities
- **Data Persistence**: Reliable storage with Redis durability options
- **Set Operations**: Task indexing using Redis sets for quick lookups

**Note**: If using Redis Stack, you can access RedisInsight web interface at `http://localhost:8001` for database management.

## Development

### Project Structure

```
timetracker/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment configuration template
├── templates/
│   └── index.html        # Main web interface
├── static/
│   ├── css/
│   │   └── style.css     # Application styling
│   └── js/
│       └── app.js        # Frontend JavaScript
├── test_api.py           # API testing suite
└── README.md             # This file
```

### Running in Development Mode

The application runs in debug mode by default, enabling:
- Automatic reloading on code changes
- Detailed error messages
- Debug toolbar (if installed)

### Database Management

If you're using Redis Stack, you can access the RedisInsight web interface at `http://localhost:8001` for:
- Viewing stored data
- Running Redis commands  
- Monitoring performance
- Visual database management

For standard Redis installations, you can use redis-cli or other Redis management tools.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is released into the public domain under the Unlicense. See [LICENSE](LICENSE) for details.
