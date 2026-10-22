import {readJsonObject, ServiceError, unavailable} from './http.ts';
import {OriginRejectedError} from './deployment.ts';

export interface User {id: string; email: string; onboarding_version: number}
export interface StorageStatus {status:'local'|'postgresql'|'unavailable'|'persistent_disk'|'ephemeral'|'unverified';required:boolean;message:string}
export interface AuthReply {user?: User | null; csrf?: string; completed?: boolean; version?: number;storage?:StorageStatus}
export class LoginRejectedError extends Error {}
export type AuthPath = 'session' | 'login' | 'register' | 'logout' | 'onboarding';

export async function requestAuth(base: string, path: AuthPath, body: unknown, csrf: string,
                                  fetcher: typeof fetch = fetch): Promise<AuthReply> {
  let response: Response;
  const read = body === undefined;
  try {
    response = await fetcher(base + '/api/auth/' + path, {
      credentials: 'include', method: read ? 'GET' : 'POST',
      headers: {'Content-Type': 'application/json', ...(read ? {} : {'X-CSRF-Token': csrf})},
      body: read ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(read ? 65000 : 45000),
    });
  } catch {
    throw read ? unavailable() : new ServiceError('İsteğin sonucu doğrulanamadı. Biraz bekleyip bağlantıyı yeniden deneyin. Kayıt oluşturduysanız giriş yapmayı deneyin.');
  }
  const value = await readJsonObject(response);
  if (!response.ok) {
    if (response.status === 503 && value.error && typeof value.error === 'object' &&
        'code' in value.error && value.error.code === 'database_unavailable')
      throw new ServiceError('Kalıcı veritabanına erişilemiyor. İşlem kaydedilmedi veya sonucu doğrulanamadı; bağlantı düzeldiğinde kaydı kontrol edin.',503);
    if (response.status >= 500) throw unavailable(response.status);
    const detail = typeof value.detail === 'string' ? value.detail.slice(0, 400) : null;
    if (response.status === 403 && detail?.startsWith('İstek kaynağı izinli değil.')) throw new OriginRejectedError();
    if (response.status === 401 && path === 'login') throw new LoginRejectedError('E-posta veya parola geçersiz.');
    const fallback = response.status === 429 ? 'Çok sayıda deneme yapıldı. Biraz bekleyip tekrar deneyin.'
      : response.status === 422 ? 'E-posta ve parola biçimini kontrol edin. Kayıt parolası en az 12 karakter olmalı.'
      : 'Oturum işlemi tamamlanamadı. Girdileri kontrol edin.';
    throw new Error(detail || fallback);
  }
  if (path === 'onboarding') {
    if (value.completed !== true) throw unavailable(response.status);
    return {completed: true};
  }
  const user = value.user;
  if (typeof value.csrf !== 'string' || !value.csrf || !(user === null ||
      (typeof user === 'object' && user !== null && 'id' in user && typeof user.id === 'string' &&
       'email' in user && typeof user.email === 'string' && 'onboarding_version' in user &&
       typeof user.onboarding_version === 'number'))) throw unavailable(response.status);
  if ((path === 'login' || path === 'register') && user === null) throw unavailable(response.status);
  const raw=value.storage;
  let storage:StorageStatus|undefined;
  if(raw&&typeof raw==='object'&&'status' in raw&&['local','postgresql','unavailable','persistent_disk','ephemeral','unverified'].includes(String(raw.status))&&
     'required' in raw&&typeof raw.required==='boolean'&&'message' in raw&&typeof raw.message==='string')
    storage=raw as StorageStatus;
  return {csrf: value.csrf, user: user as User | null,storage};
}
