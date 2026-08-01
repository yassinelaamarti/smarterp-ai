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
  sampleSize?: number;
  sampleWarningThreshold?: number;
  sampleUnitLabel?: string;
  criticality?: "normal" | "attention" | "critical";
  isSnapshot?: boolean;
}



export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
}