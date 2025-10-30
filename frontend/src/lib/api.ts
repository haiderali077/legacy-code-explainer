const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface Commit {
  id: string;
  sha: string;
  message: string;
  author_name: string;
  author_email: string;
  commit_date: string;
  html_url: string;
  files_changed: string[];
  additions: number;
  deletions: number;
  ai_summary?: string;
  analysis_status?: string;
}

export interface Repository {
  id: string;
  full_name: string;
  owner: string;
  repo_name: string;
  html_url: string;
  analysis_status: string;
  total_commits: number;
  analyzed_commits: number;
}

export async function fetchCommits(repoId: string, token: string): Promise<Commit[]> {
  const response = await fetch(`${API_BASE}/api/repositories/${repoId}/commits`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch commits: ${response.status}`);
  }

  const data = await response.json();
  return data.commits || [];
}

export async function fetchRepositoryStatus(repoId: string, token: string): Promise<Repository> {
  const response = await fetch(`${API_BASE}/api/repositories/${repoId}/status`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch repository status: ${response.status}`);
  }

  return response.json();
}

export async function fetchRepositoryCommits(
  repoId: string,
  token: string,
  page: number = 1,
  perPage: number = 100
) {
  const response = await fetch(
    `${API_BASE}/api/repositories/${repoId}/fetch-commits?page=${page}&per_page=${perPage}`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch commits from GitHub: ${response.status}`);
  }

  return response.json();
}

export async function generateEmbeddings(repoId: string, token: string) {
  const response = await fetch(`${API_BASE}/api/repositories/${repoId}/cortex-embed`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "e5-base-v2",
      batch_size: 100,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to generate embeddings: ${response.status}`);
  }

  return response.json();
}

export async function queryRAG(
  repoId: string,
  token: string,
  question: string,
  topK: number = 5,
  model: string = "mistral-7b"
) {
  const response = await fetch(`${API_BASE}/api/repositories/${repoId}/cortex-query`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      top_k: topK,
      model,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to query RAG: ${response.status}`);
  }

  return response.json();
}

export async function getEmbeddingStatus(repoId: string, token: string) {
  const response = await fetch(`${API_BASE}/api/repositories/${repoId}/embedding-status`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to get embedding status: ${response.status}`);
  }

  return response.json();
}

export async function fetchCommitDetails(repoId: string, commitSha: string, token: string) {
  const response = await fetch(
    `${API_BASE}/api/repositories/${repoId}/commits/${commitSha}/details`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch commit details: ${response.status}`);
  }

  return response.json();
}
