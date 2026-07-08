const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ApiErrorDetails {
  message: string;
  status: number;
  details?: any;
}

export class ApiError extends Error {
  status: number;
  details?: any;

  constructor({ message, status, details }: ApiErrorDetails) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${path.startsWith('/') ? '' : '/'}${path}`;
  
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);
    
    let responseData: any;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      responseData = await response.json();
    } else {
      responseData = await response.text();
    }

    if (!response.ok) {
      // Try to extract error message from standard FastAPI / Pydantic validation error or custom exceptions
      const errorMessage = responseData?.detail || responseData?.message || `Request failed with status ${response.status}`;
      throw new ApiError({
        message: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
        status: response.status,
        details: responseData,
      });
    }

    return responseData as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    
    // Network or other fetch errors
    throw new ApiError({
      message: error instanceof Error ? error.message : 'Network error or backend is unreachable',
      status: 0,
      details: error,
    });
  }
}
