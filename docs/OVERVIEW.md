# DAAV - Data Alignment, Aggregation and Vectorisation Platform

## Overview

DAAV is a comprehensive data processing and analysis platform consisting of two main components: a Python backend API and a frontend application. The platform enables users to create data transformation pipelines through an interconnected node system.

## Architecture

### Backend API (`/backendApi`)
- **Framework**: FastAPI with Python
- **Storage**: MongoDB (Beanie ODM) for users, datasets and workflows
- **Data sources**: Files, MySQL, MongoDB, REST APIs, Elasticsearch, Prometheus-X (PTX/PDC)
- **Processing**: Pandas and PyArrow for data manipulation
- **Architecture**: Modular node system for data processing
- **Security**: JWT authentication with admin/user roles, security middleware, encryption of dataset credentials

### Frontend (`/frontendApp`)
- Angular 19 + Ionic 8 application
- Visual workflow editor based on Rete.js 2 for creating and managing data pipelines
- Visualization of analysis results

## Core Components

### 1. Node System (`app/nodes/`)

The platform's core is built on a modular node system:

#### Input Nodes (`inputs/`)
- **DataFileBlock**: Loads CSV, JSON, Excel or Parquet files
- **DataMysqlBlock** / **DataMongoBlock**: Load a MySQL table or a MongoDB collection
- **ServiceChainInput**: Receives data from a Prometheus-X service chain
- **InputNode**: Base class for all input nodes

#### Transform Nodes (`transforms/`)
- **FilterTransform**: Filters rows with AND/OR rule groups
- **MergeTransform**: Merges columns from different data sources
- **FlattenTransform**: Flattens nested JSON structures
- **TransformNode**: Base class for all transformation nodes

#### Output Nodes (`outputs/`)
- **FileOutput**: Writes CSV, JSON, XML or Parquet files
- **MysqlOutput** / **MongoOutput**: Write to a MySQL table or a MongoDB collection
- **ApiOutput**: Exposes the result through an API endpoint
- **PdcOutput** / **ServiceChainOutput**: Share results in the Prometheus-X ecosystem
- **OutputNode**: Base class for all output nodes

Node classes are discovered automatically by `NodeFactory` (`node_factory.py`), which scans the `nodes/` directory. `example_*` files provide templates for new nodes (see the [Plugin Development Guide](PLUGGINS.md)).

#### Node Features
- **Inputs/Outputs**: Each node can have multiple inputs and outputs
- **State Management**: Execution status tracking (`Error`, `Incomplete`, `Complete`, `Valid`)
- **Batch Processing**: Support for large Parquet files

### 2. Data Management (`app/models/interface/`)

#### Supported Data Types
- **NodeDataPandasDf**: Pandas DataFrames for in-memory processing
- **NodeDataParquet**: Parquet files for large volume data
- **Schemas**: Automatic schema generation for validation and documentation

#### Data Sources
- Files (CSV, JSON, Excel, Parquet)
- External REST APIs
- Databases (MySQL, MongoDB, Elasticsearch)
- Prometheus-X PDC / service chains

### 3. Specialized Transformations

#### MergeTransform
- **Purpose**: Merge columns from different datasets
- **Configuration**: Flexible mapping between sources and target columns
- **Optimization**: Batch processing for large volumes
- **Use Cases**: Data consolidation from multiple sources

#### FlattenTransform
- **Purpose**: Flatten complex JSON structures
- **Features**:
  - Array explosion into multiple rows
  - Nested structure flattening
  - Parent-child relationship preservation
- **Use Cases**: JSON data normalization for analysis

### 4. Enumerations and States (`app/enums/`)
- **StatusNode**: Node states (`Error`, `Incomplete`, `Complete`, `Valid`)
- **TypeConnection**: Dataset connection types (`mysql`, `mongo`, `file`, `elastic`, `api`, `ptx`)
- **UserRole**: User roles (`admin`, `user`)
- Consistent state management across the platform

### 5. Utilities (`app/utils/`)
- **Schema Generation**: Automatic Pandas schema creation
- **Validation**: Data integrity checks
- **Optimizations**: Performance helper functions
- **Security**: Path validation (`security.py`), field encryption (`encryption.py`), JWT and password helpers (`auth_utils.py`)

### 6. API and Services (`app/routes/`, `app/services/`)
- **Routes**: `auth`, `datasets`, `workflows`, `ptx`, `output`, `api` (interactive documentation at `/docs`)
- **Services**: authentication, users, datasets, workflows, PDC integration, email (password reset), migration from legacy `config.ini`

## Processing Flow

1. **Configuration**: Define nodes and their connections
2. **Validation**: Pipeline consistency verification
3. **Execution**: Sequential node processing (a node can also be executed individually, with its parents)
4. **Monitoring**: Real-time execution state tracking
5. **Results**: Data export and visualization

## Technical Features

### Performance
- **Batch Processing**: Large volume optimization with Parquet
- **Memory Management**: Efficient handling with streaming support
- **Parallelization**: Architecture ready for concurrent processing

### Robustness
- **Error Handling**: Detailed exception capture and reporting
- **Validation**: Strict controls with Pydantic
- **Testing**: Comprehensive test suite for all components

### Extensibility
- **Modular Architecture**: Easy addition of new node types
- **Standardized Interface**: Consistent contracts between components
- **Flexible Configuration**: Data structure-based parameterization

## Use Cases

1. **ETL Pipelines**: Extract, Transform, Load for data integration
2. **Data Cleaning**: Dataset cleaning and normalization
3. **Data Integration**: Merging heterogeneous data sources
4. **Analytics Preparation**: Data preparation for analysis
5. **JSON Processing**: Semi-structured data processing

## Technologies Used

### Backend
- **Python 3.10+** (Docker image: Python 3.13)
- **FastAPI**: Modern, high-performance web framework (Gunicorn + Uvicorn workers in Docker)
- **MongoDB + Beanie**: Persistence of users, datasets and workflows
- **Pandas**: Data manipulation
- **PyArrow/Parquet**: High-performance storage and processing
- **Pydantic**: Data validation and serialization
- **python-jose / passlib (Argon2)**: JWT authentication and password hashing
- **Pytest**: Testing framework

### Frontend
- **Angular 19** and **Ionic 8**
- **Rete.js 2**: Visual workflow editor
- **Jasmine / Karma**: Testing framework

### Data Management
- **Apache Arrow**: In-memory data format
- **Parquet**: Columnar storage format
- **JSON**: Flexible data structures

## Project Structure

```
daav/
├── backendApi/          # Backend API
│   ├── app/
│   │   ├── config/      # Settings, database, logging, security
│   │   ├── core/        # Workflow engine
│   │   ├── enums/       # Enumerations
│   │   ├── middleware/  # Authentication & security middleware
│   │   ├── models/      # Data models
│   │   ├── nodes/       # Node system
│   │   ├── routes/      # API endpoints
│   │   ├── services/    # Business logic
│   │   └── utils/       # Utilities
│   └── tests/           # Automated tests
├── frontendApp/         # User interface (Angular / Ionic)
└── docs/               # Documentation
```

## Key Design Principles

### Modularity
- **Composable Nodes**: Each transformation is a self-contained, reusable component
- **Plug-and-Play**: Easy integration of new transformation types
- **Separation of Concerns**: Clear boundaries between data processing, validation, and presentation

### Scalability
- **Memory Efficiency**: Streaming processing for large datasets
- **Format Optimization**: Parquet for columnar data storage and fast querying
- **Incremental Processing**: Support for processing data in chunks

### Reliability
- **Type Safety**: Pydantic models ensure data integrity
- **Error Recovery**: Graceful handling of processing failures
- **State Tracking**: Comprehensive monitoring of pipeline execution

## Data Flow Architecture

```
Input Sources → Transform Nodes → Output Destinations
     ↓              ↓                    ↓
[Files]         [FilterTransform]   [Files (CSV/JSON/XML/Parquet)]
[MySQL/MongoDB] [MergeTransform]    [MySQL/MongoDB]
[PTX Service    [FlattenTransform]  [API / PDC /
 Chain]         [Custom Nodes]       Service Chain]
```

## Future Roadmap

Already available: visual drag-and-drop pipeline editor (Rete.js), database connectors (MySQL, MongoDB, Elasticsearch) and container-based deployment (Docker Compose).

- **Enhanced Connectors**: Integration with more data sources (LRS, Hugging Face and cloud services — some are partially implemented)
- **Advanced Monitoring**: Performance metrics and pipeline optimization suggestions
- **Real-time Processing**: Stream processing capabilities for live data
- **Machine Learning Integration**: Built-in ML model training and inference nodes

## Getting Started

1. **Installation**: Set up the backend API and frontend application
2. **Configuration**: Define your data sources and transformation requirements
3. **Pipeline Creation**: Build your data processing pipeline using available nodes
4. **Execution**: Run the pipeline and monitor progress
5. **Analysis**: Explore and visualize the processed results

DAAV represents a modern, extensible solution for data processing that combines ease of use with high performance to meet contemporary data analysis needs. The platform's modular architecture ensures it can grow and adapt to evolving data processing requirements while maintaining reliability and performance.

## 📖 Navigation

- [← Back to main project](../README.md)
- [Docker deployment guide](../DOCKER_DEPLOYMENT.md)
- [Plugin development guide](PLUGGINS.md)
- [Security guide](SECURITY.md)
- [Node user guide](README.md)