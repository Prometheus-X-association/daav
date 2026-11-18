import { Routes } from '@angular/router';
import { AuthGuard } from './guards/auth.guard';

export const routes: Routes = [
  // Authentication routes (public)
  {
    path: 'login',
    title: 'Login - DAAV',
    loadComponent: () => import('./pages/login/login.page').then(m => m.LoginPage)
  },
  {
    path: 'register',
    title: 'Create account - DAAV',
    loadComponent: () => import('./pages/register/register.page').then(m => m.RegisterPage)
  },
  {
    path: 'forgot-password',
    title: 'Forgot password - DAAV',
    loadComponent: () => import('./pages/forgot-password/forgot-password.page').then(m => m.ForgotPasswordPage)
  },
  {
    path: 'reset-password',
    title: 'Reset password - DAAV',
    loadComponent: () => import('./pages/reset-password/reset-password.page').then(m => m.ResetPasswordPage)
  },
  // Protected routes
  {
    path: 'change-password',
    title: 'Change password - DAAV',
    canActivate: [AuthGuard],
    data: { passwordChangeRoute: true },
    loadComponent: () => import('./pages/change-password/change-password.page').then(m => m.ChangePasswordPage)
  },
  {
    path: '',
    title: 'BB11 - DAAV',
    canActivate: [AuthGuard],
    loadChildren: () => import('./tabs/tabs.routes').then(m => m.routes)
  },
  {
    path: 'account',
    title: 'Account - DAAV',
    canActivate: [AuthGuard],
    loadChildren: () => import('./pages/account/account.routes').then(m => m.routes)
  },
  {
    path: 'workflow',
    title: 'Workflow - DAAV',
    canActivate: [AuthGuard],
    loadComponent: () => import('./pages/worflow/workflow.page').then(m => m.WorkflowPage)
  },
  {
    path: 'test-composant',
    title: 'Test - DAAV',
    canActivate: [AuthGuard],
    loadComponent: () => import('./pages/test-composant/test-composant.page').then(m => m.TestComposantPage)
  },
  // Redirect to login if no route matches
  {
    path: '**',
    redirectTo: 'login',
    pathMatch: 'full'
  }
];
