import asyncio
import traceback
from typing import Optional, Any
import pandas as pd
import pyarrow.parquet as pq
from fastapi import HTTPException
from pydantic import ConfigDict
from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import FileDataset
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.outputs.output_node import OutputNode
from app.services.dataset_service import DatasetService
import os
import logging
from app.utils.utils import resolve_file_name

from app.utils.security import PathSecurityValidator
from app.config.settings import settings
from app.services.workflow_service import WorkflowService
from app.core.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


def _plain_file_name(file_name: str) -> str:
    """The file name if it is a bare name; 400 if it carries a directory, so that the output stays in the upload folder."""
    if file_name in ('.', '..') or '/' in file_name or '\\' in file_name or os.path.isabs(file_name):
        raise HTTPException(status_code=400, detail="Invalid file name: a file name without directory is expected")
    return file_name


class FileOutput(OutputNode):
    
    datasetService: Optional[DatasetService] = None
    workflowService: Optional[WorkflowService] = None

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new FileOutput instance.

        Args:
            id (str): Unique identifier for the node
            data (Any): Data associated with the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)
        self.datasetService = DatasetService()
        self.workflowService = WorkflowService() 

    async def process(self, sample=False) -> StatusNode:
        """Process the data and export it to a CSV file.

        Args:
            sample (bool): Flag to indicate if process on sample should be done. Defaults to False.

        Returns:
            StatusNode: The status of the node after processing.
        """
        try:
            dataset, delimiter, encoding, file_type, file_name, file_exist = await self._retrieveFileConfig()
            

            if dataset is not None and dataset.filePath:
                data_file_type = dataset.metadata.fileType
                if data_file_type != file_type:
                    self.statusMessage = f"Output type '{file_type}' does not match dataset type '{data_file_type}'"
                    raise ValueError("File type mismatch between dataset and output node")
                
            # Determine output file path
            if dataset is not None:
                output_file = PathSecurityValidator.validate_file_path(dataset.filePath)
            elif file_name:
                resolved_filename = resolve_file_name(file_name, file_type)
                
                # Get user context for file isolation
                current_user = ExecutionContext.get_user()
                
                if current_user:
                    # Create user-specific directory: uploads/{user_id}/
                    user_upload_dir = os.path.join(settings.upload_dir, current_user.id)
                    os.makedirs(user_upload_dir, exist_ok=True)
                    output_file = os.path.join(user_upload_dir, resolved_filename)
                    logger.info(f"Creating file in user directory: {user_upload_dir}")
                else:
                    # Fallback to general uploads directory
                    output_file = os.path.join(settings.upload_dir, resolved_filename)
                    logger.info(f"Creating file in general directory: {settings.upload_dir}")
            else:
                raise ValueError("No output file specified")
            for input in self.inputs.values():
                data = input.get_node_data()
                if input.get_connected_node():
                    if isinstance(data, NodeDataPandasDf):
                        if sample:
                            df = data.dataExample
                        else:
                            df = data.data
                        if not isinstance(df, pd.DataFrame):
                            raise ValueError("Input data is not a pandas DataFrame")

                        print(f"Exporting data to {output_file}")
                        
                        if file_type == 'csv':
                            if file_exist == 'append' and os.path.exists(output_file):
                                df.to_csv(output_file, sep=delimiter, encoding=encoding, index=False, mode='a', header=False)
                            else:
                                df.to_csv(output_file, sep=delimiter, encoding=encoding, index=False)
                        elif file_type == 'json':
                            self._write_json_data(df, output_file, file_exist)
                        elif file_type == 'xml':
                            self._write_xml_data(df, output_file, encoding, file_exist)
                        elif file_type == 'parquet':
                            if file_exist == 'append':
                                # fileType == "append"
                                old_data = pd.read_parquet(output_file)
                                df = pd.concat([old_data, df], ignore_index=True)
                                df.to_parquet(output_file)
                            else:
                                df.to_parquet(output_file)
                        else:
                            raise ValueError(f"Unsupported file type: {file_type}")
                        
                        print(f"Successfully exported to {output_file}")
                        
                        # Create and save new dataset AFTER the file has been created successfully
                        if dataset is None and file_name:
                            # Get execution context for user information
                            current_user = ExecutionContext.get_user()
                            workflow = ExecutionContext.get_workflow()
                            
                            if current_user:
                                logger.info(f"User {current_user.username} creating dataset in workflow {workflow.name if workflow else 'unknown'}")
                            
                            new_dataset = self._create_file_dataset(output_file, file_type, delimiter, encoding)
                            
                            # Add connection with user context if available
                            if current_user:
                                await self.datasetService.add_connection(new_dataset, current_user)
                                logger.info(f"Created new dataset: {new_dataset.name} for user {current_user.username}")
                                self.data['selectDataSource']["value"] =  new_dataset.id
                                self.data['selectDataSource']["list"].append({
                                    "value": new_dataset.id,
                                    "label": new_dataset.name
                                })
                                self.data['fileName']["value"] = None
                                self.data['fileName']["label"] = None
                            else:
                                logger.warning("No user context available for dataset creation")
                                # You could handle this case differently or skip dataset creation                                
                        break
                        
                    elif isinstance(data, NodeDataParquet):
                        # Process in chunks to handle large files
                        chunk_size = 100
                        parquet_file_path = PathSecurityValidator.validate_file_path(data.data)
                        parquet_file = pq.ParquetFile(parquet_file_path)
                        
                        if file_type == 'csv':
                            # The file is written in a worker thread so that it does not block the event loop
                            await asyncio.to_thread(
                                self._write_csv_parquet_data, parquet_file, output_file, delimiter, encoding, sample, chunk_size, file_exist
                            )
                        
                        elif file_type == 'json':
                            self._write_json_parquet_data(parquet_file, output_file, sample, chunk_size, file_exist)
                        
                        elif file_type == 'xml':
                            self._write_xml_parquet_data(parquet_file, output_file, encoding, sample, chunk_size, file_exist)
                        elif file_type == 'parquet':
                            if file_exist == 'append':
                                # fileType == "append"
                                old_data = pd.read_parquet(output_file)
                                new_data = parquet_file.read().to_pandas()
                                combined_data = pd.concat([old_data, new_data], ignore_index=True)
                                combined_data.to_parquet(output_file)
                            else:
                                parquet_file.write(output_file)
                        print(f"Successfully exported to {output_file}")
                        
                        # Create and save new dataset AFTER the file has been created successfully
                        if dataset is None and file_name:
                            # Get execution context for user information  
                            current_user = ExecutionContext.get_user()
                            
                            new_dataset = self._create_file_dataset(output_file, file_type, delimiter, encoding)
                            if current_user:
                                await self.datasetService.add_connection(new_dataset, current_user)
                                logger.info(f"Created new dataset: {new_dataset.name} for user {current_user.username}")
                                self.data['selectDataSource']["value"] =  new_dataset.id
                                self.data['selectDataSource']["list"].append({
                                    "value": new_dataset.id,
                                    "label": new_dataset.name
                                })
                                self.data['fileName']["value"] = None
                                self.data['fileName']["label"] = None
                            else:
                                logger.warning("No user context available for dataset creation")
                                # You could handle this case differently or skip dataset creation         
                        break
                    else:
                        raise TypeError("Unsupported data type: {}".format(type(data)))
        except Exception as e:
            traceback.print_exc()
            self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
            self.statusMessage = e.__str__()
            return StatusNode.Error
        return StatusNode.Valid

    async def _retrieveFileConfig(self):
        """Retrieve the file configuration.

        Returns:
            tuple[FileDataset, str, str]: A tuple containing the dataset, delimiter, and encoding.

        Raises:
            ValueError: If no data source is selected.
        """
        dataset = None
        dataset_id: str = None
        select_data_source = self.data.get('selectDataSource')
        if select_data_source and select_data_source.get('value'):
            dataset_id = select_data_source['value']
        
        if dataset_id:
            try:  
                dataset: FileDataset = await self.datasetService.get_dataset(dataset_id)
            except Exception:
                dataset= None
        delimiter = self.data.get('delimiter')['value'] if self.data.get('delimiter') and self.data.get('delimiter').get('value') else ','
        encoding = self.data.get('encoding')['value'] if self.data.get('encoding') and self.data.get('encoding').get('value') else 'utf-8'
        file_type = self.data.get('fileType')['value'] if self.data.get('fileType') and self.data.get('fileType').get('value') else None
        file_name = self.data.get('fileName')['value'] if self.data.get('fileName') and self.data.get('fileName').get('value') else None
        
        if file_name:
            secure_file_name = PathSecurityValidator.validate_filename(_plain_file_name(file_name))
        else:
            secure_file_name = None
        
        file_exist = self.data.get('fileExist')['value'] if self.data.get('fileExist') and self.data.get('fileExist').get('value') else None
        
        if dataset is None and not file_name:
            raise ValueError("Either a data source must be selected or a filename must be provided")

        return dataset, delimiter, encoding , file_type, secure_file_name, file_exist

    def _write_json_data(self, df: pd.DataFrame, output_file: str, file_exist: str):
        """Write DataFrame to JSON file with proper array handling."""
        import json
        import os
        
        if file_exist == 'append' and os.path.exists(output_file):
            # Load existing data and append
            records = df.to_dict(orient='records')
            existing_records = []
            with open(output_file, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        existing_records = existing_data
                except json.JSONDecodeError:
                    pass
        
            # Combine existing and new records
            all_records = existing_records + records
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_records, f, ensure_ascii=False, indent=2)
        else:
            # Replace or create new file using pandas to_json
            df.to_json(output_file, orient='records', force_ascii=False, indent=2)

    def _write_xml_data(self, df: pd.DataFrame, output_file: str, encoding: str, file_exist: str):
        """Write DataFrame to XML file with proper array handling."""
        import xml.etree.ElementTree as ET
        import os
        
        if file_exist == 'append' and os.path.exists(output_file):
            # Parse existing XML and append
            try:
                tree = ET.parse(output_file)
                root = tree.getroot()
            except ET.ParseError:
                root = ET.Element("data")
                tree = ET.ElementTree(root)
            
            # Convert DataFrame to XML elements and append
            for _, row in df.iterrows():
                item = ET.SubElement(root, "item")
                for col, value in row.items():
                    elem = ET.SubElement(item, str(col))
                    elem.text = str(value)
            
            tree.write(output_file, encoding=encoding, xml_declaration=True)
        else:
            # Replace or create new file
            df.to_xml(output_file, index=False, encoding=encoding)

    def _write_csv_parquet_data(self, parquet_file, output_file: str, delimiter: str, encoding: str, sample: bool, chunk_size: int, file_exist: str):
        """Write parquet data to CSV file in chunks."""
        first_chunk = True
        mode = 'w' if file_exist == 'replace' or not os.path.exists(output_file) else 'a'
        with open(output_file, mode, encoding=encoding) as csvfile:
            for batch in parquet_file.iter_batches(batch_size=chunk_size):
                chunk_df = batch.to_pandas()
                
                if sample and first_chunk:
                    chunk_df = chunk_df.head(20)
                    chunk_df.to_csv(csvfile, sep=delimiter, index=False)
                    break
                
                write_header = first_chunk and (file_exist == 'replace' or not os.path.exists(output_file))
                chunk_df.to_csv(csvfile, sep=delimiter, index=False, header=write_header)
                first_chunk = False

    def _write_json_parquet_data(self, parquet_file, output_file: str, sample: bool, chunk_size: int, file_exist: str):
        """Write parquet data to JSON file in chunks with proper array handling."""
        import json
        import os
        
        all_records = []
        first_chunk = True
        
        # Read existing data if appending
        if file_exist == 'append' and os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        all_records.extend(existing_data)
                except json.JSONDecodeError:
                    pass
        
        # Process chunks
        for batch in parquet_file.iter_batches(batch_size=chunk_size):
            chunk_df = batch.to_pandas()
            
            if sample and first_chunk:
                chunk_df = chunk_df.head(20)
            
            records = chunk_df.to_dict(orient='records')
            all_records.extend(records)
            
            if sample and first_chunk:
                break
            first_chunk = False
        
        # Write all data as JSON array
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_records, f, ensure_ascii=False, indent=2)

    def _write_xml_parquet_data(self, parquet_file, output_file: str, encoding: str, sample: bool, chunk_size: int, file_exist: str):
        """Write parquet data to XML file in chunks with proper array handling."""
        import xml.etree.ElementTree as ET
        import os
        
        # Initialize or load existing XML structure
        if file_exist == 'append' and os.path.exists(output_file):
            try:
                tree = ET.parse(output_file)
                root = tree.getroot()
            except ET.ParseError:
                root = ET.Element("data")
                tree = ET.ElementTree(root)
        else:
            root = ET.Element("data")
            tree = ET.ElementTree(root)
        
        first_chunk = True
        for batch in parquet_file.iter_batches(batch_size=chunk_size):
            chunk_df = batch.to_pandas()
            
            if sample and first_chunk:
                chunk_df = chunk_df.head(20)
            
            # Add chunk data to XML
            for _, row in chunk_df.iterrows():
                item = ET.SubElement(root, "item")
                for col, value in row.items():
                    elem = ET.SubElement(item, str(col))
                    elem.text = str(value)
            
            if sample and first_chunk:
                break
            first_chunk = False
        
        tree.write(output_file, encoding=encoding, xml_declaration=True)

    def _create_file_dataset(self, file_path: str, file_type: str, delimiter: str, encoding: str) -> FileDataset:
        """Create a new FileDataset for the output file.
        
        Args:
            filePath (str): The complete file path
            fileType (str): The type of file (csv, json, xml, parquet)
            delimiter (str): The delimiter for CSV files
            encoding (str): The file encoding
            
        Returns:
            FileDataset: A new FileDataset instance
        """
        # Generate a name for the dataset based on the filename
        dataset_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Create the FileDataset with the actual file path
        new_dataset = FileDataset(
            name=dataset_name,
            filePath=file_path,
            type="file",
            csvDelimiter=delimiter if file_type == 'csv' else None,
            encoding=encoding,
            inputType = "file",
            metadata= {
                "fileType": file_type,
            }
        )
        
        return new_dataset

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
