import { create } from "zustand";
import { persist } from "zustand/middleware";
import { User, Repository, Installation, Task } from "@/types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      setAuth: (user, token) => set({ user, accessToken: token, isAuthenticated: true }),
      clearAuth: () => set({ user: null, accessToken: null, isAuthenticated: false }),
    }),
    {
      name: "devpilot-auth",
      partialize: (state) => ({ user: state.user, accessToken: state.accessToken, isAuthenticated: state.isAuthenticated }),
    }
  )
);

interface UIState {
  sidebarOpen: boolean;
  theme: "light" | "dark" | "system";
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  setTheme: (theme: "light" | "dark" | "system") => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: "system",
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: "devpilot-ui",
    }
  )
);

interface RepositoryState {
  selectedRepository: Repository | null;
  selectedInstallation: Installation | null;
  setSelectedRepository: (repo: Repository | null) => void;
  setSelectedInstallation: (installation: Installation | null) => void;
}

export const useRepositoryStore = create<RepositoryState>((set) => ({
  selectedRepository: null,
  selectedInstallation: null,
  setSelectedRepository: (repo) => set({ selectedRepository: repo }),
  setSelectedInstallation: (installation) => set({ selectedInstallation: installation }),
}));

interface TaskState {
  selectedTask: Task | null;
  taskFilters: {
    status?: string;
    type?: string;
    repository_id?: number;
  };
  setSelectedTask: (task: Task | null) => void;
  setTaskFilters: (filters: Partial<TaskState["taskFilters"]>) => void;
  clearTaskFilters: () => void;
}

export const useTaskStore = create<TaskState>((set) => ({
  selectedTask: null,
  taskFilters: {},
  setSelectedTask: (task) => set({ selectedTask: task }),
  setTaskFilters: (filters) => set((state) => ({ taskFilters: { ...state.taskFilters, ...filters } })),
  clearTaskFilters: () => set({ taskFilters: {} }),
}));

interface NotificationState {
  notifications: Array<{
    id: string;
    type: "success" | "error" | "warning" | "info";
    title: string;
    message?: string;
    duration?: number;
  }>;
  addNotification: (notification: Omit<NotificationState["notifications"][0], "id">) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        { ...notification, id: Math.random().toString(36).slice(2) },
      ],
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
  clearNotifications: () => set({ notifications: [] }),
}));