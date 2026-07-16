import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface ReportSchedule {
  report_schedule: "none" | "daily" | "weekly" | "monthly";
  report_email: string | null;
}

async function fetchReportSchedule(): Promise<ReportSchedule> {
  const { data } = await api.get<ReportSchedule>("/api/settings/report-schedule");
  return data;
}

async function saveReportSchedule(payload: ReportSchedule): Promise<ReportSchedule> {
  const { data } = await api.put<ReportSchedule>("/api/settings/report-schedule", payload);
  return data;
}

async function triggerTestReport(): Promise<{ status: string; message: string }> {
  const { data } = await api.post<{ status: string; message: string }>(
    "/api/settings/report-schedule/trigger-test"
  );
  return data;
}

export function useReportSchedule() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["reportSchedule"],
    queryFn: fetchReportSchedule,
  });

  const saveMutation = useMutation({
    mutationFn: saveReportSchedule,
    onSuccess: (data) => {
      queryClient.setQueryData(["reportSchedule"], data);
    },
  });

  const testMutation = useMutation({
    mutationFn: triggerTestReport,
  });

  return {
    schedule: query.data,
    isLoading: query.isLoading,
    error: query.error,
    save: saveMutation.mutate,
    isSaving: saveMutation.isPending,
    isSaveSuccess: saveMutation.isSuccess,
    saveError: saveMutation.error,
    resetSaveState: saveMutation.reset,
    triggerTest: testMutation.mutate,
    isTesting: testMutation.isPending,
    testSuccess: testMutation.isSuccess,
    testError: testMutation.error,
    testData: testMutation.data,
    resetTestState: testMutation.reset,
  };
}
