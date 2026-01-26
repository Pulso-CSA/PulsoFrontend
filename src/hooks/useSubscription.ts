import { useState, useEffect } from 'react';
import { Subscription, Invoice, PlanType, BillingCycle } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

function getStoredToken(): string | null {
  return sessionStorage.getItem('authToken');
}

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = getStoredToken();
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Erro desconhecido' }));
    throw new Error(error.message || 'Erro na requisição');
  }
  
  return response.json();
}

export function useSubscription() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSubscription = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchWithAuth(`${API_BASE_URL}/subscription`);
      setSubscription(data.subscription);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar assinatura');
      setSubscription(null);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchInvoices = async () => {
    try {
      const data = await fetchWithAuth(`${API_BASE_URL}/subscription/invoices`);
      setInvoices(data.invoices || []);
    } catch (err) {
      console.error('Failed to fetch invoices:', err);
      setInvoices([]);
    }
  };

  useEffect(() => {
    fetchSubscription();
    fetchInvoices();
  }, []);

  const cancelSubscription = async (immediately: boolean = false) => {
    const data = await fetchWithAuth(`${API_BASE_URL}/subscription/cancel`, {
      method: 'POST',
      body: JSON.stringify({ immediately }),
    });
    setSubscription(data.subscription);
    return data.subscription;
  };

  const resumeSubscription = async () => {
    const data = await fetchWithAuth(`${API_BASE_URL}/subscription/resume`, {
      method: 'POST',
    });
    setSubscription(data.subscription);
    return data.subscription;
  };

  const changePlan = async (planId: PlanType, billingCycle: BillingCycle) => {
    const data = await fetchWithAuth(`${API_BASE_URL}/subscription/change-plan`, {
      method: 'POST',
      body: JSON.stringify({ planId, billingCycle }),
    });
    setSubscription(data.subscription);
    return data.subscription;
  };

  const getCustomerPortalUrl = async (): Promise<string> => {
    const data = await fetchWithAuth(`${API_BASE_URL}/subscription/portal`);
    return data.url;
  };

  const refresh = async () => {
    await Promise.all([fetchSubscription(), fetchInvoices()]);
  };

  return {
    subscription,
    invoices,
    isLoading,
    error,
    cancelSubscription,
    resumeSubscription,
    changePlan,
    getCustomerPortalUrl,
    refresh,
  };
}
