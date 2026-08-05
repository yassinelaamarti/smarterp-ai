import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface AIRecommendation {
  id: string;
  tenantId?: string;
  sourceType: "anomaly" | "health_score" | "kpi_alert";
  sourceId: string;
  title: string;
  explanation: string;
  actionType: "restock_order" | "send_email_campaign" | "create_crm_activity" | "none";
  actionPayload?: Record<string, any>;
  estimatedImpact?: {
    label: string;
    confidence: "low" | "medium" | "high";
  };
  status: "pending" | "executed" | "dismissed" | "failed" | "acknowledged";
  executedBy?: number;
  executedAt?: string;
  createdAt: string;
  expiresAt?: string;
}

export interface AIRecommendationAudit {
  id: string;
  recommendationId: string;
  sourceType: string;
  title: string;
  actionType: string;
  actionPayload?: Record<string, any>;
  odooResult?: Record<string, any>;
  estimatedImpact?: {
    label: string;
    confidence: "low" | "medium" | "high";
  };
  status: string;
  executedByName?: string;
  executedAt?: string;
  createdAt: string;
  success?: boolean | null;
  errorMessage?: string;
}

interface RecommendationApiResponse {
  id: string;
  tenant_id?: string;
  source_type: "anomaly" | "health_score" | "kpi_alert";
  source_id: string;
  title: string;
  explanation: string;
  action_type: "restock_order" | "send_email_campaign" | "create_crm_activity" | "none";
  action_payload?: Record<string, any>;
  estimated_impact?: {
    label: string;
    confidence: "low" | "medium" | "high";
  };
  status: "pending" | "executed" | "dismissed" | "failed" | "acknowledged";
  executed_by?: number;
  executed_at?: string;
  created_at: string;
  expires_at?: string;
}

interface AuditApiResponse {
  id: string;
  recommendation_id: string;
  source_type: string;
  title: string;
  action_type: string;
  action_payload?: Record<string, any>;
  odoo_result?: Record<string, any>;
  estimated_impact?: {
    label: string;
    confidence: "low" | "medium" | "high";
  };
  status: string;
  executed_by_name?: string;
  executed_at?: string;
  created_at: string;
  success?: boolean | null;
  error_message?: string;
}

async function fetchRecommendations(): Promise<AIRecommendation[]> {
  const { data } = await api.get<RecommendationApiResponse[]>("/api/recommendations/");
  return data.map((r) => ({
    id: r.id,
    tenantId: r.tenant_id,
    sourceType: r.source_type,
    sourceId: r.source_id,
    title: r.title,
    explanation: r.explanation,
    actionType: r.action_type,
    actionPayload: r.action_payload,
    estimatedImpact: r.estimated_impact,
    status: r.status,
    executedBy: r.executed_by,
    executedAt: r.executed_at,
    createdAt: r.created_at,
    expiresAt: r.expires_at,
  }));
}

async function fetchAudit(): Promise<AIRecommendationAudit[]> {
  const { data } = await api.get<AuditApiResponse[]>("/api/recommendations/audit");
  return data.map((r) => ({
    id: r.id,
    recommendationId: r.recommendation_id,
    sourceType: r.source_type,
    title: r.title,
    actionType: r.action_type,
    actionPayload: r.action_payload,
    odooResult: r.odoo_result,
    estimatedImpact: r.estimated_impact,
    status: r.status,
    executedByName: r.executed_by_name,
    executedAt: r.executed_at,
    createdAt: r.created_at,
    success: r.success,
    errorMessage: r.error_message,
  }));
}

async function executeRecommendation(id: string): Promise<any> {
  const { data } = await api.post(`/api/recommendations/${id}/execute`);
  return data;
}

async function dismissRecommendation(id: string): Promise<any> {
  const { data } = await api.post(`/api/recommendations/${id}/dismiss`);
  return data;
}

async function acknowledgeRecommendation(id: string): Promise<any> {
  const { data } = await api.post(`/api/recommendations/${id}/acknowledge`);
  return data;
}

export function useRecommendations() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["recommendations"],
    queryFn: fetchRecommendations,
    refetchInterval: 30_000,
  });

  const executeMutation = useMutation({
    mutationFn: executeRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["recommendationsAudit"] });
    },
  });

  const dismissMutation = useMutation({
    mutationFn: dismissRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["recommendationsAudit"] });
    },
  });

  const acknowledgeMutation = useMutation({
    mutationFn: acknowledgeRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["recommendationsAudit"] });
    },
  });

  return {
    recommendations: query.data,
    isLoading: query.isLoading,
    error: query.error,
    execute: executeMutation.mutate,
    isExecuting: executeMutation.isPending,
    executeError: executeMutation.error,
    dismiss: dismissMutation.mutate,
    isDismissing: dismissMutation.isPending,
    acknowledge: acknowledgeMutation.mutate,
    isAcknowledging: acknowledgeMutation.isPending,
  };
}


export function useRecommendationsAudit() {
  return useQuery({
    queryKey: ["recommendationsAudit"],
    queryFn: fetchAudit,
    refetchInterval: 60_000,
  });
}
