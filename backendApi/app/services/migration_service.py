import asyncio
import json
import os
from typing import Dict, Any
from pydantic import TypeAdapter
from app.models.interface.dataset_interface import DatasetUnion
from app.models.interface.workflow_interface import IProject
from app.models.interface.user_interface import User
from app.services.dataset_service import DatasetService
from app.services.workflow_service import workflow_service


def _read_text_file(path: str) -> str:
    """Read a text file (run in a worker thread by the async migration)"""
    with open(path, 'r') as f:
        return f.read()


class MigrationService:
    
    @staticmethod
    async def migrate_from_config_ini(user: User):
        """Migrate data from config.ini to MongoDB"""
        config_path = "./app/config.ini"
        
        if not os.path.exists(config_path):
            print("❌ config.ini not found")
            return False
        
        try:
            config = json.loads(await asyncio.to_thread(_read_text_file, config_path))
            
            # Migrate datasets
            connections = config.get("connections", [])
            migrated_datasets = 0
            dataset_service = DatasetService()
            
            for conn_data in connections:
                try:
                    type_adapter = TypeAdapter(DatasetUnion)
                    validated_dataset = type_adapter.validate_python(conn_data)
                    
                    result = await dataset_service.add_connection(validated_dataset, user)
                    if result["status"] == "Connection added":
                        migrated_datasets += 1
                        print(f"✅ Migrated dataset: {validated_dataset.name} ({validated_dataset.type})")
                    else:
                        print(f"⚠️  Skipped dataset (already exists): {validated_dataset.name}")
                        
                except Exception as e:
                    print(f"❌ Error migrating dataset {conn_data.get('name', 'Unknown')}: {e}")
            
            # Migrate workflows
            workflows = config.get("workflows", [])
            migrated_workflows = 0
            
            for workflow_data in workflows:
                try:
                    validated_workflow = IProject.model_validate(workflow_data)
                    
                    # Check if workflow already exists
                    if not await workflow_service.workflow_exists(validated_workflow.id):
                        await workflow_service.create_workflow(validated_workflow, user)
                        migrated_workflows += 1
                        print(f"✅ Migrated workflow: {validated_workflow.name} (ID: {validated_workflow.id})")
                    else:
                        print(f"⚠️  Skipped workflow (already exists): {validated_workflow.name}")
                        
                except Exception as e:
                    print(f"❌ Error migrating workflow {workflow_data.get('name', 'Unknown')}: {e}")
            
            print(f"🎉 Migration completed: {migrated_datasets} datasets, {migrated_workflows} workflows migrated")
            
            # Backup the config.ini file
            backup_path = f"{config_path}.backup"
            os.rename(config_path, backup_path)
            print(f"📦 config.ini backed up to {backup_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False