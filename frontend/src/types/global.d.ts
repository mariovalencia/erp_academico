// src/types/global.d.ts
export {};

declare global {
  interface Window {
    google: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: {
              credential: string;
              select_by?: string;
            }) => void;
            auto_select?: boolean;
            login_uri?: string;
            native_callback?: () => void;
            cancel_on_tap_outside?: boolean;
            prompt_parent_id?: string;
            nonce?: string;
            context?: string;
            state_cookie_domain?: string;
            ux_mode?: 'popup' | 'redirect';
            allowed_parent_origin?: string | string[];
            intermediate_iframe_close_callback?: () => void;
            itp_support?: boolean;
          }) => void;
          prompt: (callback?: (notification: {
            isNotDisplayed: boolean;
            isSkippedMoment: boolean;
            getNotDisplayedReason: () => string;
            getSkippedReason: () => string;
            getMomentType: () => string;
          }) => void) => void;
          renderButton: (
            parent: HTMLElement, 
            options: {
              type?: 'standard' | 'icon';
              theme?: 'outline' | 'filled_blue' | 'filled_black';
              size?: 'large' | 'medium' | 'small';
              text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin';
              shape?: 'rectangular' | 'pill' | 'circle' | 'square';
              logo_alignment?: 'left' | 'center';
              width?: number | string;
              locale?: string;
            }
          ) => void;
          disableAutoSelect: () => void;
          storeCredential: (credential: { id: string; password: string }) => void;
          cancel: () => void;
          revoke: (hint: string, callback?: (response: { successful: boolean; error: string }) => void) => void;
        };
      };
    };
  }
}