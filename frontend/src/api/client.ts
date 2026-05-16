import type { AnalysisCreateResponse, AnalysisResult, AnalysisSummary, ReportResponse } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

async function parseError(response: Response): Promise<string> {
  try {
    const payload: unknown = await response.json();
    if (isRecord(payload) && typeof payload.detail === 'string') {
      return payload.detail;
    }
  } catch {
    // Response body is not JSON.
  }
  return `Ошибка API: ${response.status}`;
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${url}`, init);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return (await response.json()) as T;
}

export async function uploadAnalysis(
  file: File,
  materialType: string,
  audienceType: string,
  title?: string,
): Promise<AnalysisCreateResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('material_type', materialType);
  formData.append('audience_type', audienceType);
  if (title?.trim()) {
    formData.append('title', title.trim());
  }

  return requestJson<AnalysisCreateResponse>('/api/analyses', {
    method: 'POST',
    body: formData,
  });
}

export function getAnalyses(): Promise<AnalysisSummary[]> {
  return requestJson<AnalysisSummary[]>('/api/analyses');
}

export function getAnalysis(id: string): Promise<AnalysisResult> {
  return requestJson<AnalysisResult>(`/api/analyses/${id}`);
}

export function getReport(id: string): Promise<ReportResponse> {
  return requestJson<ReportResponse>(`/api/analyses/${id}/report`);
}

export async function downloadReport(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/analyses/${id}/report/download`);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  const blob = await response.blob();
  const href = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = href;
  link.download = 'report.md';
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(href);
}
