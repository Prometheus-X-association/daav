import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { of } from 'rxjs';

import { AuthService } from './auth.service';
import { TokenService } from './token.service';
import { BaseService } from './base.service.service';
import { DatasetService } from './dataset.service';
import { WorkflowService } from './worflow.service';
import { Token, User } from '../models/auth.models';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;
  let tokenServiceSpy: jasmine.SpyObj<TokenService>;
  let datasetServiceSpy: jasmine.SpyObj<DatasetService>;
  let workflowServiceSpy: jasmine.SpyObj<WorkflowService>;
  let urlBack: string;

  const token: Token = { access_token: 'access', refresh_token: 'refresh', token_type: 'bearer' };
  const user = { id: 'user-1', username: 'jdoe', role: 'user', must_change_password: false } as User;

  // Let the pending promises and macrotasks (lazy imports) run
  const settle = () => new Promise(resolve => setTimeout(resolve));

  beforeEach(() => {
    let accessToken: string | null = null;
    tokenServiceSpy = jasmine.createSpyObj<TokenService>('TokenService', ['saveTokens', 'getAccessToken', 'clearTokens']);
    tokenServiceSpy.saveTokens.and.callFake(async (access: string) => {
      accessToken = access;
    });
    tokenServiceSpy.getAccessToken.and.callFake(() => accessToken);
    tokenServiceSpy.clearTokens.and.returnValue(Promise.resolve());

    datasetServiceSpy = jasmine.createSpyObj<DatasetService>('DatasetService', ['get', 'clearDatasets']);
    workflowServiceSpy = jasmine.createSpyObj<WorkflowService>('WorkflowService', ['getWorkflows', 'clearWorkflows']);
    workflowServiceSpy.getWorkflows.and.returnValue(of([]));

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: TokenService, useValue: tokenServiceSpy },
        { provide: Router, useValue: jasmine.createSpyObj<Router>('Router', { navigate: Promise.resolve(true) }) },
        { provide: DatasetService, useValue: datasetServiceSpy },
        { provide: WorkflowService, useValue: workflowServiceSpy }
      ]
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
    urlBack = TestBed.inject(BaseService).urlBack;
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('login', () => {
    it('should emit only once the tokens are saved and the current user is loaded', async () => {
      let resolveSave!: () => void;
      tokenServiceSpy.saveTokens.and.callFake(() => new Promise<void>(resolve => {
        resolveSave = resolve;
      }));
      tokenServiceSpy.getAccessToken.and.returnValue('access');

      const emissions: { token: Token; currentUser: User | null }[] = [];
      const completed = new Promise<void>((resolve, reject) => {
        service.login('jdoe', 'secret', true).subscribe({
          next: emitted => emissions.push({ token: emitted, currentUser: service.currentUserValue }),
          error: reject,
          complete: resolve
        });
      });

      httpMock.expectOne(`${urlBack}/auth/login`).flush(token);
      expect(tokenServiceSpy.saveTokens).toHaveBeenCalledWith('access', 'refresh', true);

      // Tokens not saved yet: nothing emitted, the user is not requested
      await settle();
      expect(emissions).toEqual([]);
      httpMock.expectNone(`${urlBack}/auth/me`);

      resolveSave();
      await settle();

      // Tokens saved, user being loaded: still nothing emitted
      const meRequest = httpMock.expectOne(`${urlBack}/auth/me`);
      expect(meRequest.request.headers.get('Authorization')).toBe('Bearer access');
      expect(emissions).toEqual([]);

      meRequest.flush(user);
      await completed;

      expect(emissions).toEqual([{ token, currentUser: user }]);
    });

    it('should load the user data once', async () => {
      const login = new Promise<void>((resolve, reject) => {
        service.login('jdoe', 'secret').subscribe({ error: reject, complete: resolve });
      });

      httpMock.expectOne(`${urlBack}/auth/login`).flush(token);
      await settle();
      httpMock.expectOne(`${urlBack}/auth/me`).flush(user);
      await login;

      expect(datasetServiceSpy.get).toHaveBeenCalledTimes(1);
      expect(workflowServiceSpy.getWorkflows).toHaveBeenCalledTimes(1);
    });

    it('should fail instead of emitting when the tokens cannot be saved', async () => {
      spyOn(console, 'error');
      tokenServiceSpy.saveTokens.and.callFake(() => Promise.reject(new Error('Storage unavailable')));
      const next = jasmine.createSpy('next');

      const failure = new Promise<Error>((resolve, reject) => {
        service.login('jdoe', 'secret').subscribe({ next, error: resolve, complete: () => reject(new Error('completed')) });
      });
      httpMock.expectOne(`${urlBack}/auth/login`).flush(token);

      expect((await failure).message).toBe('Storage unavailable');
      expect(next).not.toHaveBeenCalled();
      httpMock.expectNone(`${urlBack}/auth/me`);
    });

    it('should fail with the API message when the credentials are rejected', async () => {
      spyOn(console, 'error');
      const failure = new Promise<Error>((resolve, reject) => {
        service.login('jdoe', 'wrong').subscribe({ error: resolve, complete: () => reject(new Error('completed')) });
      });
      httpMock.expectOne(`${urlBack}/auth/login`).flush({ detail: 'Incorrect username or password' }, { status: 401, statusText: 'Unauthorized' });

      expect((await failure).message).toBe('Incorrect username or password');
      expect(tokenServiceSpy.saveTokens).not.toHaveBeenCalled();
    });
  });
});
