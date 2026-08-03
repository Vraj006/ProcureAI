import { apiClient } from "./client";
import { UserResponse } from "./types";

export const usersApi = {
  getMe: async (): Promise<UserResponse> => {
    // Requirements split GET /api/v1/users/me implicitly, but auth.py has it at /auth/me for this backend.
    const response = await apiClient.get<UserResponse>("/auth/me");
    return response.data;
  },
};
