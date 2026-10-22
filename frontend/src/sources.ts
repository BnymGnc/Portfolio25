import type {Building,SourceKind} from './types';
export const sourceLabels:Record<SourceKind,string>={measured:'Ölçülmüş',user_estimate:'Kullanıcı tahmini',default:'Varsayılan',synthetic:'Sentetik',unspecified:'Belirtilmemiş'};
export const sourceFields=[['consumption','Tüketimler'],['area','Alan'],['connection','Bağlantı sınırı'],['investment','Yatırım maliyeti'],['boiler','Kazan verimi'],['scop','SCOP'],['insulation','Yalıtım etkisi']] as const;
export function sourceKind(b:Building,key:string):SourceKind{return b.field_sources?.[key]??(b.provenance.kind==='synthetic'?'synthetic':'unspecified')}
