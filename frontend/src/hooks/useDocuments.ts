import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deleteDocument, listDocuments, uploadDocument } from '../services/documentsService';
import { errorMessage } from '../services/authService';

export function useDocuments() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: listDocuments,
  });

  const uploadMutation = useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  return {
    documents: data ?? [],
    isLoading,
    uploadDocument: uploadMutation.mutate,
    isUploading: uploadMutation.isPending,
    // Server messages like "No text could be extracted" or "File is larger than 10 MB".
    uploadError: uploadMutation.error ? errorMessage(uploadMutation.error, 'Upload failed.') : null,
    deleteDocument: deleteMutation.mutate,
  };
}
