from typing import Optional, Any

import pandas as pd
from pydantic import ConfigDict
from sqlalchemy import create_engine
from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf
from app.nodes.outputs.output_node import OutputNode


class ExampleOutput(OutputNode):

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new ExampleInput instance.

        Args:
            id (str): Unique identifier for the node
            data (Any): Data associated with the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)    

    def process(self,sample = False):
        print(f"inside ouput {len(self.inputs)}")
        for input in self.inputs.values():

            if (input.get_connected_node()):
                print("inside input port")
                data = input.get_node_data()
                if isinstance(data, NodeDataPandasDf):
                    df = data.data
                    if not isinstance(df, pd.DataFrame):
                        raise ValueError("Input data is not a pandas DataFrame")
                    # Export the DataFrame to a SQL file

                    # Create an in-memory SQLite database
                    engine = create_engine('sqlite://', echo=False)

                    # Write the DataFrame to the SQL database
                    df.to_sql('example_table', con=engine, index=False, if_exists='replace')

                    # Export the SQL database to a file
                    with open('output.sql', 'w') as f:
                        print('Exporting SQL database to output.sql')
                        for line in engine.raw_connection().driver_connection.iterdump():
                            print('%s\n' % line)
                            f.write('%s\n' % line)
                break        
        
        return StatusNode.Valid

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )        