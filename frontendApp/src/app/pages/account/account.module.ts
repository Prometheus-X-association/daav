import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { RouterModule, Routes } from '@angular/router';

import { AccountPage } from './account.page';
import { ProfileSectionComponent } from './profile/profile-section.component';
import { SecuritySectionComponent } from './security/security-section.component';
import { CredentialsSectionComponent } from './credentials/credentials-section.component';
import { UsersSectionComponent } from './users/users-section.component';
import { ComponentsModule } from '../../components-module';
import { adminGuard } from '../../guards/admin.guard';

const routes: Routes = [
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

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    IonicModule,
    ComponentsModule,
    RouterModule.forChild(routes)
  ],
  declarations: [
    AccountPage,
    ProfileSectionComponent,
    SecuritySectionComponent,
    CredentialsSectionComponent,
    UsersSectionComponent
  ]
})
export class AccountPageModule {}
