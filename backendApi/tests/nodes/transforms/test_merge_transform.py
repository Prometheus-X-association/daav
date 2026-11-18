import pytest
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from app.nodes.transforms.merge_transform import MergeTransform, Source, DataMappingItem
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.enums.status_node import StatusNode


@pytest.fixture
def merge_transform():
    """Fixture to create a MergeTransform instance"""
    data = {
        'dataMapping': [
            {
                'id': 'mapping1',
                'sources': [
                    {'id': '1', 'name': 'col1', 'type': 'string', 'datasetId': 'dataset1'},
                    {'id': '2', 'name': 'col2', 'type': 'string', 'datasetId': 'dataset2'}
                ],
                'targetName': 'merged_column'
            }
        ],
        'parquetSave': {'value': False}
    }
    transform = MergeTransform(id="test_merge", data=data)
    transform.inputs = {'dataset1': Mock(), 'dataset2': Mock()}
    transform.outputs = {'out': Mock()}
    return transform


@pytest.fixture
def sample_dataframes():
    """Sample DataFrames for testing"""
    df1 = pd.DataFrame({
        'col1': ['A', 'B', 'C'],
        'other1': [1, 2, 3]
    })
    df2 = pd.DataFrame({
        'col2': ['X', 'Y', 'Z'],
        'other2': [10, 20, 30]
    })
    return df1, df2


@pytest.fixture
def parquet_files(sample_dataframes):
    """Create temporary parquet files for testing"""
    df1, df2 = sample_dataframes
    
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f1:
        df1.to_parquet(f1.name)
        parquet_path1 = f1.name
    
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f2:
        df2.to_parquet(f2.name)
        parquet_path2 = f2.name
    
    yield parquet_path1, parquet_path2
    
    # Cleanup
    os.unlink(parquet_path1)
    os.unlink(parquet_path2)


def test_merge_pandas_dataframes(merge_transform, sample_dataframes):
    """Test merging pandas DataFrames"""
    df1, df2 = sample_dataframes
    
    # Setup
    mock_data1 = NodeDataPandasDf(
        data=df1,
        dataExample=df1.head(),
        nodeSchema=[],
        name="dataset1"
    )
    mock_data2 = NodeDataPandasDf(
        data=df2,
        dataExample=df2.head(),
        nodeSchema=[],
        name="dataset2"
    )
    
    merge_transform.inputs['dataset1'].get_node_data.return_value = mock_data1
    merge_transform.inputs['dataset2'].get_node_data.return_value = mock_data2
    
    # Execute
    result = merge_transform.process(sample=False)
    
    # Assert
    assert result == StatusNode.Valid
    merge_transform.outputs['out'].set_node_data.assert_called_once()
    
    # Verify merged data
    call_args = merge_transform.outputs['out'].set_node_data.call_args[0][0]
    result_df = call_args.data
    
    assert 'merged_column' in result_df.columns
    assert len(result_df) == 6  # 3 from df1 + 3 from df2
    expected_values = ['A', 'B', 'C', 'X', 'Y', 'Z']
    assert list(result_df['merged_column']) == expected_values


def test_merge_sample_mode(merge_transform, sample_dataframes):
    """Test merge in sample mode"""
    df1, df2 = sample_dataframes
    
    # Setup
    mock_data1 = NodeDataPandasDf(
        data=df1,
        dataExample=df1.head(2),
        nodeSchema=[],
        name="dataset1"
    )
    mock_data2 = NodeDataPandasDf(
        data=df2,
        dataExample=df2.head(1),
        nodeSchema=[],
        name="dataset2"
    )
    
    merge_transform.inputs['dataset1'].get_node_data.return_value = mock_data1
    merge_transform.inputs['dataset2'].get_node_data.return_value = mock_data2
    
    # Execute
    result = merge_transform.process(sample=True)
    
    # Assert
    assert result == StatusNode.Valid
    
    call_args = merge_transform.outputs['out'].set_node_data.call_args[0][0]
    result_df = call_args.dataExample
    
    assert 'merged_column' in result_df.columns
    assert len(result_df) == 3  # 2 from df1 sample + 1 from df2 sample


def test_merge_parquet_files(merge_transform, parquet_files):
    """Test merging parquet files"""
    parquet_path1, parquet_path2 = parquet_files
    
    # Mock NodeDataParquet without actual schema validation
    mock_data1 = Mock(spec=NodeDataParquet)
    mock_data1.data = parquet_path1
    mock_data1.nodeSchema = None
    mock_data1.name = "dataset1"
    
    mock_data2 = Mock(spec=NodeDataParquet)
    mock_data2.data = parquet_path2
    mock_data2.nodeSchema = None
    mock_data2.name = "dataset2"
    
    merge_transform.inputs['dataset1'].get_node_data.return_value = mock_data1
    merge_transform.inputs['dataset2'].get_node_data.return_value = mock_data2
    
    # Execute
    result = merge_transform.process(sample=False)
    
    # Assert
    assert result == StatusNode.Valid
    
    call_args = merge_transform.outputs['out'].set_node_data.call_args[0][0]
    result_df = call_args.data
    
    assert 'merged_column' in result_df.columns
    assert len(result_df) == 6


def test_process_if_parquet(merge_transform, sample_dataframes, tmp_path, monkeypatch):
    """Test parquet processing mode"""
    df1, df2 = sample_dataframes
    monkeypatch.setattr("app.nodes.transforms.merge_transform.settings.upload_dir", str(tmp_path))

    # Setup parquet save mode
    merge_transform.data['parquetSave']['value'] = True

    mock_data1 = NodeDataPandasDf(
        data=df1,
        dataExample=df1.head(),
        nodeSchema=[],
        name="dataset1"
    )
    mock_data2 = NodeDataPandasDf(
        data=df2,
        dataExample=df2.head(),
        nodeSchema=[],
        name="dataset2"
    )

    merge_transform.inputs['dataset1'].get_node_data.return_value = mock_data1
    merge_transform.inputs['dataset2'].get_node_data.return_value = mock_data2

    # Execute
    result = merge_transform.process(sample=False)

    # Assert
    assert result == StatusNode.Valid
    node_data = merge_transform.outputs['out'].set_node_data.call_args[0][0]
    assert isinstance(node_data, NodeDataParquet)
    assert node_data.data == str(tmp_path / "merged_data_test_merge.parquet")
    assert list(pd.read_parquet(node_data.data)['merged_column']) == ['A', 'B', 'C', 'X', 'Y', 'Z']


def test_multiple_mappings(merge_transform, sample_dataframes):
    """Test multiple column mappings"""
    df1, df2 = sample_dataframes
    
    # Setup multiple mappings
    merge_transform.data['dataMapping'] = [
        {
            'id': 'mapping1',
            'sources': [{'id': '1', 'name': 'col1', 'type': 'string', 'datasetId': 'dataset1'}],
            'targetName': 'first_column'
        },
        {
            'id': 'mapping2',
            'sources': [{'id': '2', 'name': 'col2', 'type': 'string', 'datasetId': 'dataset2'}],
            'targetName': 'second_column'
        }
    ]
    
    mock_data1 = NodeDataPandasDf(
        data=df1,
        dataExample=df1.head(),
        nodeSchema=[],
        name="dataset1"
    )
    mock_data2 = NodeDataPandasDf(
        data=df2,
        dataExample=df2.head(),
        nodeSchema=[],
        name="dataset2"
    )
    
    merge_transform.inputs['dataset1'].get_node_data.return_value = mock_data1
    merge_transform.inputs['dataset2'].get_node_data.return_value = mock_data2
    
    # Execute
    result = merge_transform.process(sample=False)
    
    # Assert
    assert result == StatusNode.Valid
    
    call_args = merge_transform.outputs['out'].set_node_data.call_args[0][0]
    result_df = call_args.data
    
    assert 'first_column' in result_df.columns
    assert 'second_column' in result_df.columns
    assert list(result_df['first_column']) == ['A', 'B', 'C']
    assert list(result_df['second_column']) == ['X', 'Y', 'Z']


def test_invalid_data_format(merge_transform):
    """Test with invalid input data format"""
    # Setup
    merge_transform.inputs['dataset1'].get_node_data.return_value = "invalid_format"
    
    # Execute
    result = merge_transform.process(sample=False)
    
    # Assert
    assert result == StatusNode.Error
    assert "is not a handled format" in merge_transform.statusMessage


def test_missing_data_mapping():
    """Test with missing data mapping"""
    data = {'parquetSave': {'value': False}}  # Missing dataMapping
    transform = MergeTransform(id="test_merge", data=data)
    
    with pytest.raises(ValueError, match="Data Mapping is required"):
        transform._retreiveColumnsMapping()


def test_missing_parquet_save():
    """Test with missing parquet save configuration"""
    data = {'dataMapping': []}  # Missing parquetSave
    transform = MergeTransform(id="test_merge", data=data)
    
    with pytest.raises(ValueError, match="Data Mapping is required"):
        transform._retreiveColumnsMapping()


def test_retrieve_columns_mapping_valid(merge_transform):
    """Test valid columns mapping retrieval"""
    mappings, parquet_save = merge_transform._retreiveColumnsMapping()
    
    assert len(mappings) == 1
    assert mappings[0].targetName == 'merged_column'
    assert len(mappings[0].sources) == 2
    assert parquet_save == False


def test_missing_input_dataset(merge_transform, sample_dataframes):
    """Test with missing input dataset"""
    df1, _ = sample_dataframes
    
    # Setup - only provide dataset1, not dataset2
    mock_data1 = NodeDataPandasDf(
        data=df1,
        dataExample=df1.head(),
        nodeSchema=[],
        name="dataset1"
    )
    
    merge_transform.inputs['dataset1'].get_node_data.return_value = mock_data1
    merge_transform.inputs.pop('dataset2')  # Remove dataset2
    
    # Execute - should not fail, just skip missing datasets
    result = merge_transform.process(sample=False)
    
    # Assert
    assert result == StatusNode.Valid


@patch('traceback.print_exc')
def test_exception_handling(mock_print_exc, merge_transform):
    """Test exception handling"""
    # Setup
    merge_transform.inputs['dataset1'].get_node_data.side_effect = Exception("Test error")
    
    # Execute
    result = merge_transform.process(sample=False)
    
    # Assert
    assert result == StatusNode.Error
    assert merge_transform.statusMessage == "Test error"
    assert merge_transform.errorStackTrace is not None
    mock_print_exc.assert_called_once()


@patch('app.utils.utils.generate_pandas_schema')
def test_empty_column_data(mock_generate_schema, merge_transform):
    """Test with empty column data"""
    # Mock the schema generation to return a valid schema for empty DataFrames
    from app.models.interface.dataset_schema import PandasColumn, PandasSchema
    
    mock_schema = PandasSchema(root=[
        PandasColumn(
            name='merged_column',
            dtype='object',
            nullable=True,
            count=0,
            nested=None
        )
    ])
    mock_generate_schema.return_value = mock_schema
    
    # Setup empty DataFrames
    empty_df1 = pd.DataFrame({'col1': []})
    empty_df2 = pd.DataFrame({'col2': []})
    
    mock_data1 = NodeDataPandasDf(
        data=empty_df1,
        dataExample=empty_df1,
        nodeSchema=[],
        name="dataset1"
    )
    mock_data2 = NodeDataPandasDf(
        data=empty_df2,
        dataExample=empty_df2,
        nodeSchema=[],
        name="dataset2"
    )
    
    merge_transform.inputs['dataset1'].get_node_data.return_value = mock_data1
    merge_transform.inputs['dataset2'].get_node_data.return_value = mock_data2
    
    # Execute
    result = merge_transform.process(sample=False)
    
    # Assert
    assert result == StatusNode.Valid
    mock_generate_schema.assert_called_once()
    
    # Verify the output contains an empty merged column
    call_args = merge_transform.outputs['out'].set_node_data.call_args[0][0]
    result_df = call_args.data
    
    assert 'merged_column' in result_df.columns
    assert len(result_df) == 0  # Empty result


if __name__ == "__main__":
    pytest.main([__file__])