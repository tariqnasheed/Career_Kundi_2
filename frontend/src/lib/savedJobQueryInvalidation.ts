export interface SavedJobQueryInvalidator {
  invalidateQueries: (
    filters: {
      queryKey: readonly unknown[];
    },
  ) => Promise<unknown>;
}

export async function invalidateSavedJobQueries(
  queryClient: SavedJobQueryInvalidator,
): Promise<void> {
  await Promise.all([
    queryClient.invalidateQueries({
      queryKey: ["jobs"],
    }),
    queryClient.invalidateQueries({
      queryKey: ["jobs-search"],
    }),
  ]);
}
