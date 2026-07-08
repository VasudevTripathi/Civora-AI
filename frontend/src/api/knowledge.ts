import { apiFetch } from './client';

export interface KnowledgeObject {
  id: string;
  type: string;
  jurisdiction: string;
  authority: string;
  title: string;
  description: string;
  effective_date: string;
  expiry_date?: string | null;
  version: string;
  source: string;
  tags: string[];
  metadata: Record<string, any>;
}

export async function getBusinesses(): Promise<KnowledgeObject[]> {
  return apiFetch<KnowledgeObject[]>('/knowledge/businesses');
}

export async function getLicenses(): Promise<KnowledgeObject[]> {
  return apiFetch<KnowledgeObject[]>('/knowledge/licenses');
}

export async function getAuthorities(): Promise<KnowledgeObject[]> {
  return apiFetch<KnowledgeObject[]>('/knowledge/authorities');
}
