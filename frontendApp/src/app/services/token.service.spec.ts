import { TestBed } from '@angular/core/testing';
import { Storage } from '@ionic/storage-angular';

import { TokenService } from './token.service';

describe('TokenService', () => {
  let service: TokenService;
  let storageSpy: jasmine.SpyObj<Storage>;

  beforeEach(() => {
    storageSpy = jasmine.createSpyObj<Storage>('Storage', ['create', 'get', 'set', 'remove']);
    storageSpy.create.and.callFake(() => Promise.resolve(storageSpy));
    storageSpy.get.and.returnValue(Promise.resolve(null));
    storageSpy.set.and.returnValue(Promise.resolve());
    storageSpy.remove.and.returnValue(Promise.resolve());

    TestBed.configureTestingModule({
      providers: [{ provide: Storage, useValue: storageSpy }]
    });
    service = TestBed.inject(TokenService);
  });

  afterEach(() => {
    sessionStorage.removeItem('refresh_token');
  });

  it('should not create the storage in the constructor', () => {
    expect(service).toBeTruthy();
    expect(storageSpy.create).not.toHaveBeenCalled();
  });

  it('should create the storage only once for concurrent calls', async () => {
    await Promise.all([service.getRefreshToken(), service.isRememberMe(), service.clearTokens()]);
    await service.getRefreshToken();

    expect(storageSpy.create).toHaveBeenCalledTimes(1);
  });

  it('should retry the storage creation after a failure', async () => {
    storageSpy.create.and.returnValues(
      Promise.reject(new Error('storage unavailable')),
      Promise.resolve(storageSpy)
    );

    await expectAsync(service.isRememberMe()).toBeRejectedWithError('storage unavailable');
    await expectAsync(service.isRememberMe()).toBeResolvedTo(false);
    expect(storageSpy.create).toHaveBeenCalledTimes(2);
  });

  it('should keep the refresh token in session storage without remember me', async () => {
    await service.saveTokens('access', 'refresh', false);

    expect(service.getAccessToken()).toBe('access');
    expect(sessionStorage.getItem('refresh_token')).toBe('refresh');
    expect(storageSpy.set).toHaveBeenCalledWith('remember_me', false);
    expect(await service.getRefreshToken()).toBe('refresh');
  });
});
