"""
Execution context management for workflow execution.

This module provides context variables to track the current user and workflow
during workflow execution, making this information accessible from any node
without explicit parameter passing.
"""

from contextvars import ContextVar
from typing import Optional
from app.models.interface.user_interface import User
from app.models.interface.workflow_interface import IProject

# Context variables for workflow execution
execution_user_var: ContextVar[Optional[User]] = ContextVar('execution_user', default=None)
execution_workflow_var: ContextVar[Optional[IProject]] = ContextVar('execution_workflow', default=None)


class ExecutionContext:
    """
    Centralized execution context manager for workflows.
    
    Provides static methods to set and retrieve the current execution context,
    including the authenticated user and the workflow being executed.
    
    Usage:
        # Set context at workflow execution start
        ExecutionContext.set_user(current_user)
        ExecutionContext.set_workflow(workflow_project)
        
        # Get context from any node
        user = ExecutionContext.get_user()
        workflow = ExecutionContext.get_workflow()
        workflow_id = ExecutionContext.get_workflow_id()
    """
    
    @staticmethod
    def set_user(user: Optional[User]) -> None:
        """
        Set the current execution user context.
        
        Args:
            user: The authenticated user executing the workflow, or None to clear
        """
        execution_user_var.set(user)
    
    @staticmethod
    def get_user() -> Optional[User]:
        """
        Get the current execution user.
        
        Returns:
            The authenticated user, or None if no user context is set
        """
        return execution_user_var.get()
    
    @staticmethod
    def set_workflow(workflow: Optional[IProject]) -> None:
        """
        Set the current workflow project context.
        
        Args:
            workflow: The IProject instance being executed, or None to clear
        """
        execution_workflow_var.set(workflow)
    
    @staticmethod
    def get_workflow() -> Optional[IProject]:
        """
        Get the current workflow project.
        
        Returns:
            The complete IProject instance, or None if no workflow context is set
        """
        return execution_workflow_var.get()
    
    @staticmethod
    def get_workflow_id() -> Optional[str]:
        """
        Get the current workflow ID (convenience method).
        
        Returns:
            The workflow ID, or None if no workflow context is set
        """
        workflow = execution_workflow_var.get()
        return workflow.id if workflow else None
    
    @staticmethod
    def get_workflow_name() -> Optional[str]:
        """
        Get the current workflow name (convenience method).
        
        Returns:
            The workflow name, or None if no workflow context is set
        """
        workflow = execution_workflow_var.get()
        return workflow.name if workflow else None
    
    @staticmethod
    def clear() -> None:
        """
        Clear all execution context variables.
        
        Should be called after workflow execution completes to prevent
        context leakage between different workflow executions.
        """
        execution_user_var.set(None)
        execution_workflow_var.set(None)
    
    @staticmethod
    def get_context_summary() -> dict:
        """
        Get a summary of the current execution context (useful for debugging).
        
        Returns:
            Dictionary with user and workflow information
        """
        user = execution_user_var.get()
        workflow = execution_workflow_var.get()
        
        return {
            "user": {
                "id": str(user.id),
                "username": user.username,
                "role": user.role.value
            } if user else None,
            "workflow": {
                "id": workflow.id,
                "name": workflow.name,
                "revision": workflow.revision
            } if workflow else None
        }
