"""
Migration script to assign ownership of existing datasets and workflows to admin user
"""
import logging
import asyncio
from app.models.interface.dataset_interface import Dataset
from app.models.interface.workflow_interface import IProject
from app.models.interface.user_interface import User
from app.enums.user_role import UserRole
from app.config.database import db_config
from app.config.settings import settings

logger = logging.getLogger(__name__)


async def migrate_resource_ownership():
    """
    Migrate existing datasets and workflows to be owned by admin user
    """
    try:
        logger.info("Starting resource ownership migration...")
        
        # Initialize database
        await db_config.connect(settings, [Dataset, IProject, User])
        
        # Find admin user
        admin = await User.find_one(User.role == UserRole.ADMIN)
        
        if not admin:
            logger.error("No admin user found! Cannot proceed with migration")
            return False
        
        logger.info(f"Using admin user: {admin.username} (ID: {admin.id})")
        
        # Migrate datasets without owner
        datasets_updated = 0
        datasets = await Dataset.find(Dataset.owner_id == None).to_list()
        
        logger.info(f"Found {len(datasets)} datasets without owner")
        
        for dataset in datasets:
            dataset.owner_id = admin.id
            await dataset.save()
            
            # Add to admin's owned datasets
            if dataset.id not in admin.owned_datasets:
                admin.owned_datasets.append(dataset.id)
            
            datasets_updated += 1
            logger.debug(f"Assigned dataset {dataset.id} to admin")
        
        # Migrate workflows without owner
        workflows_updated = 0
        workflows = await IProject.find(IProject.owner_id == None).to_list()
        
        logger.info(f"Found {len(workflows)} workflows without owner")
        
        for workflow in workflows:
            workflow.owner_id = admin.id
            await workflow.save()
            
            # Add to admin's owned workflows
            if workflow.id not in admin.owned_workflows:
                admin.owned_workflows.append(workflow.id)
            
            workflows_updated += 1
            logger.debug(f"Assigned workflow {workflow.id} to admin")
        
        # Save admin user with updated owned resources
        await admin.save()
        
        logger.info("✅ Migration completed successfully!")
        logger.info(f"   - Datasets assigned to admin: {datasets_updated}")
        logger.info(f"   - Workflows assigned to admin: {workflows_updated}")
        
        await db_config.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("="*60)
    logger.info("RESOURCE OWNERSHIP MIGRATION")
    logger.info("="*60)
    
    success = asyncio.run(migrate_resource_ownership())
    
    if success:
        logger.info("✅ Migration script completed successfully")
    else:
        logger.error("❌ Migration script failed")
        exit(1)
