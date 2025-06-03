# Talent Match

Talent Match is a task management and talent assignment system designed to streamline the process of assigning tasks to the most suitable talent based on availability, skill, and other criteria. It integrates with Redis, Celery, and AI models (OpenAI or a local AI replacement) to provide a robust and scalable solution for task management.

---

## Features

- **Task Assignment**: Automatically assigns tasks to the most suitable talent.
- **Task Reassignment**: Reassigns overdue tasks to available talents.
- **Deadline Monitoring**: Tracks task deadlines and triggers reassignment if necessary.
- **Extension Requests**: Evaluates task extension requests using AI.
- **Slack Integration**: Sends task notifications to Slack channels.(not fully implemented - using mock for testing purposes)
- **Redis Event Stream**: Publishes and subscribes to task-related events using Redis.
- **Local AI Integration**: Supports evaluation of extension requests using a local AI model.

## Project Structure

```
.
├── config/                 # Configuration files (Redis, Celery, etc.)
├── domain/                 # Core business logic (models, services, utilities)
├── integrations/           # External service integrations (OpenAI, Slack, Redis)
├── tasks/                  # Celery tasks for assignment, monitoring, and reassignment
├── logs/                   # Log files
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Docker image definition
└── README.md               # Project documentation
```

---

## Prerequisites

Before running the project, ensure you have the following installed:

- Python 3.13 or higher
- Docker and Docker Compose
- Redis server (if not using Docker)
- OpenAI API key (if using OpenAI for extension evaluation)

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/MeFerdi/talent-match.git
cd talent-match
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory and configure the following variables:

```env
LOCAL_AI_URL="http://localhost:11434"
LOCAL_AI_MODEL="mistral"
LOCAL_AI_TIMEOUT="30"
REDIS_URL="redis://localhost:6379/0"
CELERY_BROKER_URL="redis://localhost:6379/0"
CELERY_RESULT_BACKEND="redis://localhost:6379/0"
PYTHONPATH=.
GEMINI_API_KEY=your_api_key_here
```

### 3. Install Dependencies

Install Python dependencies using `pip`:

```bash
pip install -r requirements.txt
```

### 4. Run the Project with Docker

Build and start the services using Docker Compose:

```bash
docker-compose up --build
```

This will start the following services:
- **App**: Runs the tests and application logic.
- **Redis**: Redis server for task and event management.

### 5. Run Tests

To ensure everything is working correctly, run the test suite:

```bash
PYTHONPATH=. pytest tests
```

---

## How It Works

### Task Assignment Workflow

1. **Task Creation**: Tasks are created and stored in Redis.
2. **Matching Service**: The `MatchingService` identifies the best available talent for a task.
3. **Assignment**: The `assign_task` Celery task assigns the task to the selected talent.

### Deadline Monitoring

1. **Deadline Check**: The `check_deadline` Celery task monitors task deadlines.
2. **Reassignment**: If a task is overdue and no extensions are approved, it is reassigned to another talent.

### Extension Requests

1. **Request Evaluation**: The `ExtensionService` evaluates extension requests using OpenAI or a local AI model.
2. **Approval/Rejection**: The AI model determines whether to approve or reject the request.

### Slack Notifications

1. **Task Notifications**: Task assignments and updates are sent to Slack channels using the `MockSlackClient`.

---

## Key Components

### 1. **Redis**
   - Used for storing task and talent data.
   - Provides a pub/sub mechanism for event streaming.

### 2. **Celery**
   - Handles background tasks such as task assignment, monitoring, and reassignment.

### 3. **OpenAI/Local AI**
   - Evaluates task extension requests using AI models.

### 4. **Slack Integration**
   - Sends task-related notifications to Slack channels.

---

## Development

### Running Locally

1. Start Redis:
   ```bash
   redis-server
   ```

2. Start Celery workers:
   ```bash
   celery -A config.celery worker --loglevel=info
   ```

---

## Testing

The project includes comprehensive unit and integration tests. To run the tests:

```bash
PYTHONPATH=. pytest pytest tests
```

---

## Logging

Logs are stored in the `logs/` directory. The logging system uses a custom JSON formatter for structured logging.

---