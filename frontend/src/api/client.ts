/**
 * API Client for On-Premise LLM & RAG System
 */

const API_BASE_URL = '/api/v1';

interface LoginResponse {
  access_token: string;
  token_type: string;
}

interface UserInfo {
  user_id: string;
  username: string;
  security_level: number;
  security_level_name: string;
  department: string;
  roles: string[];
  accessible_levels: number[];
}

interface QueryRequest {
  query: string;
  top_k?: number;
  stream?: boolean;
  include_sources?: boolean;
}

interface Source {
  title: string;
  security_level: number;
  score: number;
  source_path?: string;
}

interface SearchResult {
  documents: Array<{
    id: string;
    content: string;
    security_level: number;
    source_path: string;
    document_title: string;
    score: number;
  }>;
  total_found: number;
  user_security_level: number;
}

interface QueueStatus {
  queue: {
    queued: number;
    processing: number;
    max_size: number;
  };
  active_requests: number;
  max_concurrent: number;
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('auth_token');
    }
    return this.token;
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  async login(username: string, password: string): Promise<LoginResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data: LoginResponse = await response.json();
    this.setToken(data.access_token);
    return data;
  }

  async getUserInfo(): Promise<UserInfo> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.setToken(null);
      }
      throw new Error('Failed to get user info');
    }

    return response.json();
  }

  logout() {
    this.setToken(null);
  }

  async *queryStream(request: QueryRequest): AsyncGenerator<{ type: string; content?: string; documents?: Source[] }> {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        ...request,
        stream: true,
      }),
    });

    if (!response.ok) {
      throw new Error(`Query failed: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            return;
          }
          try {
            const parsed = JSON.parse(data);
            yield parsed;
          } catch {
            // Skip invalid JSON
          }
        }
      }
    }
  }

  async search(query: string, topK: number = 10): Promise<SearchResult> {
    const response = await fetch(`${API_BASE_URL}/search`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ query, top_k: topK }),
    });

    if (!response.ok) {
      throw new Error('Search failed');
    }

    return response.json();
  }

  async getQueueStatus(): Promise<QueueStatus> {
    const response = await fetch(`${API_BASE_URL}/queue/status`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to get queue status');
    }

    return response.json();
  }
}

export const apiClient = new ApiClient();
export type { LoginResponse, UserInfo, QueryRequest, Source, SearchResult, QueueStatus };
