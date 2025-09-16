# Time Tracker

A Python Flask web application for tracking work time with Redis Stack Server backend. Features a calendar-based interface with adjustable start/end times, reference ticket management, and powerful querying capabilities.

## Features

- 📅 **Calendar-based Time Tracking**: Intuitive interface for tracking work sessions
- ⏰ **Precise Time Control**: Adjustable start and end times for accurate tracking  
- 🎫 **Reference Tickets**: Link tasks to multiple reference tickets/issues
- 📝 **Task Descriptions**: Add detailed descriptions and labels for each task
- 🔍 **Advanced Filtering**: Filter tasks by date range with easy querying
- 🚀 **Redis Stack JSON**: Fast storage and retrieval using Redis JSON functionality
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices

## Architecture

- **Backend**: Python Flask with REST API
- **Database**: Redis Stack Server with JSON document storage
- **Frontend**: Vanilla JavaScript with modern ES6+ features
- **Styling**: Custom CSS with responsive design

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Modern web browser

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/gavinbarnard/timetracker.git
cd timetracker
```

### 2. Start Redis Stack Server

```bash
docker-compose up -d
```

This will start Redis Stack Server with:
- Redis database on port 6379
- RedisInsight web interface on port 8001
- Default password: `mypassword`

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

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

### Health Check
```http
GET /health
```

## Configuration

Environment variables can be set in the `.env` file:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=mypassword
FLASK_DEBUG=True
FLASK_ENV=development
```

## Data Storage

Tasks are stored as JSON documents in Redis Stack Server with the following structure:

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

## Redis Stack Features

The application leverages Redis Stack Server's JSON functionality for:

- **Document Storage**: Tasks stored as native JSON documents
- **Efficient Querying**: Fast retrieval and filtering
- **Data Persistence**: Reliable storage with Redis durability
- **RedisInsight**: Web-based GUI for database management at `http://localhost:8001`

## Development

### Project Structure

```
timetracker/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Redis Stack Server setup
├── .env                   # Environment configuration
├── templates/
│   └── index.html        # Main web interface
├── static/
│   ├── css/
│   │   └── style.css     # Application styling
│   └── js/
│       └── app.js        # Frontend JavaScript
└── README.md             # This file
```

### Running in Development Mode

The application runs in debug mode by default, enabling:
- Automatic reloading on code changes
- Detailed error messages
- Debug toolbar (if installed)

### Accessing RedisInsight

Visit `http://localhost:8001` to access the RedisInsight web interface for:
- Viewing stored data
- Running Redis commands
- Monitoring performance
- Database management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is released into the public domain under the Unlicense. See [LICENSE](LICENSE) for details.
