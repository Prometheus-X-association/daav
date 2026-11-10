import { Routes } from '@angular/router';
import { adminGuard } from '../../guards/admin.guard';
import { AccountPage } from './account.page';
import { ProfileSectionComponent } from './profile/profile-section.component';
import { SecuritySectionComponent } from './security/security-section.component';
import { CredentialsSectionComponent } from './credentials/credentials-section.component';
import { UsersSectionComponent } from './users/users-section.component';

export const routes: Routes = [
  {
    path: '',
    component: AccountPage,
    children: [
      {
        path: 'profile',
        title: 'Profile - DAAV',
        component: ProfileSectionComponent
      },
      {
        path: 'security',
        title: 'Security - DAAV',
        component: SecuritySectionComponent
      },
      {
        path: 'credentials',
        title: 'Credentials - DAAV',
        component: CredentialsSectionComponent
      },
      {
        path: 'users',
        title: 'Users - DAAV',
        canActivate: [adminGuard],
        component: UsersSectionComponent
      },
      {
        path: '',
        redirectTo: 'profile',
        pathMatch: 'full'
      }
    ]
  }
];
