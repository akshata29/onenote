import { useState, useEffect } from 'react';
import { authFetch, postAuth } from '../api';

interface SearchFilter {
  notebook_ids?: string[];
  section_ids?: string[];
  content_types?: string[];
  date_range?: { start: string; end: string };
  attachment_types?: string[];
  has_attachments?: boolean;
}

interface SearchResult {
  answer: string;
  citations: any[];
  mode: string;
  search_mode?: string;
  filter_applied?: boolean;
  total_results?: number;
}

interface AdvancedSearchProps {
  token: string | null;
  notebooks: any[];
  onSearch: (result: SearchResult) => void;
}

export function AdvancedSearch({ token, notebooks, onSearch }: AdvancedSearchProps) {
  const [query, setQuery] = useState('');
  const [searchMode, setSearchMode] = useState('hybrid');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilter>({});
  const [facets, setFacets] = useState<any>({});
  const [isSearching, setIsSearching] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Load facets for filter options
  useEffect(() => {
    if (!token) return;
    
    const loadFacets = async () => {
      try {
        const response = await authFetch('/search/facets', token);
        if (response.ok) {
          const data = await response.json();
          setFacets(data.facets || {});
        }
      } catch (error) {
        console.error('Failed to load facets:', error);
      }
    };
    
    loadFacets();
  }, [token]);

  // Get search suggestions
  const handleQueryChange = async (value: string) => {
    setQuery(value);
    
    if (value.length > 2 && token) {
      try {
        const response = await authFetch(`/search/suggestions?query=${encodeURIComponent(value)}&top=5`, token);
        if (response.ok) {
          const data = await response.json();
          setSuggestions(data.suggestions || []);
          setShowSuggestions(true);
        }
      } catch (error) {
        console.error('Failed to get suggestions:', error);
        setSuggestions([]);
      }
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const handleSearch = async () => {
    if (!token || !query.trim()) return;

    setIsSearching(true);
    setShowSuggestions(false);
    try {
      const searchPayload = {
        query: query.trim(),
        filters,
        search_mode: searchMode,
        top: 15
      };

      const response = await postAuth('/search/advanced', searchPayload, token);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      onSearch(result);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleFilterChange = (key: keyof SearchFilter, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const clearFilters = () => {
    setFilters({});
  };

  const getActiveFilterCount = () => {
    return Object.values(filters).filter(value => 
      value !== undefined && 
      value !== null && 
      (Array.isArray(value) ? value.length > 0 : true)
    ).length;
  };

  return (
    <div className="space-y-4">
      {/* Search Input */}
      <div className="relative">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => handleQueryChange(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Ask a question about your OneNote content..."
              className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:border-accent focus:ring-1 focus:ring-accent"
            />
            
            {/* Search Suggestions */}
            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-600 rounded-lg shadow-lg z-10">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setQuery(suggestion);
                      setShowSuggestions(false);
                    }}
                    className="w-full px-4 py-2 text-left text-slate-100 hover:bg-slate-700 first:rounded-t-lg last:rounded-b-lg"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <button
            onClick={handleSearch}
            disabled={isSearching || !query.trim()}
            className="px-6 py-3 bg-accent text-slate-950 font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent/90"
          >
            {isSearching ? 'Searching...' : 'Search'}
          </button>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-3 font-medium rounded-lg border ${
              showFilters || getActiveFilterCount() > 0
                ? 'bg-accent/10 border-accent text-accent'
                : 'bg-slate-700 border-slate-600 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Filters {getActiveFilterCount() > 0 && `(${getActiveFilterCount()})`}
          </button>
        </div>
      </div>

      {/* Search Mode Selection */}
      <div className="flex gap-2">
        <span className="text-sm text-slate-300 py-2">Search mode:</span>
        {(['hybrid', 'semantic', 'simple', 'full'] as const).map(mode => (
          <button
            key={mode}
            onClick={() => setSearchMode(mode)}
            className={`px-3 py-1 text-xs font-medium rounded-full ${
              searchMode === mode
                ? 'bg-accent text-slate-950'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {mode}
          </button>
        ))}
      </div>

      {/* Advanced Filters Panel */}
      {showFilters && (
        <div className="bg-panel p-6 rounded-lg border border-slate-700 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-slate-100">Advanced Filters</h3>
            <button
              onClick={clearFilters}
              className="text-sm text-slate-400 hover:text-slate-300"
            >
              Clear All
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Notebook Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Notebooks</label>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {notebooks.map(notebook => (
                  <label key={notebook.id} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={filters.notebook_ids?.includes(notebook.id) || false}
                      onChange={(e) => {
                        const current = filters.notebook_ids || [];
                        if (e.target.checked) {
                          handleFilterChange('notebook_ids', [...current, notebook.id]);
                        } else {
                          handleFilterChange('notebook_ids', current.filter(id => id !== notebook.id));
                        }
                      }}
                      className="w-4 h-4 text-accent bg-slate-700 border-slate-600 rounded focus:ring-accent"
                    />
                    <span className="text-sm text-slate-300 truncate" title={notebook.displayName}>
                      {notebook.displayName}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Content Type Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Content Types</label>
              <div className="space-y-2">
                {['page_text', 'attachment'].map(type => (
                  <label key={type} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={filters.content_types?.includes(type) || false}
                      onChange={(e) => {
                        const current = filters.content_types || [];
                        if (e.target.checked) {
                          handleFilterChange('content_types', [...current, type]);
                        } else {
                          handleFilterChange('content_types', current.filter(t => t !== type));
                        }
                      }}
                      className="w-4 h-4 text-accent bg-slate-700 border-slate-600 rounded focus:ring-accent"
                    />
                    <span className="text-sm text-slate-300">
                      {type === 'page_text' ? 'Page Content' : 'Attachments'}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Attachment Types Filter */}
            {facets.attachment_filetype && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Attachment Types</label>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {facets.attachment_filetype.map((item: any) => (
                    <label key={item.value} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={filters.attachment_types?.includes(item.value) || false}
                        onChange={(e) => {
                          const current = filters.attachment_types || [];
                          if (e.target.checked) {
                            handleFilterChange('attachment_types', [...current, item.value]);
                          } else {
                            handleFilterChange('attachment_types', current.filter(t => t !== item.value));
                          }
                        }}
                        className="w-4 h-4 text-accent bg-slate-700 border-slate-600 rounded focus:ring-accent"
                      />
                      <span className="text-sm text-slate-300">
                        .{item.value} ({item.count})
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Date Range Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Date Range</label>
              <div className="space-y-2">
                <input
                  type="date"
                  value={filters.date_range?.start || ''}
                  onChange={(e) => handleFilterChange('date_range', {
                    ...filters.date_range,
                    start: e.target.value
                  })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded text-slate-100 text-sm"
                  placeholder="Start date"
                />
                <input
                  type="date"
                  value={filters.date_range?.end || ''}
                  onChange={(e) => handleFilterChange('date_range', {
                    ...filters.date_range,
                    end: e.target.value
                  })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded text-slate-100 text-sm"
                  placeholder="End date"
                />
              </div>
            </div>

            {/* Has Attachments Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Attachments</label>
              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="has_attachments"
                    checked={filters.has_attachments === undefined}
                    onChange={() => handleFilterChange('has_attachments', undefined)}
                    className="w-4 h-4 text-accent bg-slate-700 border-slate-600 focus:ring-accent"
                  />
                  <span className="text-sm text-slate-300">All content</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="has_attachments"
                    checked={filters.has_attachments === true}
                    onChange={() => handleFilterChange('has_attachments', true)}
                    className="w-4 h-4 text-accent bg-slate-700 border-slate-600 focus:ring-accent"
                  />
                  <span className="text-sm text-slate-300">Has attachments</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="has_attachments"
                    checked={filters.has_attachments === false}
                    onChange={() => handleFilterChange('has_attachments', false)}
                    className="w-4 h-4 text-accent bg-slate-700 border-slate-600 focus:ring-accent"
                  />
                  <span className="text-sm text-slate-300">No attachments</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}