import type { Instrument, ImportPricesResponse } from '../types/api';
import { apiClient, USE_MOCKS } from './http';
import { mockApi } from './mocks';

export async function listInstruments(): Promise<Instrument[]> {
  if (USE_MOCKS) {
    return mockApi.getInstruments();
  }
  return apiClient<Instrument[]>('/api/instruments', {
    method: 'GET',
  });
}

export async function createInstrument(
  ticker: string,
  name: string,
  asset_class: string
): Promise<Instrument> {
  if (USE_MOCKS) {
    return mockApi.createInstrument(ticker, name, asset_class);
  }
  return apiClient<Instrument>('/api/instruments', {
    method: 'POST',
    body: JSON.stringify({ ticker, name, asset_class }),
  });
}

export async function updateInstrument(
  id: number,
  ticker: string,
  name: string,
  asset_class: string
): Promise<Instrument> {
  if (USE_MOCKS) {
    return mockApi.updateInstrument(id, ticker, name, asset_class);
  }
  return apiClient<Instrument>(`/api/instruments/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ ticker, name, asset_class }),
  });
}

export async function deleteInstrument(id: number): Promise<void> {
  if (USE_MOCKS) {
    return mockApi.deleteInstrument(id);
  }
  return apiClient<void>(`/api/instruments/${id}`, {
    method: 'DELETE',
  });
}

export async function importPrices(
  id: number,
  file: File
): Promise<ImportPricesResponse> {
  if (USE_MOCKS) {
    return mockApi.importPrices(id, file);
  }
  const formData = new FormData();
  formData.append('file', file);

  return apiClient<ImportPricesResponse>(`/api/instruments/${id}/prices`, {
    method: 'POST',
    body: formData,
  });
}
