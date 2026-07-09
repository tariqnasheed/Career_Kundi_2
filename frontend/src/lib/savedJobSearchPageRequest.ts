import type {
  SavedJobRead,
} from "../types/api";


export interface SavedJobSearchPageParams {
  q?: string;
  location?: string;
  employment_type?: string;
  remote?: boolean;
  page?: number;
  page_size?: number;
}


export interface SavedJobSearchPageRead {
  items: SavedJobRead[];
  page: number;
  page_size: number;
  has_next: boolean;
}


export interface SavedJobSearchPageRequest {
  url: "/job-search/search/page";
  params: SavedJobSearchPageParams;
}


export function buildSavedJobSearchPageRequest(
  params: SavedJobSearchPageParams,
): SavedJobSearchPageRequest {
  return {
    url: "/job-search/search/page",
    params: {
      ...params,
    },
  };
}
