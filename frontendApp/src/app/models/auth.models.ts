/**
 * Authentication Models and Interfaces
 */

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  must_change_password: boolean;
  last_login: string | null;
  created_at: string;
  updated_at: string;
  config: UserConfig;
  owned_datasets: string[];
  owned_workflows: string[];
  shared_datasets: string[];
  shared_workflows: string[];
}

export interface UserConfig {
  credentials: { [key: string]: string };
  settings: { [key: string]: any };
}

export enum UserRole {
  ADMIN = 'admin',
  USER = 'user'
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  full_name: string;
  password: string;
  role?: UserRole;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface UserUpdate {
  email?: string;
  full_name?: string;
  password?: string;
  config?: UserConfig;
}
