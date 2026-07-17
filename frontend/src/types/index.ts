export interface KPISourceData {
  model: string;
  domain: string;
  formula: string;
}

export interface KPI {
  id: string;
  label: string;
  value: number;
  unit?: string;
  trend?: "up" | "down" | "stable";
  changePercent?: number;
  sourceData?: KPISourceData;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
}