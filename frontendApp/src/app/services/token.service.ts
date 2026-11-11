import { Injectable, inject } from '@angular/core';
import { Storage } from '@ionic/storage-angular';

/**
 * Token Service
 * Manages JWT tokens with hybrid storage:
 * - Access token: In-memory (cleared on page refresh)
 * - Refresh token: Ionic Storage (persistent if "Remember Me" is checked)
 */
@Injectable({
  providedIn: 'root'
})
export class TokenService {
  private readonly storage = inject(Storage);

  private accessToken: string | null = null;
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private readonly REMEMBER_ME_KEY = 'remember_me';
  private storageReady: Promise<void> | null = null;

  /**
   * Initialize Ionic Storage on first use.
   * The pending creation is shared, so concurrent callers create the storage only once,
   * and a failed creation is retried on the next call.
   */
  private initStorage(): Promise<void> {
    this.storageReady ??= this.storage.create().then(
      () => undefined,
      (error) => {
        this.storageReady = null;
        throw error;
      }
    );
    return this.storageReady;
  }

  /**
   * Save tokens
   * @param accessToken JWT access token
   * @param refreshToken JWT refresh token
   * @param rememberMe Whether to persist refresh token
   */
  async saveTokens(accessToken: string, refreshToken: string, rememberMe: boolean = false): Promise<void> {
    await this.initStorage();

    // Always store access token in memory
    this.accessToken = accessToken;

    // Store refresh token based on "Remember Me"
    if (rememberMe) {
      await this.storage.set(this.REFRESH_TOKEN_KEY, refreshToken);
      await this.storage.set(this.REMEMBER_ME_KEY, true);
    } else {
      // Store in sessionStorage (cleared on browser close)
      sessionStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
      await this.storage.set(this.REMEMBER_ME_KEY, false);
    }
  }

  /**
   * Get access token from memory
   */
  getAccessToken(): string | null {
    return this.accessToken;
  }

  /**
   * Get refresh token from storage
   */
  async getRefreshToken(): Promise<string | null> {
    await this.initStorage();

    // Check if "Remember Me" was used
    const rememberMe = await this.storage.get(this.REMEMBER_ME_KEY);

    if (rememberMe) {
      // Get from persistent storage
      return await this.storage.get(this.REFRESH_TOKEN_KEY);
    } else {
      // Get from sessionStorage
      return sessionStorage.getItem(this.REFRESH_TOKEN_KEY);
    }
  }

  /**
   * Set access token in memory (used after refresh)
   */
  setAccessToken(token: string): void {
    this.accessToken = token;
  }

  /**
   * Clear all tokens (logout)
   */
  async clearTokens(): Promise<void> {
    await this.initStorage();

    // Clear memory
    this.accessToken = null;

    // Clear persistent storage
    await this.storage.remove(this.REFRESH_TOKEN_KEY);
    await this.storage.remove(this.REMEMBER_ME_KEY);

    // Clear session storage
    sessionStorage.removeItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * Check if user has valid tokens
   */
  async hasTokens(): Promise<boolean> {
    const refreshToken = await this.getRefreshToken();
    return !!refreshToken || !!this.accessToken;
  }

  /**
   * Check if tokens are stored persistently (Remember Me)
   */
  async isRememberMe(): Promise<boolean> {
    await this.initStorage();
    return await this.storage.get(this.REMEMBER_ME_KEY) || false;
  }

  /**
   * Decode JWT token to get payload (without verification)
   * @param token JWT token
   */
  decodeToken(token: string): any {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        return null;
      }

      const payload = parts[1];
      const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
      return JSON.parse(decoded);
    } catch (error) {
      console.error('Error decoding token:', error);
      return null;
    }
  }

  /**
   * Check if token is expired
   * @param token JWT token
   */
  isTokenExpired(token: string): boolean {
    try {
      const decoded = this.decodeToken(token);
      if (!decoded || !decoded.exp) {
        return true;
      }

      const expirationDate = new Date(decoded.exp * 1000);
      const now = new Date();

      return expirationDate < now;
    } catch (error) {
      console.error('Error checking token expiration:', error);
      return true;
    }
  }

  /**
   * Get token expiration date
   * @param token JWT token
   */
  getTokenExpiration(token: string): Date | null {
    try {
      const decoded = this.decodeToken(token);
      if (!decoded || !decoded.exp) {
        return null;
      }

      return new Date(decoded.exp * 1000);
    } catch (error) {
      console.error('Error reading token expiration:', error);
      return null;
    }
  }

  /**
   * Check if access token needs refresh (5 minutes before expiration)
   */
  shouldRefreshToken(): boolean {
    if (!this.accessToken) {
      return false;
    }

    try {
      const decoded = this.decodeToken(this.accessToken);
      if (!decoded || !decoded.exp) {
        return true;
      }

      const expirationDate = new Date(decoded.exp * 1000);
      const now = new Date();
      const fiveMinutes = 5 * 60 * 1000;

      // Refresh if less than 5 minutes until expiration
      return (expirationDate.getTime() - now.getTime()) < fiveMinutes;
    } catch (error) {
      console.error('Error checking token refresh:', error);
      return true;
    }
  }
}
