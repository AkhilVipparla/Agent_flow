import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deleteReportById, listReports } from '../services/reportsService';

export function useReports() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: listReports,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteReportById,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
  });

  return {
    reports: data?.reports ?? [],
    total: data?.total ?? 0,
    isLoading,
    deleteReport: deleteMutation.mutate,
  };
}
