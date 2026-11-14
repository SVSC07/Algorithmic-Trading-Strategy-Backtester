import type { Strategy, StrategyParameters, StrategyType } from '../types/api';
import { apiClient, USE_MOCKS } from './http';
import { mockApi } from './mocks';

export async function listStrategies(): Promise<Strategy[]> {
  if (USE_MOCKS) {
    return mockApi.getStrategies();
  }
  return apiClient<Strategy[]>('/api/strategies', {
    method: 'GET',
  });
}

export async function createStrategy(
  strategy_type: StrategyType,
  parameters: StrategyParameters
): Promise<Strategy> {
  if (USE_MOCKS) {
    return mockApi.createStrategy(strategy_type, parameters);
  }
  return apiClient<Strategy>('/api/strategies', {
    method: 'POST',
    body: JSON.stringify({ strategy_type, parameters }),
  });
}
