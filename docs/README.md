# Data Alignment, Aggregation and Vectorisation (DAAV) BB

[Design document](design-document.md)


## How to Use DAAV Nodes in the Frontend

### 1. What Are Nodes?

Nodes are building blocks in DAAV’s workflow editor. Each node represents a step in your data processing pipeline (e.g., loading a file, filtering data, exporting results).

### 2. Main Node Types

- **Input nodes** (File, MySQL, MongoDB, Service Chain Input): load a dataset (file, database table/collection, PTX service chain) into your workflow.
- **Transform nodes** (Filter, Flatten, Merge): filter rows, flatten nested data or merge several sources.
- **Output nodes** (File, API, MongoDB, MySQL, PDC, Service Chain Output): export the results of your workflow (write a file or a table, expose them through an API, send them to the PTX ecosystem).

### 3. How to Build a Workflow

1. **Add Nodes:**  
	 Drag and drop nodes (Input, Transform, Output) into the editor area.

2. **Connect Nodes:**  
	 Draw connections between nodes to define the flow of data (e.g., connect File Input to Filter, then to Output).

3. **Configure Each Node:**  
	 - For Input: Select your dataset file from the dropdown.
	 - For Transform: Set filter rules using the provided interface.
	 - For Output: Choose where to export or view your results.

4. **Run the Workflow:**  
	 Click the play button on each node to execute, or run the entire workflow.

### 4. What You Need to Know

	Make sure the data you load matches what the next node expects (e.g., tabular data for filters).

	Each node shows its status (incomplete, complete, error). Fix any errors before running.

	You can save your workflow, export results, and re-use nodes for different tasks.

	Hover over controls and status indicators for more information.


## DAAV Node Reference Guide (Frontend)

### Input Nodes

#### DataFileBlock (File Input)
**Purpose:** Load a dataset file (CSV, JSON, Excel or Parquet) into your workflow.
**Interface Parameters:**
- Dataset selection: Dropdown to choose a file from available datasets.
- Status indicator: Shows if the node is ready, incomplete, or in error.
**How to Use:**
1. Add the node to your workflow.
2. Select a dataset file from the dropdown.
3. Wait for the loader to finish; status will update to "Complete" if successful.
4. Output is available for connection to other nodes.

#### DataMysqlBlock (MySQL Input)
**Purpose:** Connect to a MySQL database and load table data.
**Interface Parameters:**
- Dataset selection: Dropdown to choose a MySQL dataset.
- Database selection: Dropdown appears after dataset selection if multiple databases are available.
- Table selection: Dropdown appears after database selection if multiple tables are available.
- Status indicator: Shows node readiness.
**How to Use:**
1. Add the node to your workflow.
2. Select a MySQL dataset.
3. Choose a database (if prompted).
4. Choose a table (if prompted).
5. Wait for the loader and status update.
6. Output is available for connection.

#### DataMongoBlock (MongoDB Input)
**Purpose:** Connect to a MongoDB database and load collection data.
**Interface Parameters:**
- Dataset selection: Dropdown to choose a MongoDB dataset.
- Database selection: Dropdown appears after dataset selection if multiple databases are available.
- Collection selection: Dropdown appears after database selection if multiple collections are available.
- Status indicator: Shows node readiness.
**How to Use:**
1. Add the node to your workflow.
2. Select a MongoDB dataset.
3. Choose a database (if prompted).
4. Choose a collection (if prompted).
5. Wait for the loader and status update.
6. Output is available for connection.

#### DataElasticBlock (Elasticsearch Input)
**Purpose:** Read the documents of an Elasticsearch index.
**Interface Parameters:**
- Dataset selection: Dropdown to choose an Elasticsearch dataset.
- Index selection: Dropdown of the indices visible with the dataset credentials (only when the dataset does not fix an index).
- Query (optional): a Lucene query string (`category:books AND price:>20`) or a JSON Query DSL clause (`{"term": {"in_stock": true}}`). Empty reads all documents.
- Fields (optional): comma-separated list of the fields to keep. Empty keeps the whole document.
- Max documents (optional): stop after this number of documents. Empty reads the whole result.
- Include _id: adds the document id as an `_id` column.
- Status indicator: Shows node readiness.
**How to Use:**
1. Add the node to your workflow.
2. Select an Elasticsearch dataset, then an index (if prompted).
3. Optionally type a query, fields or a maximum: the output preview is refreshed after typing.
4. Output is available for connection. Nested objects are kept as objects (use the Flatten node to get flat columns).

See [Elasticsearch](ELASTICSEARCH.md) for the connection settings, the privileges and an example workflow.

#### ServiceChainInput (Service Chain Input Prometheusx integration)
**Purpose:** Load data from a service chain (PTX or other contract-based source).
**Prerequisites:** Add a key/value credential from the pdc (on vision trust side use the the identifier of the credential pair).
This will ensure an User verification and the right to use this workflow.
Any workflow using this node must end with a ServiceChainOutput to return the transformed result to the PDC.
**Interface Parameters:**
- Contract/service selection: Dropdowns to select contract and service chain.
- Custom controls: May include JSON input, trigger button, etc.
- Status indicator: Shows node readiness.
**How to Use:**
1. Add the node to your workflow.
2. Select contract and service chain as prompted.
3. Configure any custom controls.
4. Wait for status update.
5. Output is available for connection.

This node is a special input that must be paired with ServiceChainOutput. Both are required for a workflow to interact with a service chain and properly exchange data with the PDC.

---

### Transform Nodes

#### FilterTransform (Filter)
**Purpose:** Apply filter rules to incoming tabular data.
**Interface Parameters:**
- Data source connection: Connect to a previous node providing tabular data.
- Filter rules: UI widget to build filter conditions (column, operator, value).
- Status indicator: Shows if filter rules are valid and node is ready.
**How to Use:**
1. Add the node to your workflow.
2. Connect it to a data source node (e.g., DataFileBlock).
3. Use the filter widget to add rules (e.g., "column X > 10").
4. Status updates to "Complete" when valid rules are set.
5. Output is available for connection.

#### FlattenTransform (Flatten)
**Purpose:** Flatten nested data structures into a tabular format.
**Interface Parameters:**
- Data source connection: Connect to a node providing nested data.
- Output: Tabular data.
- Status indicator: Shows node readiness.
**How to Use:**
1. Add the node to your workflow.
2. Connect it to a node providing nested data.
3. Configure as needed.
4. Status updates to "Complete" when ready.
5. Output is available for connection.

#### MergeTransform (Merge)
**Purpose:** Merge multiple datasets into one.
**Interface Parameters:**
- Multiple data source connections: Connect to two or more input nodes.
- Data mapping widget: Configure how columns from different datasets are mapped/merged.
- Status indicator: Shows if mapping is valid and node is ready.
**How to Use:**
1. Add the node to your workflow.
2. Connect it to two or more data source nodes.
3. Use the mapping widget to align columns.
4. Status updates to "Complete" when mapping is valid.
5. Output is available for connection.

---

### Output Nodes

#### ApiOutput (API Output)
**Purpose:** Expose the workflow result as JSON through a DAAV API endpoint.
**Interface Parameters:**
- URL/token configuration: Custom path (must be unique across workflows) and optional access token.
- Status indicator: Shows node readiness.
**How to Use:**
1. Add the node to your workflow.
2. Configure the custom path and token as needed.
3. Connect input data.
4. Wait for status update.
5. The result is then available with `GET /api/{custom_path}` (or `GET /api/workflow/{workflow_id}`).

#### FileOutput (File Output)
**Purpose:** Save data to a file (CSV, JSON, XML or Parquet).
**Interface Parameters:**
- File type/delimiter/name controls: Select file format, delimiter (CSV only: comma, semicolon or tab), and name.
- If file exists: Replace or Append.
- Status indicator: Shows node readiness.
**How to Use:**
1. Add the node to your workflow.
2. Configure file type, delimiter, and name.
3. Connect input data.
4. Wait for status update.
5. Download or view results as provided.

#### ElasticOutput (Elasticsearch Output)
**Purpose:** Index data into an Elasticsearch index.
**Interface Parameters:**
- Dataset selection: Dropdown to choose an Elasticsearch dataset.
- Index: existing indices are suggested; a new name creates the index.
- If index already exists: `Fail` (default), `Replace` (the index is deleted and created again) or `Append`.
- Id field (optional): column used as document `_id`. Documents with an existing id are replaced, so running the workflow again updates them instead of duplicating them. Empty: ids are generated.
- Status indicator: Shows node readiness.
**How to Use:**
1. Add the node to your workflow and connect input data (nested, or flat e.g. after a Flatten node).
2. Select an Elasticsearch dataset and type or pick the index.
3. Choose the behaviour when the index exists and, optionally, the id field.
4. Run the workflow: the status message gives the number of indexed documents.

Like the other outputs, running the node on the sample writes the sample. See [Elasticsearch](ELASTICSEARCH.md) for the index mappings, the `_id` column, the required privileges and the dataset dashboard.

#### MongoOutput (MongoDB Output)
**Purpose:** Save data to a MongoDB collection.
**Interface Parameters:**
- Database/collection selection: Dropdowns for database and collection.
- Index options: Controls for index creation.
- Status indicator: Shows node readiness.
**How to Use:**
1. Add the node to your workflow.
2. Select database and collection.
3. Configure index options as needed.
4. Connect input data.
5. Wait for status update.

#### MysqlOutput (MySQL Output)
**Purpose:** Save data to a MySQL table.
**Interface Parameters:**
- Database/table selection: Dropdowns for database and table.
- Index options: Controls for index creation.
- Status indicator: Shows node readiness.
**How to Use:**
1. Add the node to your workflow.
2. Select database and table.
3. Configure index options as needed.
4. Connect input data.
5. Wait for status update.

#### PdcOutput (PTX Output share data in prometheusx ecosystem )
**Purpose:** Send data to PTX resources or endpoints.
**Prerequisites:** Add a key/value credential from the pdc (on vision trust side use the the identifier of the credential pair).
This will ensure an User verification and the right to use this workflow.
**Interface Parameters:**
- Resource selection: Dropdown for PTX resource.
- URL controls: Input for endpoint URL the {custom_path}.
- Status indicator: Shows node readiness.
**How to Use:**
1. Add the node to your workflow.
2. Select PTX resource and configure URL.
3. Connect input data.
4. Wait for status update.
This node work in pair with routes /output/{custom_path} or /output/workflow/{workflow_id}

#### ServiceChainOutput (Service Chain Output Prometheusx ecosystem) 
**Purpose:** Send data to a service chain (PTX or contract-based destination).
**Prerequisites:** ServiceChainInput source ultimately wired with this node.
**Interface Parameters:**
- Dataset selection: Dropdown for service chain dataset.
- Status indicator: Shows node readiness.
**How to Use:**
1. Add the node to your workflow.
2. Select service chain dataset.
3. Connect input data.
4. Wait for status update.

This node is a special output that must be paired with ServiceChainInput. Both are required for a workflow to interact with a service chain and properly exchange data with the PDC.

---

### Common Controls (All Nodes)

- Label/Title: Name of the node.
- Status indicator: Visual feedback (color, tooltip) for node state.
- Play/Execute button: Runs the node’s process.
- Error messages: Tooltip or modal for error details.
- Loader indicator: Shows when node is busy.

---

**Summary:**
For each node, select the appropriate dataset or configure parameters as prompted. Connect nodes in the desired order, configure each node’s options, and use the play button to execute. Status and loader indicators help you track progress and resolve issues. All controls are accessible via the node’s UI in the workflow editor.
- **Help & Tooltips:**
	Hover over controls and status indicators for more information.

