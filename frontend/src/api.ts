export async function api<T = any>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch('/api' + path, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })
  if (!res.ok) {
    const raw = await res.text()
    let msg = raw || res.statusText
    try {
      const body = JSON.parse(raw)
      if (body?.detail) msg = body.detail
    } catch { /* keep raw text */ }
    throw new Error(msg)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}
