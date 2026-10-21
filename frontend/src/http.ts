export class ServiceError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ServiceError';
    this.status = status;
  }
}

export function unavailable(status?: number) {
  return new ServiceError(`Sunucu şu anda yanıt veremiyor${status ? ` (${status})` : ''}. Sunucu uyanıyor veya geçici bir bağlantı sorunu yaşıyor olabilir. Biraz bekleyip tekrar deneyin.`, status);
}

export function hasJsonContent(response: Response) {
  const type = (response.headers.get('content-type') ?? '').split(';')[0].trim().toLowerCase();
  return type === 'application/json' || type.endsWith('+json');
}

// Never display a proxy's HTML, raw response body or JSON parser exception.
export async function readJsonObject(response: Response): Promise<Record<string, unknown>> {
  if (!hasJsonContent(response)) throw unavailable(response.status);
  let value: unknown;
  try { value = await response.json(); } catch { throw unavailable(response.status); }
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw unavailable(response.status);
  return value as Record<string, unknown>;
}

export function safeError(error: unknown) {
  if (error instanceof SyntaxError) return unavailable().message;
  return error instanceof Error ? error.message : 'İşlem tamamlanamadı. Lütfen tekrar deneyin.';
}
