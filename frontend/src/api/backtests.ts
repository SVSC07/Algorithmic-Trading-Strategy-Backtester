import type { RunSummary, RunDetail, CompareRunsResponse } from '../types/api';
import { apiClient, USE_MOCKS } from './http';
import { mockApi } from './mocks';

export async function listBacktests(): Promise<RunSummary[]> {
  if (USE_MOCKS) {
    return mockApi.getBacktests();
  }
  return apiClient<RunSummary[]>('/api/backtests', {
    method: 'GET',
  });
}

export async function getBacktest(id: number): Promise<RunDetail> {
  if (USE_MOCKS) {
    return mockApi.getBacktest(id);
  }
  return apiClient<RunDetail>(`/api/backtests/${id}`, {
    method: 'GET',
  });
}

export async function createBacktest(
  strategy_id: number,
  instrument_id: number,
  start_date: string,
  end_date: string
): Promise<{ run_id: number; status: 'COMPLETED' }> {
  if (USE_MOCKS) {
    return mockApi.createBacktest(strategy_id, instrument_id, start_date, end_date);
  }
  return apiClient<{ run_id: number; status: 'COMPLETED' }>('/api/backtests', {
    method: 'POST',
    body: JSON.stringify({ strategy_id, instrument_id, start_date, end_date }),
  });
}

export async function compareBacktests(
  runA: number,
  runB: number
): Promise<CompareRunsResponse> {
  if (USE_MOCKS) {
    return mockApi.compareBacktests(runA, runB);
  }
  return apiClient<CompareRunsResponse>(`/api/backtests/compare?runA=${runA}&runB=${runB}`, {
    method: 'GET',
  });
}
