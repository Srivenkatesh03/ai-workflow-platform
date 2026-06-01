export type AuthUser = {
  id: string;
  name: string;
  email: string;
  role: string;
};

export type AuthTokens = {
  access_token: string;
  refresh_token: string;
  user: AuthUser;
};

export type ApiResponse<T> = {
  success: boolean;
  message: string;
  data: T;
};

