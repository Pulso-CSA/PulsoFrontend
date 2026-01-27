import { useState, useEffect } from 'react';
import { Subscription, Invoice, PlanType, BillingCycle } from '@/types';
import { useAuth } from '@/contexts/AuthContext';
import { subscriptionApi } from '@/lib/api';

export function useSubscription() {
  const { isAuthenticated } = useAuth();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSubscription = async () => {
    if (!isAuthenticated) return;

    try {
      setIsLoading(true);
      setError(null);
      const data = await subscriptionApi.get();
      setSubscription(data.subscription);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar assinatura');
      setSubscription(null);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchInvoices = async () => {
    if (!isAuthenticated) return;

    try {
      const data = await subscriptionApi.getInvoices();
      setInvoices(data.invoices || []);
    } catch {
      setInvoices([]);
    }
  };

  // Only fetch when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchSubscription();
      fetchInvoices();
    } else {
      // Clear data when not authenticated
      setSubscription(null);
      setInvoices([]);
    }
  }, [isAuthenticated]);

  const cancelSubscription = async (immediately: boolean = false) => {
    const data = await subscriptionApi.cancel(immediately);
    setSubscription(data.subscription);
    return data.subscription;
  };

  const resumeSubscription = async () => {
    const data = await subscriptionApi.resume();
    setSubscription(data.subscription);
    return data.subscription;
  };

  const changePlan = async (planId: PlanType, billingCycle: BillingCycle) => {
    const data = await subscriptionApi.changePlan(planId, billingCycle);
    setSubscription(data.subscription);
    return data.subscription;
  };

  const getCustomerPortalUrl = async (): Promise<string> => {
    const data = await subscriptionApi.getPortalUrl();
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
