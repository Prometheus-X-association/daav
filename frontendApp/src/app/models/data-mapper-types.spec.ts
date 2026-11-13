
import { DataMapperUtils } from './data-mapper-types';
import { NodeDataMysql } from './node-data';

describe('DataMapperUtils', () => {
  it('should transform NodeDataMysql to DatasetMapper', () => {
    const nodeData: NodeDataMysql = {
      type: 'mysql',
      name: 'testNode',
      nodeSchema: [
        {
          Field: 'id', Type: 'int',
          Null: '',
          Key: '',
          Default: undefined,
          Extra: ''
        },
        {
          Field: 'name', Type: 'varchar',
          Null: '',
          Key: '',
          Default: undefined,
          Extra: ''
        },
        {
          Field: 'email', Type: 'varchar',
          Null: '',
          Key: '',
          Default: undefined,
          Extra: ''
        },
        {
          Field: 'created_at', Type: 'datetime',
          Null: '',
          Key: '',
          Default: undefined,
          Extra: ''
        },
      ],
      dataExample: [
        { id: 1, name: 'John Doe', email: 'john@example.com', created_at: '2023-01-01' },
        { id: 2, name: 'Jane Doe', email: 'jane@example.com', created_at: '2023-01-02' },
      ],
      database: '',
      table: '',
      datasetId: ''
    };

    const result = DataMapperUtils.nodeDataToMapper(nodeData, 'sourceKey');

    expect(result).toEqual({
      id: 'sourceKey',
      name: 'testNode',
      columns: [
        {
          id: 'id',
          name: 'id',
          type: 'id',
          sample: [1, 2],
          datasetId: 'sourceKey',
        },
        {
          id: 'name',
          name: 'name',
          type: 'string',
          sample: ['John Doe', 'Jane Doe'],
          datasetId: 'sourceKey',
        },
        {
          id: 'email',
          name: 'email',
          type: 'email',
          sample: ['john@example.com', 'jane@example.com'],
          datasetId: 'sourceKey',
        },
        {
          id: 'created_at',
          name: 'created_at',
          type: 'date',
          sample: ['2023-01-01', '2023-01-02'],
          datasetId: 'sourceKey',
        },
      ],
    });
  });

  it('should detect correct DataType for MySQL fields', () => {
    expect(DataMapperUtils.detectTypeFieldMysql('int', '1', 'id')).toBe('id');
    expect(DataMapperUtils.detectTypeFieldMysql('varchar', 'john@example.com', 'email')).toBe('email');
    expect(DataMapperUtils.detectTypeFieldMysql('varchar', 'https://example.com', 'url')).toBe('url');
    expect(DataMapperUtils.detectTypeFieldMysql('varchar', '123-456-7890', 'phone')).toBe('phone');
    expect(DataMapperUtils.detectTypeFieldMysql('varchar', '50%', 'percentage')).toBe('percentage');
    expect(DataMapperUtils.detectTypeFieldMysql('datetime', '2023-01-01', 'created_at')).toBe('date');
    expect(DataMapperUtils.detectTypeFieldMysql('tinyint(1)', '1', 'is_active')).toBe('number');
    expect(DataMapperUtils.detectTypeFieldMysql('varchar', 'some text', 'description')).toBe('string');
  });

  it('should detect currency, empty text and other MySQL types', () => {
    expect(DataMapperUtils.detectTypeFieldMysql('decimal(10,2)', '9.99', 'price')).toBe('currency');
    expect(DataMapperUtils.detectTypeFieldMysql('double', '9.99', 'cost')).toBe('currency');
    expect(DataMapperUtils.detectTypeFieldMysql('float', '9.99', 'total_price')).toBe('number');
    expect(DataMapperUtils.detectTypeFieldMysql('bigint', '3', 'quantity')).toBe('number');
    expect(DataMapperUtils.detectTypeFieldMysql('text', '', 'email')).toBe('string');
    expect(DataMapperUtils.detectTypeFieldMysql('char(2)', 'FR', 'country')).toBe('string');
    expect(DataMapperUtils.detectTypeFieldMysql('blob', 'abc', 'telephone')).toBe('phone');
    expect(DataMapperUtils.detectTypeFieldMysql('varchar', '10 %', 'ratio')).toBe('percentage');
    expect(DataMapperUtils.detectTypeFieldMysql('varchar', '10', 'percent_done')).toBe('percentage');
    expect(DataMapperUtils.detectTypeFieldMysql('timestamp', '2023-01-01', 'updated')).toBe('date');
    expect(DataMapperUtils.detectTypeFieldMysql('date', '2023-01-01', 'day')).toBe('date');
    expect(DataMapperUtils.detectTypeFieldMysql('boolean', 'true', 'active')).toBe('boolean');
    expect(DataMapperUtils.detectTypeFieldMysql('json', '{}', 'payload')).toBe('string');
    expect(DataMapperUtils.detectTypeFieldMysql('varchar', 'x', 'user_id')).toBe('id');
    expect(DataMapperUtils.detectTypeFieldMysql('varchar', 'ftp://files.example.com/a', 'link')).toBe('url');
  });

  it('should detect correct DataType for Pandas fields', () => {
    expect(DataMapperUtils.detectTypeFieldPandas('int', '1', 'id')).toBe('id');
    expect(DataMapperUtils.detectTypeFieldPandas('int', '1', 'quantity')).toBe('number');
    expect(DataMapperUtils.detectTypeFieldPandas('float', '1.5', 'ratio')).toBe('number');
    expect(DataMapperUtils.detectTypeFieldPandas('int', '3', 'price')).toBe('currency');
    expect(DataMapperUtils.detectTypeFieldPandas('float', '3.5', 'cost')).toBe('currency');
    expect(DataMapperUtils.detectTypeFieldPandas('object', 'john@example.com', 'contact')).toBe('email');
    expect(DataMapperUtils.detectTypeFieldPandas('object', 'https://example.com', 'site')).toBe('url');
    expect(DataMapperUtils.detectTypeFieldPandas('object', '0102030405', 'phone')).toBe('phone');
    expect(DataMapperUtils.detectTypeFieldPandas('object', '50%', 'ratio')).toBe('percentage');
    expect(DataMapperUtils.detectTypeFieldPandas('object', '50', 'percentage')).toBe('percentage');
    expect(DataMapperUtils.detectTypeFieldPandas('object', 'some text', 'description')).toBe('string');
    expect(DataMapperUtils.detectTypeFieldPandas('object', '', 'email')).toBe('string');
    expect(DataMapperUtils.detectTypeFieldPandas('datetime64[ns]', '2023-01-01', 'created_at')).toBe('date');
    expect(DataMapperUtils.detectTypeFieldPandas('bool', 'true', 'is_active')).toBe('boolean');
    expect(DataMapperUtils.detectTypeFieldPandas('int64', '1', 'quantity')).toBe('string');
    expect(DataMapperUtils.detectTypeFieldPandas('constructor', '1', 'quantity')).toBe('string');
    expect(DataMapperUtils.detectTypeFieldPandas('toString', '1', 'quantity')).toBe('string');
  });

  it('should detect Pandas object fields whose value is not text', () => {
    const value = 42 as unknown as string;
    expect(DataMapperUtils.detectTypeFieldPandas('object', value, 'amount')).toBe('string');
    expect(DataMapperUtils.detectTypeFieldPandas('object', value, 'percent')).toBe('percentage');
    expect(DataMapperUtils.detectTypeFieldPandas('object', value, 'tel')).toBe('phone');
    const list = ['a@b.co'] as unknown as string;
    expect(DataMapperUtils.detectTypeFieldPandas('object', list, 'contacts')).toBe('email');
    expect(DataMapperUtils.detectTypeFieldPandas('object', null, 'amount')).toBe('string');
  });

  it('should detect the DataType from the value type', () => {
    expect(DataMapperUtils.detectTypeFieldFromValueType(1, 'id')).toBe('id');
    expect(DataMapperUtils.detectTypeFieldFromValueType(1, 'quantity')).toBe('number');
    expect(DataMapperUtils.detectTypeFieldFromValueType(1, 'price')).toBe('currency');
    expect(DataMapperUtils.detectTypeFieldFromValueType('a@b.co', 'contact')).toBe('email');
    expect(DataMapperUtils.detectTypeFieldFromValueType('http://a.b', 'site')).toBe('url');
    expect(DataMapperUtils.detectTypeFieldFromValueType('1', 'phone')).toBe('phone');
    expect(DataMapperUtils.detectTypeFieldFromValueType('5%', 'ratio')).toBe('percentage');
    expect(DataMapperUtils.detectTypeFieldFromValueType('', 'label')).toBe('string');
    expect(DataMapperUtils.detectTypeFieldFromValueType(true, 'active')).toBe('boolean');
    expect(DataMapperUtils.detectTypeFieldFromValueType(new Date(), 'day')).toBe('date');
    expect(DataMapperUtils.detectTypeFieldFromValueType(null, 'other')).toBe('string');
  });
});
