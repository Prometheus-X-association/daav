# DAAV - Data Alignment, Aggregation and Vectorisation Platform

DAAV is an open-source platform for Data Alignment, Aggregation and Vectorisation built with modern web technologies. It provides a comprehensive solution for data processing, alignment, aggregation, vectorisation, and visualization through a web-based interface with visual workflow capabilities.

## 🎯 What is DAAV?

DAAV enables you to:
- **Design visual workflows**: Create data processing pipelines with an intuitive graphical interface
- **Process multiple formats**: Native support for CSV, Parquet, Excel, JSON and more
- **Analyze in real-time**: Interactive data exploration with integrated tools
- **Connect multiple sources**: REST APIs, databases, local files
- **Visualize results**: Integrated charts and tables for analysis

## 🏗️ Technical Architecture

- **Frontend**: Angular 19 with Ionic 8 components and Rete.js 2 for workflow design
- **Backend**: High-performance FastAPI with async support (served by Gunicorn + Uvicorn workers in Docker)
- **Database**: MongoDB 7.0 (via Beanie ODM) for scalable storage
- **Authentication**: JWT (access/refresh tokens), Argon2 password hashing, admin/user roles
- **Workflow Engine**: Custom engine for data pipeline execution

## 🚀 Quick Installation

### Option 1: Docker (Recommended)
```bash
git clone https://github.com/Prometheus-X-association/daav.git
cd daav
docker-compose up -d
```

**Access**:
- **Application**: http://localhost:8080
- **API Documentation**: http://localhost:8081/docs
- **MongoDB Admin** (optional): http://localhost:8083

#### Docker Services
| Service | Port | Description |
|---------|------|-------------|
| Frontend | 8080 | Angular/Nginx user interface |
| Backend | 8081 | FastAPI REST API |
| MongoDB | — | Database (internal Docker network only, port not published) |
| Mongo Express | 8083 | Database admin (optional, `admin` profile) |

> ⚠️ The default MongoDB credentials in `docker-compose.yml` (`admin/admin123`) are for local use only — change them before any deployment.
> `JWT_SECRET_KEY` and `FIELD_ENCRYPTION_KEY` have no default value: on first start, temporary keys are generated and an error is logged until you copy them to your configuration and save them in a secrets vault (see [Application secrets](docs/SECURITY.md#application-secrets)).

#### Useful Docker Commands
```bash
# Start with MongoDB admin interface
docker-compose --profile admin up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

> 🔧 **For advanced configuration and troubleshooting**: [Docker Deployment Guide](DOCKER_DEPLOYMENT.md)

### Option 2: Local Installation

**Prerequisites**: Node.js 20 or 22 (Angular 19 also supports 18.19+), Python 3.10+ (the Docker image uses 3.13), a running MongoDB instance (required: users, datasets and workflows are stored in it)

#### Frontend (Angular + Ionic)
```bash
cd frontendApp
npm install
npm start  # http://localhost:4200
```

#### Backend (FastAPI)
```bash
cd backendApi
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Configure your variables
uvicorn app.main:app --reload --port 8000
```

On first launch (when no user exists) the backend creates a default admin user:
Username: `admin`, Password: `Admin123!`.
A password change is required at first login: until it is done, the API only allows
`GET /auth/me` and `POST /auth/change-password`, and the frontend redirects to the change password page.

**API Documentation**: http://localhost:8000/docs

## 📊 Key Features

- **Workflow Designer**: Visual interface for creating workflows with Rete.js
- **Data Processing**: Support for CSV, Parquet, Excel, JSON
- **Interactive Analysis**: Real-time data exploration
- **Complete REST API**: Automatic documentation with Swagger
- **Multiple Connectors**: Databases, external APIs, files
- **Integrated Visualizations**: Dynamic charts and tables

## 📁 Project Structure

```
daav/
├── frontendApp/              # Angular frontend application
│   ├── src/app/             # Application source code
│   └── package.json         # Node.js dependencies
├── backendApi/              # FastAPI backend application
│   ├── app/                 # Application source code
│   │   ├── main.py         # FastAPI entry point
│   │   ├── config/         # Settings, database, logging, security config
│   │   ├── core/           # Main workflow engine
│   │   ├── enums/          # Node status, connection types, user roles
│   │   ├── middleware/     # Authentication & security middleware
│   │   ├── models/         # Pydantic / Beanie models
│   │   ├── nodes/          # Input, transform and output nodes
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── utils/          # Helpers (security, encryption, auth...)
│   ├── tests/               # Pytest test suite
│   ├── requirements.txt     # Python dependencies
│   └── .env.example        # Environment variables template
├── docker-compose.yml       # Docker configuration
├── docker-start.sh          # Interactive Docker Compose helper
└── docs/                    # Documentation
```

## ⚙️ Configuration

Configuration is done via environment variables. Copy `.env.example` to `.env` in the `backendApi/` folder. Main variables:

```bash
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=daav_datasets

# Server Configuration
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:4200,http://localhost:8080

# Secrets — no default value. If empty, temporary keys are generated in backendApi/secrets/
# and an error is logged until they are copied here (keep a copy in a secrets vault)
JWT_SECRET_KEY=           # min. 32 characters
FIELD_ENCRYPTION_KEY=     # Fernet key encrypting the dataset credentials
ALLOW_PUBLIC_REGISTRATION=false

# File Upload
MAX_FILE_SIZE=100MB
UPLOAD_DIR=uploads

# Logging
LOG_LEVEL=INFO
```

See [`backendApi/.env.example`](backendApi/.env.example) for the full list (SMTP for password reset, security middleware, security logs, domain whitelist...) and [docs/SECURITY.md](docs/SECURITY.md) for the security-related settings.

## 🧪 Unit Testing

### Backend Tests

The backend includes comprehensive unit tests for security, data processing, and API endpoints.

**Run all tests:**
```bash
cd backendApi
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pytest
```

**Run tests with coverage:**
```bash
pytest --cov=app --cov-report=html
```

**Run specific test files:**
```bash
# Security tests
pytest tests/security/test_path_security.py -v

# Service tests
pytest tests/services/test_workflow_service.py -v
```

**Run tests by folder:**
```bash
pytest tests/security    # Security
pytest tests/services    # Services
pytest tests/nodes       # Nodes and transforms
pytest tests/core        # Workflow engine
```

### Test Coverage

The backend test suite includes comprehensive coverage of all critical functionality:

#### 🔒 Security Tests
- **`test_path_security.py`**: Path traversal protection, dangerous pattern detection, Unix/Windows path attack prevention, null byte injection protection
- **`test_security_middleware.py`**: Rate limiting enforcement, request validation, suspicious pattern detection (and false positives), IP blocking, proxy header spoofing
- **`test_injection_validators.py`**: SQL identifier validation (MySQL), Elasticsearch index wildcard rejection, SSRF protection on API/Elastic URLs
- **`test_secret_keys.py`**: Temporary secret generation (persistence, file permissions, concurrent workers), refusal of public placeholder secrets, error logging

#### 🗃️ Model Tests
- **`test_dataset_interface.py`**: Encryption of sensitive dataset fields before persistence and plaintext restoration after write

#### 🔧 Service Tests
- **`test_user_service.py`**: User CRUD operations, permission management, resource ownership, password changes, duplicate username/email validation, admin enforcement, dataset/workflow sharing
- **`test_auth_service.py`**: User authentication, JWT token management (access/refresh), password reset flow, admin verification, inactive account handling
- **`test_workflow_service.py`**: Workflow CRUD operations, workflow validation, timestamp management, ownership checks, database error handling
- **`test_dataset_service.py`**: Dataset operations (File, MySQL, PTX), PDC chain context management, file format support (CSV, JSON, Parquet), pagination, user isolation
- **`test_pdc_service.py`**: PDC API integration, contract/ecosystem/participant fetching, service offering management, HTTP error handling, timeout/connection errors
- **`test_email_service.py`**: Email sending (plain text/HTML), password reset emails, SMTP configuration, authentication errors, multipart message structure
- **`test_reencryption_service.py`**: Re-encryption of stored dataset credentials (plain text, previous keys, temporary key), undecryptable values
- **`test_migration_service.py`**: Config migration from INI files, dataset/workflow migration, validation errors, backup creation, mixed results handling

#### 🔄 Node Transform Tests
- **`test_filter_transform.py`**: DataFrame filtering with AND/OR conditions, rule validation, Parquet support
- **`test_merge_transform.py`**: DataFrame merging from multiple sources, column mapping, Parquet file merging, data alignment
- **`test_flatten_transform.py`**: JSON flattening (nested objects and arrays), hierarchical data transformation, column naming conventions

#### ⚙️ Core Tests
- **`test_workflow.py`**: Workflow execution engine, node execution order, workflow validation
- **`test_execution_context.py`**: Execution context isolation, user/workflow context management, async context propagation, context cleanup
- **`test_node.py`**: Base node execution, input/output handling, error states, validation

#### 🛠️ Utility Tests
- **`test_utils.py`**: File size conversion, folder operations, pandas schema generation, data slicing, base64 decoding, file type detection, DataFrame filtering with DuckDB, route access verification
- **`test_drupal_filter_converter.py`**: Drupal JSON:API filter conversion to parameterized DuckDB queries (IN / NOT IN, identifier quoting against SQL injection)

### Frontend Tests

Frontend tests use Jasmine + Karma and run in headless Chrome (a local Chrome/Chromium install is required).

```bash
cd frontendApp
npm test                      # watch mode
npm test -- --watch=false     # single run (CI)
```

**Run with coverage:**
```bash
npm test -- --watch=false --code-coverage
```

### Frontend Test Coverage

About 70 spec files cover:
- **Workflow editor**: `core/workflow-editor`, `core/workflow-node-editor`, `nodes/node-block`
- **Nodes**: every input, transform and output node (`nodes/inputs`, `nodes/transforms`, `nodes/outputs`)
- **Components**: node rendering, sockets, connections, widgets, data mapper/filter, modals, dashboards, user profile
- **Models & services**: dataset models (API, MongoDB, MySQL, PTX), dataset/workflow/loading services

## 📖 Documentation

- [Docker Deployment Guide](DOCKER_DEPLOYMENT.md) - Advanced Docker configuration and troubleshooting
- [Project Overview](docs/OVERVIEW.md) - Detailed technical architecture
- [Plugin Development Guide](docs/PLUGGINS.md) - Create custom nodes for the platform
- [Security Guide](docs/SECURITY.md) - Security measures, encryption and configuration
- [Node User Guide](docs/README.md) - How to use each node in the workflow editor
- [Design Document](docs/design-document.md) - Prometheus-X building block design document

## Contributing

Contributions to the Prometheus-X Daav are welcome! If you would like to contribute, please follow these steps:

1. Fork the repository on GitHub.
2. Create a new branch for your feature or bug fix.
3. Make the necessary code changes, adhering to the project's coding style and guidelines.
4. Write appropriate tests to ensure code integrity.
5. Commit your changes and push the branch to your forked repository.
6. Submit a pull request to the main repository, describing your changes in detail.

Please ensure that your contributions align with the project's coding standards, have proper test coverage, and include necessary documentation or updates to existing documentation.

## License

The Prometheus-X Daav is released under the [MIT License](LICENSE.md). You are free to use, modify, and distribute the software as per the terms specified in the license.

## Support

If you encounter any issues or have questions regarding the Prometheus-X Daav, feel free to open an issue on the GitHub repository. The project maintainers and community members will be happy to assist you.
