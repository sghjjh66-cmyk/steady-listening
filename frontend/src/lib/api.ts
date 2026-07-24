const API_URL = process.env.NEXT_PUBLIC_API_URL;
const APP_KEY = process.env.NEXT_PUBLIC_APP_KEY;

// 백엔드가 요구하는 공유 비밀 헤더(X-App-Key)를 모든 요청에 자동으로 붙여준다.
export function apiFetch(path: string, options: RequestInit = {}) {
  return fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      "X-App-Key": APP_KEY ?? "",
    },
  });
}
