import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, FormGroup, Validators, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { AlertController, LoadingController, ToastController, IonButton, IonIcon, IonInput, IonInputPasswordToggle } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { addOutline, checkmarkOutline, closeOutline, createOutline, keyOutline, trashOutline } from 'ionicons/icons';
import { firstValueFrom } from 'rxjs';
import { AuthService } from '../../../services/auth.service';
import { User } from '../../../models/auth.models';

/**
 * Account page section: credentials of the current user
 * The credentials authenticate machine-to-machine calls with HTTP headers
 */
@Component({
    selector: 'app-credentials-section',
    templateUrl: './credentials-section.component.html',
    styleUrls: ['./credentials-section.component.scss'],
    imports: [FormsModule, ReactiveFormsModule, IonButton, IonIcon, IonInput, IonInputPasswordToggle]
})
export class CredentialsSectionComponent implements OnInit {
  private readonly formBuilder = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly toastController = inject(ToastController);
  private readonly alertController = inject(AlertController);
  private readonly loadingController = inject(LoadingController);

  private readonly destroyRef = inject(DestroyRef);
  user: User | null = null;
  credentialForm!: FormGroup;
  editCredentialForm!: FormGroup;
  editingCredential: string | null = null;
  loading = false;

  constructor() {
    addIcons({ addOutline, checkmarkOutline, closeOutline, createOutline, keyOutline, trashOutline });
  }

  ngOnInit() {
    this.authService.currentUser$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(user => {
        this.user = user;
      });

    this.credentialForm = this.formBuilder.group({
      credentialKey: ['', [Validators.required]],
      credentialValue: ['', [Validators.required]]
    });

    this.editCredentialForm = this.formBuilder.group({
      credentialValueEdit: ['', [Validators.required]]
    });
  }

  /**
   * Get user credentials as key-value pairs
   */
  getCredentials(): Array<{key: string, value: string}> {
    if (!this.user?.config?.credentials) return [];
    return Object.entries(this.user.config.credentials).map(([key, value]) => ({key, value}));
  }

  /**
   * Add new credential
   */
  async addCredential() {
    if (this.credentialForm.invalid) {
      this.credentialForm.markAllAsTouched();
      return;
    }

    const { credentialKey, credentialValue } = this.credentialForm.value;

    if (!this.user?.config) {
      await this.showToast('User config not available', 'danger');
      return;
    }

    if (this.user.config.credentials?.[credentialKey] !== undefined) {
      await this.showToast('Credential key already exists', 'warning');
      return;
    }

    const saved = await this.saveCredentials(
      { ...this.user.config.credentials, [credentialKey]: credentialValue },
      'Adding credential...',
      'Credential added successfully',
      'Failed to add credential'
    );
    if (saved) {
      this.credentialForm.reset();
    }
  }

  /**
   * Start editing a credential
   */
  startEditCredential(key: string) {
    this.editingCredential = key;
    this.editCredentialForm.reset();
    this.editCredentialForm.get('credentialValueEdit')?.setValue(this.user?.config?.credentials?.[key] || '');
  }

  /**
   * Cancel editing credential
   */
  cancelEditCredential() {
    this.editingCredential = null;
    this.editCredentialForm.reset();
  }

  /**
   * Save edited credential
   */
  async saveEditedCredential() {
    if (this.editCredentialForm.invalid) {
      this.editCredentialForm.markAllAsTouched();
      return;
    }

    if (!this.editingCredential) {
      await this.showToast('No credential selected for editing', 'warning');
      return;
    }

    if (!this.user?.config?.credentials) {
      await this.showToast('User config not available', 'danger');
      return;
    }

    const { credentialValueEdit } = this.editCredentialForm.value;
    await this.saveCredentials(
      { ...this.user.config.credentials, [this.editingCredential]: credentialValueEdit },
      'Updating credential...',
      'Credential updated successfully',
      'Failed to update credential'
    );
    this.cancelEditCredential();
  }

  /**
   * Delete credential
   */
  async deleteCredential(key: string) {
    const alert = await this.alertController.create({
      header: 'Delete Credential',
      message: `Are you sure you want to delete the credential "${key}"?`,
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel'
        },
        {
          text: 'Delete',
          role: 'destructive',
          handler: async () => {
            if (!this.user?.config?.credentials) {
              await this.showToast('User config not available', 'danger');
              return;
            }

            const { [key]: _deleted, ...credentials } = this.user.config.credentials;
            await this.saveCredentials(
              credentials,
              'Deleting credential...',
              'Credential deleted successfully',
              'Failed to delete credential'
            );
          }
        }
      ]
    });

    await alert.present();
  }

  /**
   * Replace the credentials of the current user, resolves to true once saved
   */
  private async saveCredentials(credentials: { [key: string]: string }, loadingMessage: string, successMessage: string, errorMessage: string): Promise<boolean> {
    const loading = await this.loadingController.create({
      message: loadingMessage,
    });
    await loading.present();
    this.loading = true;

    // PUT /auth/me updates the current user and refreshes it in the AuthService
    const failure = await firstValueFrom(this.authService.updateProfile({ config: { ...this.user.config, credentials } }))
      .then(() => null, (error: Error) => error);

    await loading.dismiss();
    this.loading = false;

    if (failure) {
      await this.showToast(`${errorMessage}: ${failure.message}`, 'danger');
      return false;
    }

    await this.showToast(successMessage, 'success');
    return true;
  }

  /**
   * Show toast message
   */
  private async showToast(message: string, color: string = 'primary') {
    const toast = await this.toastController.create({
      message,
      duration: 3000,
      color,
      position: 'top'
    });
    await toast.present();
  }
}
