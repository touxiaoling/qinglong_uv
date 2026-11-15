export async function request(path, options = {}) {
  const { body, ...init } = options
  const response = await fetch('/api' + path, {
    ...init,
    cache: 'no-store',
    ...(body === undefined ? {} : {
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const detail = payload?.detail
    const message = Array.isArray(detail)
      ? detail.map(({ loc, msg }) => `${loc.at(-1)}: ${msg}`).join('; ')
      : detail
    throw new Error(message || `Request failed (${response.status}).`)
  }
  return response.status === 204 ? undefined : response.json()
}

export const projectPath = (name) => '/projects/' + encodeURIComponent(name)
export const taskPath = (name) => '/tasks/' + encodeURIComponent(name)
