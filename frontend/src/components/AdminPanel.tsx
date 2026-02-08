import { useState, useEffect } from 'react';
import { authFetch, postAuth, deleteAuth } from '../api';

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
  const [indexedNotebooks, setIndexedNotebooks] = useState<any[]>([]);

  // Load admin stats and available notebooks
  const fetchIngestionJobs = async () => {
    if (!token) return;
    
    try {
      const jobsResponse = await authFetch('/admin/ingestion-jobs', token);
      if (jobsResponse.ok) {
        const jobs = await jobsResponse.json();
        console.log('Ingestion jobs received:', jobs);
        setIngestionJobs(jobs);
      } else {
        console.error('Ingestion jobs failed:', jobsResponse.status, jobsResponse.statusText);
      }
    } catch (error) {
      console.error('Failed to load ingestion jobs:', error);
    }
  };

  const fetchAvailableNotebooks = async () => {
    if (!token) return;
    
    try {
      const notebooksResponse = await authFetch('/admin/available-notebooks', token);
      if (notebooksResponse.ok) {
        const availableData = await notebooksResponse.json();
        console.log('Available notebooks received:', availableData);
        setAvailableNotebooks(availableData);
      } else {
        console.error('Available notebooks failed:', notebooksResponse.status, notebooksResponse.statusText);
      }
    } catch (error) {
      console.error('Failed to load available notebooks:', error);
    }
  };

  const fetchIndexedNotebooks = async () => {
    if (!token) return;
    
    try {
      const indexedResponse = await authFetch('/admin/indexed-notebooks', token);
      if (indexedResponse.ok) {
        const indexedData = await indexedResponse.json();
        console.log('Indexed notebooks received:', indexedData);
        setIndexedNotebooks(indexedData);
      } else {
        console.error('Indexed notebooks failed:', indexedResponse.status, indexedResponse.statusText);
      }
    } catch (error) {
      console.error('Failed to load indexed notebooks:', error);
    }
  };

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

        // Load all data using the new functions
        await Promise.all([
          fetchAvailableNotebooks(),
          fetchIndexedNotebooks(),
          fetchIngestionJobs()
        ]);
      } catch (error) {
        console.error('Failed to load admin data:', error);
      }
    };

    loadAdminData();
    
    // Set up polling for real-time updates - reduced frequency to prevent connection buildup
    const interval = setInterval(loadAdminData, 15000); // 15 seconds to reduce server load
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

  const handleReindex = async (notebookId: string, notebookName: string) => {
    if (!token) return;

    try {
      const response = await postAuth(`/admin/notebooks/${notebookId}/reindex?notebook_name=${encodeURIComponent(notebookName)}`, {}, token);

      if (response.ok) {
        const result = await response.json();
        console.log('Reindex started:', result);
        // Refresh the ingestion jobs to show the new reindex job
        await fetchIngestionJobs();
      } else {
        console.error('Reindex failed:', await response.text());
      }
    } catch (error) {
      console.error('Reindex failed:', error);
    }
  };

  const handleDeleteNotebook = async (notebookId: string, notebookName: string) => {
    if (!token) return;
    
    if (!confirm(`Are you sure you want to DELETE all indexed content for "${notebookName}"? This cannot be undone.`)) {
      return;
    }

    try {
      const response = await deleteAuth(`/admin/notebooks/${notebookId}`, token);

      if (response.ok) {
        const result = await response.json();
        console.log('Notebook deleted:', result);
        alert(`Successfully deleted ${result.documents_deleted} documents for "${notebookName}"`);
        // Refresh the lists
        await fetchAvailableNotebooks();
        await fetchIndexedNotebooks();
      } else {
        const error = await response.text();
        console.error('Delete failed:', error);
        alert(`Delete failed: ${error}`);
      }
    } catch (error) {
      console.error('Delete failed:', error);
      alert(`Delete failed: ${error}`);
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

      {/* Available Notebooks for Ingestion */}
      <div className="bg-panel p-6 rounded-lg border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-100">Available for Ingestion</h2>
          <span className="px-2 py-1 text-xs bg-orange-500/20 text-orange-400 rounded-full">
            {availableNotebooks.length} notebook{availableNotebooks.length !== 1 ? 's' : ''}
          </span>
        </div>
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

      {/* Indexed (Completed) Notebooks */}
      <div className="bg-panel p-6 rounded-lg border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-100">Indexed Notebooks</h2>
          <span className="px-2 py-1 text-xs bg-green-500/20 text-green-400 rounded-full">
            {indexedNotebooks.length} completed
          </span>
        </div>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {indexedNotebooks.length === 0 ? (
            <p className="text-slate-400 text-center py-8">
              No notebooks have been indexed yet
            </p>
          ) : (
            indexedNotebooks.map(notebook => (
              <div key={notebook.id} className="flex items-center justify-between p-3 bg-slate-800 rounded-lg border border-green-500/20">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-green-500/20 rounded-full flex items-center justify-center">
                    <span className="text-green-400 text-sm">✓</span>
                  </div>
                  <div> 
                    <h3 className="font-medium text-slate-100">{notebook.displayName}</h3>
                    <p className="text-xs text-slate-400">ID: {notebook.id}</p>
                    <p className="text-xs text-green-400">Indexed: {notebook.indexed_date}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleReindex(notebook.id, notebook.displayName)}
                    className="px-3 py-1 text-sm bg-yellow-600 text-slate-100 rounded hover:bg-yellow-500"
                    title="Delete existing content and re-index this notebook"
                  >
                    Reindex
                  </button>
                  <button
                    onClick={() => handleDeleteNotebook(notebook.id, notebook.displayName)}
                    className="px-3 py-1 text-sm bg-red-600 text-slate-100 rounded hover:bg-red-500"
                    title="Delete all indexed content for this notebook"
                  >
                    Delete
                  </button>
                </div>
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