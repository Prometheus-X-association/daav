import { Injectable, signal, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable , tap } from 'rxjs';
import { Project } from '../models/interfaces/project';
import { BaseService } from './base.service.service';


@Injectable({
  providedIn: 'root'
})
export class WorkflowService extends BaseService {
  private readonly http = inject(HttpClient);

  private readonly apiUrl = this.urlBack+"/workflows";

  private readonly workflowsSignals = signal<Project[]>([]);
  workflows = this.workflowsSignals.asReadonly();

  // Get all workflows
  getWorkflows(): Observable<Project[]> {
    return this.http.get<Project[]>(this.apiUrl + "/").pipe(
      tap(workflows => this.workflowsSignals.set(workflows))
    );
  }

  // Get workflow by ID
  getWorkflow(id: string): Observable<Project> {
    return this.http.get<Project>(`${this.apiUrl}/${id}`);
  }

  // Create new workflow
  createWorkflow(workflow: Project): Observable<Project> {
    return this.http.post<Project>(this.apiUrl + "/", workflow);
  }

  // Update workflow
  updateWorkflow(workflow: Project): Observable<Project> {
    return this.http.put<Project>(this.apiUrl + "/", workflow);
  }

  // Delete workflow
  deleteWorkflow(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }

  // Execute workflow by ID
  executeWorkflow(id: string): Observable<Project> {
    return this.http.post<Project>(`${this.apiUrl}/execute/${id}`, {});
  }

  // Execute workflow from JSON
  executeWorkflowJson(workflow: Project): Observable<Project> {
    return this.http.post<Project>(`${this.apiUrl}/execute`, workflow);
  }

  // Execute specific node in a workflow by ID
  executeNode(workflowId: string, nodeId: string): Observable<Project> {
    return this.http.post<Project>(`${this.apiUrl}/execute_node/${workflowId}/${nodeId}`, {});
  }

  // Execute specific node from workflow JSON
  executeNodeJson(workflow: Project, nodeId: string): Observable<Project> {
    return this.http.post<Project>(`${this.apiUrl}/execute_node/${nodeId}`, workflow);
  }

  /**
   * Clear all workflows from cache (called on logout)
   */
  clearWorkflows(): void {
    this.workflowsSignals.set([]);
  }
}
