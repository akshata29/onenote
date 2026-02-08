import { useState, useEffect } from 'react';
import { authFetch, postAuth } from '../api';

interface IngestionJob {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'not_found';
  message?: string;
  progress?: number;
  notebook_name?: string;
  started_at?: string;
  completed_at?: string;
  summary?: {
    pages_processed: number;
    attachments_processed: number;
    chunks_created: number;
    errors: number;
    duration_seconds: number;
  };
}

interface AdminStats {
  indexed_notebooks: number;
  indexed_sections: number;
  content_chunks: number;
  processed_attachments: number;
  active_ingestion_jobs: number;
}

interface AdminPanelProps {
  token: string | null;
  notebooks: any[];
}

export function AdminPanel({ token, notebooks }: AdminPanelProps) {
  const [selectedNotebooks, setSelectedNotebooks] = useState<string[]>([]);
  const [ingestionJobs, setIngestionJobs] = useState<IngestionJob[]>([]);
  const [isIngestingBatch, setIsIngestingBatch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [adminStats, setAdminStats] = useState<AdminStats>({
    indexed_notebooks: 0,
    indexed_sections: 0,
    content_chunks: 0,
    processed_attachments: 0,
    active_ingestion_jobs: 0
  });
  const [availableNotebooks, setAvailableNotebooks] = useState<any[]>([]);

  // Load admin stats and available notebooks
  useEffect(() => {
    if (!token) return;

    const loadAdminData = async () => {
      try {
        // Load admin stats
        const statsResponse = await authFetch('/admin/stats', token);
        if (statsResponse.ok) {
          const stats = await statsResponse.json();
          console.log('Admin stats received:', stats);
          setAdminStats(stats);
        } else {
          console.error('Admin stats failed:', statsResponse.status, statsResponse.statusText);
        }

        // Load available notebooks (excluding already indexed ones)
        const notebooksResponse = await authFetch('/admin/available-notebooks', token);
        if (notebooksResponse.ok) {
          const availableData = await notebooksResponse.json();
          console.log('Available notebooks received:', availableData);
          console.log('Available notebooks count:', availableData.length);
          setAvailableNotebooks(availableData);
        } else {
          console.error('Available notebooks failed:', notebooksResponse.status, notebooksResponse.statusText);
        }

        // Load ingestion jobs
        const jobsResponse = await authFetch('/admin/ingestion-jobs', token);
        if (jobsResponse.ok) {
          const jobs = await jobsResponse.json();
          console.log('Ingestion jobs received:', jobs);
          setIngestionJobs(jobs);
        } else {
          console.error('Ingestion jobs failed:', jobsResponse.status, jobsResponse.statusText);
        }
      } catch (error) {
        console.error('Failed to load admin data:', error);
      }
    };

    loadAdminData();
    
    // Set up polling for real-time updates (reduced frequency)
    const interval = setInterval(loadAdminData, 10000); // 10 seconds instead of 3
    return () => clearInterval(interval);
  }, [token]);

  const handleNotebookToggle = (notebookId: string) => {
    setSelectedNotebooks(prev => 
      prev.includes(notebookId) 
        ? prev.filter(id => id !== notebookId)
        : [...prev, notebookId]
    );
  };

  const handleSingleIngestion = async (notebookId: string, notebookName: string) => {
    if (!token) return;

    try {
      const response = await postAuth('/ingest', {
        notebook_id: notebookId,
        notebook_name: notebookName
      }, token);

      if (response.ok) {
        const result = await response.json();
        console.log('Ingestion started:', result);
      }
    } catch (error) {
      console.error('Single ingestion failed:', error);
    }
  };

  const handleBatchIngestion = async () => {
    if (!token || selectedNotebooks.length === 0) return;
    
    setIsIngestingBatch(true);
    try {
      const requests = selectedNotebooks.map(async (notebookId) => {
        const notebook = availableNotebooks.find(nb => nb.id === notebookId);
        if (notebook) {
          return postAuth('/ingest', {
            notebook_id: notebookId,
            notebook_name: notebook.displayName
          }, token);
        }
      });

      const responses = await Promise.all(requests.filter(Boolean));
      
      for (const response of responses) {
        if (response && response.ok) {
          const result = await response.json();
          console.log('Batch ingestion item started:', result);
        }
      }
      
      setSelectedNotebooks([]);
    } catch (error) {
      console.error('Batch ingestion failed:', error);
    } finally {
      setIsIngestingBatch(false);
    }
  };

  const getJobStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600';
      case 'failed': return 'text-red-600';  
      case 'running': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  const getJobStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅';
      case 'failed': return '❌';
      case 'running': return '🔄';
      default: return '⏳';
    }
  };

  return (
    <div className="p-6 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-2">Search Index Management</h1>
        <p className="text-slate-300">Manage document ingestion and search index content</p>
      </div>

      {/* Index Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div className="bg-panel p-4 rounded-lg border border-slate-700">
          <h3 className="text-sm font-medium text-slate-300 mb-1">Indexed Notebooks</h3>
          <p className="text-2xl font-bold text-slate-100">{adminStats.indexed_notebooks}</p>
        </div>
        <div className="bg-panel p-4 rounded-lg border border-slate-700">
          <h3 className="text-sm font-medium text-slate-300 mb-1">Indexed Sections</h3>
          <p className="text-2xl font-bold text-slate-100">{adminStats.indexed_sections}</p>
        </div>
        <div className="bg-panel p-4 rounded-lg border border-slate-700">
          <h3 className="text-sm font-medium text-slate-300 mb-1">Content Chunks</h3>
          <p className="text-2xl font-bold text-slate-100">{adminStats.content_chunks}</p>
        </div>
        <div className="bg-panel p-4 rounded-lg border border-slate-700">
          <h3 className="text-sm font-medium text-slate-300 mb-1">Processed Attachments</h3>
          <p className="text-2xl font-bold text-slate-100">{adminStats.processed_attachments}</p>
        </div>
      </div>

      {/* Batch Ingestion Controls */}
      <div className="bg-panel p-6 rounded-lg border border-slate-700">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">Batch Ingestion</h2>
        <div className="flex items-center gap-4 mb-4">
          <span className="text-sm text-slate-300">
            {selectedNotebooks.length} notebooks selected
          </span>
          <button
            onClick={handleBatchIngestion}
            disabled={selectedNotebooks.length === 0 || isIngestingBatch}
            className="px-4 py-2 bg-accent text-slate-950 font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isIngestingBatch ? 'Processing...' : 'Start Batch Ingestion'}
          </button>
          <button
            onClick={() => setSelectedNotebooks(availableNotebooks.map(nb => nb.id))}
            className="px-4 py-2 bg-slate-600 text-slate-100 font-medium rounded-lg hover:bg-slate-500"
          >
            Select All
          </button>
          <button
            onClick={() => setSelectedNotebooks([])}
            className="px-4 py-2 bg-slate-700 text-slate-300 font-medium rounded-lg hover:bg-slate-600"
          >
            Clear Selection
          </button>
        </div>
      </div>

      {/* Notebooks Management */}
      <div className="bg-panel p-6 rounded-lg border border-slate-700">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">Notebooks</h2>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {availableNotebooks.length === 0 ? (
            <p className="text-slate-400 text-center py-8">
              {adminStats.indexed_notebooks > 0 
                ? "All notebooks have been indexed! ✅" 
                : "No notebooks available for ingestion"
              }
            </p>
          ) : (
            availableNotebooks.map(notebook => (
              <div key={notebook.id} className="flex items-center justify-between p-3 bg-slate-800 rounded-lg">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={selectedNotebooks.includes(notebook.id)}
                    onChange={() => handleNotebookToggle(notebook.id)}
                    className="w-4 h-4 text-accent bg-slate-700 border-slate-600 rounded focus:ring-accent"
                  />
                  <div>
                    <h3 className="font-medium text-slate-100">{notebook.displayName}</h3>
                    <p className="text-xs text-slate-400">ID: {notebook.id}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleSingleIngestion(notebook.id, notebook.displayName)}
                  disabled={ingestionJobs.some(job => job.job_id === notebook.id && job.status === 'running')}
                  className="px-3 py-1 text-sm bg-slate-600 text-slate-100 rounded hover:bg-slate-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {ingestionJobs.some(job => job.job_id === notebook.id && job.status === 'running') 
                    ? 'Processing...' 
                    : 'Ingest Now'
                  }
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Ingestion Jobs Status */}
      {ingestionJobs.length > 0 && (
        <div className="bg-panel p-6 rounded-lg border border-slate-700">
          <h2 className="text-lg font-semibold text-slate-100 mb-4">
            Ingestion Status
            {adminStats.active_ingestion_jobs > 0 && (
              <span className="ml-2 px-2 py-1 text-xs bg-blue-500/20 text-blue-400 rounded-full">
                {adminStats.active_ingestion_jobs} active
              </span>
            )}
          </h2>
          <div className="space-y-3">
            {ingestionJobs.slice(-5).reverse().map((job, index) => (
              <div key={`${job.job_id || job.notebook_id}-${index}`} className="p-4 bg-slate-800 rounded-lg border border-slate-700">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">{getJobStatusIcon(job.status)}</span>
                  <h3 className="font-medium text-slate-100 flex-1">{job.notebook_name}</h3>
                  <span className={`text-sm font-medium ${getJobStatusColor(job.status)}`}>
                    {job.status.toUpperCase()}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mb-2">{job.job_id || job.notebook_id}</p>
                {job.message && (
                  <p className="text-sm text-slate-300 mb-2">{job.message}</p>
                )}
                {job.progress !== undefined && job.status === 'running' && (
                  <div className="mb-2">
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${job.progress}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{job.progress}% complete</p>
                  </div>
                )}
                {job.summary && job.status === 'completed' && (
                  <div className="text-xs text-slate-400">
                    ✅ {job.summary.pages_processed} pages, {job.summary.chunks_created} chunks, {job.summary.attachments_processed} attachments
                    {job.summary.duration_seconds && (
                      <span className="ml-2">({Math.round(job.summary.duration_seconds)}s)</span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}