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

- **Frontend**: Angular 17 with Ionic 8 components and Rete.js for workflow design
- **Backend**: High-performance FastAPI with async support
- **Database**: MongoDB 7.0 for scalable storage
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
| MongoDB | 27017 | Database |
| Mongo Express | 8083 | Database admin (optional) |

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

**Prerequisites**: Node.js 18+, Python 3.10+, MongoDB (optional)

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
│   │   ├── core/           # Main workflow engine
│   │   ├── models/         # Pydantic models
│   │   ├── routes/         # API endpoints
│   │   └── services/       # Business logic
│   ├── requirements.txt     # Python dependencies
│   └── .env.example        # Environment variables template
├── docker-compose.yml       # Docker configuration
└── docs/                    # Documentation
```

## ⚙️ Configuration

Configuration is done via environment variables. Copy `.env.example` to `.env` in the `backendApi/` folder:

```bash
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=daav_datasets

# Server Configuration
HOST=0.0.0.0
PORT=8000

# File Upload
MAX_FILE_SIZE=100MB
UPLOAD_DIR=uploads

# Logging
LOG_LEVEL=INFO
```

## 🧪 Testing

```bash
# Backend tests
cd backendApi && pytest

# Frontend tests
cd frontendApp && npm test
```

## 📖 Documentation

- [Docker Deployment Guide](DOCKER_DEPLOYMENT.md) - Advanced Docker configuration and troubleshooting
- [Project Overview](docs/OVERVIEW.md) - Detailed technical architecture
- [Plugin Development Guide](docs/PLUGGINS.md) - Create custom nodes for the platform

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

The Prometheus-X Daav is released under the [MIT License](LICENSE). You are free to use, modify, and distribute the software as per the terms specified in the license.

## Support

If you encounter any issues or have questions regarding the Prometheus-X Daav, feel free to open an issue on the GitHub repository. The project maintainers and community members will be happy to assist you.
