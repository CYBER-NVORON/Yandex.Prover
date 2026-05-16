import { useEffect, useState } from 'react';
import type { AnalysisResult, AnalysisSummary, UploadAnalysisPayload } from './api/types';
import { getAnalyses, getAnalysis, uploadAnalysis } from './api/client';
import { AnalysisDashboard } from './components/AnalysisDashboard';
import { ErrorState } from './components/ErrorState';
import { Hero } from './components/Hero';
import { Layout } from './components/Layout';
import { LoadingState } from './components/LoadingState';
import { UploadPanel } from './components/UploadPanel';

export default function App() {
  const [history, setHistory] = useState<AnalysisSummary[]>([]);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refreshHistory() {
    try {
      setHistory(await getAnalyses());
    } catch {
      setHistory([]);
    }
  }

  useEffect(() => {
    void refreshHistory();
  }, []);

  async function handleUpload(payload: UploadAnalysisPayload) {
    setLoading(true);
    setError(null);
    try {
      const response = await uploadAnalysis(payload);
      setResult(response.result);
      await refreshHistory();
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : 'Не удалось выполнить анализ.');
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectHistory(id: string) {
    setLoading(true);
    setError(null);
    try {
      setResult(await getAnalysis(id));
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : 'Не удалось открыть анализ.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout history={history} selectedId={result?.id} onSelectHistory={handleSelectHistory}>
      <div className="space-y-7">
        <Hero />
        {error ? <ErrorState message={error} onDismiss={() => setError(null)} /> : null}
        {loading ? <LoadingState /> : null}
        {!loading ? <UploadPanel disabled={loading} onSubmit={handleUpload} /> : null}
        {result && !loading ? <AnalysisDashboard result={result} /> : null}
      </div>
    </Layout>
  );
}
