import {errorMessage} from './format.ts';

export function aiErrorMessage(error: unknown): string {
 const message=errorMessage(error);
 if(/kota|kredi|faturalama|quota|credit/i.test(message))return 'AI hizmetinin kullanım limiti dolmuş. Şu anda yanıt alınamıyor; hesaplanan planınız kullanılabilir.';
 if(/anahtar|yapılandırılmamış/i.test(message))return 'AI asistanı şu anda kullanılamıyor. Hesaplanan planınız kullanılabilir.';
 if(/zaman aşımı|bağlanılamadı|okunamadı|fetch|network/i.test(message))return 'AI hizmetinden yanıt alınamadı. Biraz sonra yeniden deneyin; planınız korunuyor.';
 if(/kaynak alanı|sayısal iddia|şema|doğrulanamadı|doğrulamasını/i.test(message))return 'AI yanıtı hesapla doğrulanamadığı için gösterilmedi. Yeniden deneyebilirsiniz.';
 return message;
}

// Recognize application failures; never echo arbitrary gateway/provider payloads.
export function aiServiceFailure(body: Record<string,unknown>): string {
 const detail=body.detail;
 if(typeof detail==='string'&&detail.length<1000&&/^(LLM|AI) /.test(detail)&&/kota|kredi|anahtar|yapılandırılmamış|zaman aşımı|bağlanılamadı|doğrulanamadı|doğrulamasını/.test(detail))return aiErrorMessage(new Error(detail));
 return 'AI hizmetinden yanıt alınamadı. Biraz sonra yeniden deneyin; planınız korunuyor.';
}
