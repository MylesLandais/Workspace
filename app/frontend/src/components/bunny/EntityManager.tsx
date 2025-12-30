import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import { IdentityProfile, Relationship, SourceLink, PlatformType } from '../../lib/bunny/types';
import { GET_IDENTITY_PROFILES, GET_IDENTITY_PROFILE } from '../../lib/graphql/queries';
import { CREATE_IDENTITY_PROFILE, UPDATE_IDENTITY_PROFILE, DELETE_IDENTITY_PROFILE, CREATE_RELATIONSHIP, DELETE_RELATIONSHIP, ADD_HANDLE, REMOVE_HANDLE } from '../../lib/graphql/mutations';
import { 
  Users, Save, Plus, Trash2, Instagram, Twitter, Command, 
  ExternalLink, ArrowLeft, Search, Network, Tag, Camera, Youtube, Globe, Link2,
  Eye, EyeOff
} from 'lucide-react';

interface EntityManagerProps {
  onBack: () => void;
}

export const EntityManager: React.FC<EntityManagerProps> = ({ onBack }) => {
  const userId = 'default-user'; // TODO: Get from auth context
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [formState, setFormState] = useState<IdentityProfile | null>(null);
  const [filterText, setFilterText] = useState('');
  
  // Local state for adding new relationship
  const [newRelTargetId, setNewRelTargetId] = useState('');
  const [newRelType, setNewRelType] = useState('');
  
  // Local state for adding new source
  const [newSourcePlatform, setNewSourcePlatform] = useState<PlatformType>('reddit');
  const [newSourceId, setNewSourceId] = useState('');
  const [newSourceLabel, setNewSourceLabel] = useState('');

  // Load identities from GraphQL
  const { data: identitiesData, refetch: refetchIdentities } = useQuery(GET_IDENTITY_PROFILES, {
    variables: { query: filterText || undefined, limit: 100 },
    fetchPolicy: 'cache-and-network',
  });
  
  const [createProfile] = useMutation(CREATE_IDENTITY_PROFILE, {
    refetchQueries: [{ query: GET_IDENTITY_PROFILES, variables: { limit: 100 } }],
  });
  
  const [updateProfile] = useMutation(UPDATE_IDENTITY_PROFILE, {
    refetchQueries: [{ query: GET_IDENTITY_PROFILES, variables: { limit: 100 } }],
  });
  
  const [deleteProfile] = useMutation(DELETE_IDENTITY_PROFILE, {
    refetchQueries: [{ query: GET_IDENTITY_PROFILES, variables: { limit: 100 } }],
  });
  
  const [createRel] = useMutation(CREATE_RELATIONSHIP, {
    refetchQueries: [{ query: GET_IDENTITY_PROFILE, variables: { id: selectedId } }],
  });
  
  const [deleteRel] = useMutation(DELETE_RELATIONSHIP, {
    refetchQueries: [{ query: GET_IDENTITY_PROFILE, variables: { id: selectedId } }],
  });
  
  const [addHandle] = useMutation(ADD_HANDLE, {
    refetchQueries: [{ query: GET_IDENTITY_PROFILE, variables: { id: selectedId } }],
  });
  
  const [removeHandle] = useMutation(REMOVE_HANDLE, {
    refetchQueries: [{ query: GET_IDENTITY_PROFILE, variables: { id: selectedId } }],
  });

  const identities: Record<string, IdentityProfile> = {};
  if (identitiesData?.getIdentityProfiles) {
    identitiesData.getIdentityProfiles.forEach((profile: IdentityProfile) => {
      identities[profile.id] = profile;
    });
  }

  const handleSelect = (id: string) => {
    setSelectedId(id);
    setFormState({ ...identities[id] });
    setIsEditing(false);
    resetForms();
  };

  const resetForms = () => {
    setNewRelTargetId('');
    setNewRelType('');
    setNewSourceId('');
    setNewSourceLabel('');
  };

  const handleSave = async () => {
    if (formState && selectedId) {
      try {
        await updateProfile({
          variables: {
            id: selectedId,
            input: {
              name: formState.name,
              bio: formState.bio,
              avatarUrl: formState.avatarUrl,
              aliases: formState.aliases,
              contextKeywords: formState.contextKeywords,
              imagePool: formState.imagePool,
            },
          },
        });
        setIsEditing(false);
        await refetchIdentities();
      } catch (error) {
        console.error('Failed to update profile:', error);
        alert('Failed to save. Please try again.');
      }
    }
  };

  const handleCreate = async () => {
    try {
      const result = await createProfile({
        variables: {
          userId,
          input: {
            name: 'New Identity',
            bio: 'Enter bio here...',
            avatarUrl: 'https://images.unsplash.com/photo-1633332755192-727a05c4013d?w=400&h=400&fit=crop',
            aliases: [],
            sources: [],
            contextKeywords: [],
            imagePool: [],
            relationships: [],
          },
        },
      });
      
      if (result.data?.createIdentityProfile) {
        const newProfile = result.data.createIdentityProfile;
        setSelectedId(newProfile.id);
        setFormState(newProfile);
        setIsEditing(true);
        resetForms();
        await refetchIdentities();
      }
    } catch (error) {
      console.error('Failed to create profile:', error);
      alert('Failed to create. Please try again.');
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm(`Delete ${identities[id]?.name}?`)) {
      try {
        await deleteProfile({ variables: { id } });
        if (selectedId === id) setSelectedId(null);
        await refetchIdentities();
      } catch (error) {
        console.error('Failed to delete profile:', error);
        alert('Failed to delete. Please try again.');
      }
    }
  };

  const handleAddRelationship = async () => {
    if (formState && selectedId && newRelTargetId && newRelType) {
      try {
        await createRel({
          variables: {
            profileId: selectedId,
            input: {
              targetId: newRelTargetId,
              type: newRelType,
            },
          },
        });
        setNewRelTargetId('');
        setNewRelType('');
        // Refetch the profile to get updated relationships
        const { data } = await refetchIdentities();
        if (data?.getIdentityProfiles) {
          const updated = data.getIdentityProfiles.find((p: IdentityProfile) => p.id === selectedId);
          if (updated) setFormState(updated);
        }
      } catch (error) {
        console.error('Failed to add relationship:', error);
        alert('Failed to add relationship. Please try again.');
      }
    }
  };

  const handleRemoveRelationship = async (targetId: string) => {
    if (formState && selectedId) {
      try {
        await deleteRel({
          variables: {
            profileId: selectedId,
            targetId,
          },
        });
        // Refetch the profile
        const { data } = await refetchIdentities();
        if (data?.getIdentityProfiles) {
          const updated = data.getIdentityProfiles.find((p: IdentityProfile) => p.id === selectedId);
          if (updated) setFormState(updated);
        }
      } catch (error) {
        console.error('Failed to remove relationship:', error);
        alert('Failed to remove relationship. Please try again.');
      }
    }
  };

  const handleAddSource = async () => {
    if (formState && selectedId && newSourceId) {
      try {
        const platformMap: Record<string, string> = {
          'reddit': 'REDDIT',
          'instagram': 'INSTAGRAM',
          'twitter': 'TWITTER',
          'youtube': 'YOUTUBE',
          'tiktok': 'TIKTOK',
        };
        
        await addHandle({
          variables: {
            creatorId: selectedId,
            platform: platformMap[newSourcePlatform] || 'REDDIT',
            username: newSourceId,
            url: `https://${newSourcePlatform}.com/${newSourceId}`,
          },
        });
        
        setNewSourceId('');
        setNewSourceLabel('');
        // Refetch to get updated profile
        const { data } = await refetchIdentities();
        if (data?.getIdentityProfiles) {
          const updated = data.getIdentityProfiles.find((p: IdentityProfile) => p.id === selectedId);
          if (updated) setFormState(updated);
        }
      } catch (error) {
        console.error('Failed to add source:', error);
        alert('Failed to add source. Please try again.');
      }
    }
  };

  const handleRemoveSource = async (sourceIdOrIndex: string | number) => {
    if (formState && selectedId) {
      try {
        // Find the source to get its database ID
        const source = typeof sourceIdOrIndex === 'number' 
          ? formState.sources[sourceIdOrIndex]
          : formState.sources.find(s => s.id === sourceIdOrIndex || s.databaseId === sourceIdOrIndex);
        
        if (!source) {
          console.error('Source not found');
          return;
        }
        
        // Use databaseId if available, otherwise try to find by username
        const handleId = source.databaseId || source.id;
        await removeHandle({ variables: { handleId } });
        // Refetch to get updated profile
        const { data } = await refetchIdentities();
        if (data?.getIdentityProfiles) {
          const updated = data.getIdentityProfiles.find((p: IdentityProfile) => p.id === selectedId);
          if (updated) setFormState(updated);
        }
      } catch (error) {
        console.error('Failed to remove source:', error);
        alert('Failed to remove source. Please try again.');
      }
    }
  };

  const handleToggleSourceVisibility = async (sourceIdOrIndex: string | number, currentHidden: boolean) => {
    if (formState && selectedId) {
      // Find the source
      const source = typeof sourceIdOrIndex === 'number' 
        ? formState.sources[sourceIdOrIndex]
        : formState.sources.find(s => s.id === sourceIdOrIndex || s.databaseId === sourceIdOrIndex);
      
      if (!source) {
        console.error('Source not found');
        return;
      }
      
      // TODO: Implement updateHandleVisibility mutation in backend
      // For now, update locally and save
      const updatedSources = formState.sources.map(s => 
        (s.id === source.id || s.databaseId === source.databaseId) 
          ? { ...s, hidden: !currentHidden }
          : s
      );
      setFormState({ ...formState, sources: updatedSources });
      // Save will happen on handleSave
    }
  };

  const getPlatformIcon = (platform: PlatformType) => {
      switch (platform) {
          case 'reddit': return <span className="font-bold text-xs">r/</span>;
          case 'instagram': return <Instagram className="w-3 h-3" />;
          case 'twitter': return <Twitter className="w-3 h-3" />;
          case 'youtube': return <Youtube className="w-3 h-3" />;
          case 'tiktok': return <span className="font-bold text-[9px] uppercase">TT</span>;
          default: return <Globe className="w-3 h-3" />;
      }
  };

  return (
    <div className="h-full flex flex-col md:flex-row bg-app-bg text-app-text">
      
      {/* Left Pane: List */}
      <div className="w-full md:w-80 border-r border-app-border flex flex-col h-full bg-app-bg">
        <div className="p-4 border-b border-app-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button onClick={onBack} className="p-2 hover:bg-app-surface rounded-full">
              <ArrowLeft className="w-5 h-5 text-app-muted" />
            </button>
            <h2 className="font-bold text-lg">Entities</h2>
          </div>
          <button onClick={handleCreate} className="p-2 bg-app-accent text-white rounded-full hover:bg-app-accent-hover transition-colors">
            <Plus className="w-4 h-4" />
          </button>
        </div>
        
        <div className="p-4 border-b border-app-border bg-app-surface/50">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-app-muted" />
            <input 
              type="text" 
              placeholder="Filter entities..."
              value={filterText}
              onChange={e => setFilterText(e.target.value)}
              className="w-full bg-app-bg border border-app-border rounded-lg pl-9 pr-3 py-2 text-sm focus:border-app-accent focus:outline-none"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {Object.values(identities)
            .filter(p => p.name.toLowerCase().includes(filterText.toLowerCase()))
            .map(profile => (
            <div 
              key={profile.id}
              onClick={() => handleSelect(profile.id)}
              className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${selectedId === profile.id ? 'bg-app-accent/20 border border-app-accent/50' : 'hover:bg-app-surface'}`}
            >
              <img src={profile.avatarUrl} alt={profile.name} className="w-10 h-10 rounded-full object-cover border border-app-border" />
              <div className="overflow-hidden">
                <h3 className="font-medium truncate">{profile.name}</h3>
                <p className="text-xs text-app-muted truncate">{profile.bio}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right Pane: Details / Editor */}
      <div className="flex-1 h-full overflow-y-auto bg-app-surface/30">
        {selectedId && formState ? (
          <div className="p-6 md:p-10 max-w-4xl mx-auto space-y-8 animate-in fade-in duration-300">
            
            {/* Header Card */}
            <div className="bg-app-surface border border-app-border rounded-2xl p-6 shadow-xl relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-24 bg-gradient-to-r from-app-accent/20 to-purple-500/20" />
              
              <div className="relative flex flex-col md:flex-row gap-6 mt-4">
                <div className="relative group">
                  <img src={formState.avatarUrl} alt={formState.name} className="w-32 h-32 rounded-2xl object-cover border-4 border-app-surface shadow-lg" />
                  <button className="absolute bottom-2 right-2 p-2 bg-black/70 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                    <Camera className="w-4 h-4" />
                  </button>
                </div>
                
                <div className="flex-1 space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1 w-full">
                      <label className="text-xs font-semibold text-app-muted uppercase tracking-wider">Entity Name</label>
                      <input 
                        type="text" 
                        value={formState.name}
                        onChange={e => setFormState({ ...formState, name: e.target.value })}
                        className="w-full text-3xl font-bold bg-transparent border-b border-transparent focus:border-app-accent focus:outline-none"
                      />
                    </div>
                    <div className="flex gap-2">
                       <button 
                        onClick={() => handleDelete(formState.id)}
                        className="p-2 text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                        title="Delete Entity"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-app-muted uppercase tracking-wider">Bio</label>
                    <textarea 
                      value={formState.bio}
                      onChange={e => setFormState({ ...formState, bio: e.target.value })}
                      className="w-full bg-app-bg/50 border border-app-border rounded-lg p-3 text-sm focus:border-app-accent focus:outline-none min-h-[80px]"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Source Routing Card (Dynamic) */}
              <div className="bg-app-surface border border-app-border rounded-xl p-6 space-y-4">
                <div className="flex items-center gap-2 mb-2">
                  <Network className="w-5 h-5 text-app-accent" />
                  <h3 className="font-semibold text-lg">Mapped Sources</h3>
                </div>
                <p className="text-xs text-app-muted mb-4">Map external accounts (e.g. Alts, Fan Pages, Spam Accounts) to this identity.</p>

                {/* List Sources */}
                <div className="space-y-2 mb-4">
                    {formState.sources.map((src, idx) => (
                        <div 
                          key={idx} 
                          className={`flex items-center gap-3 bg-app-bg p-2 rounded border border-app-border/50 transition-all ${src.hidden ? 'opacity-50 grayscale' : ''}`}
                        >
                            <div className={`w-6 h-6 rounded flex items-center justify-center text-app-text/80 bg-app-surface`}>
                                {getPlatformIcon(src.platform)}
                            </div>
                            <div className="flex-1 flex flex-col min-w-0">
                                <div className="flex items-center gap-2">
                                    <span className={`text-sm font-medium truncate ${src.hidden ? 'line-through text-app-muted' : ''}`}>{src.id}</span>
                                    {src.label && <span className="text-[10px] bg-app-accent/20 text-app-accent px-1.5 rounded">{src.label}</span>}
                                </div>
                                <span className="text-[10px] text-app-muted capitalize">{src.platform}</span>
                            </div>
                            
                            {/* Toggle Visibility */}
                            <button 
                                onClick={() => handleToggleSourceVisibility(src.id, src.hidden)}
                                className={`p-1.5 rounded hover:bg-app-surface transition-colors ${src.hidden ? 'text-app-muted' : 'text-app-accent'}`}
                                title={src.hidden ? "Show in feed" : "Hide from feed"}
                            >
                                {src.hidden ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                            </button>

                            <button 
                                onClick={() => handleRemoveSource(src.id)}
                                className="text-app-muted hover:text-red-400 p-1.5 rounded hover:bg-app-surface transition-colors"
                                title="Remove Source"
                            >
                                <XIcon className="w-3.5 h-3.5" />
                            </button>
                        </div>
                    ))}
                    {formState.sources.length === 0 && <div className="text-center py-4 text-xs text-app-muted italic bg-app-bg/30 rounded">No sources mapped yet.</div>}
                </div>

                {/* Add Source Form */}
                <div className="flex flex-col gap-2 bg-app-bg/50 p-3 rounded-lg border border-app-border/50">
                    <div className="text-xs font-semibold text-app-muted uppercase">Add Source</div>
                    <div className="flex gap-2">
                        <select
                            value={newSourcePlatform}
                            onChange={(e) => setNewSourcePlatform(e.target.value as PlatformType)}
                            className="bg-app-surface border border-app-border rounded px-2 py-1.5 text-xs focus:border-app-accent outline-none"
                        >
                            <option value="reddit">Reddit</option>
                            <option value="instagram">Instagram</option>
                            <option value="twitter">Twitter / X</option>
                            <option value="tiktok">TikTok</option>
                            <option value="youtube">YouTube</option>
                            <option value="web">Web/RSS</option>
                        </select>
                        <input 
                            type="text"
                            value={newSourceId}
                            onChange={(e) => setNewSourceId(e.target.value)}
                            placeholder={newSourcePlatform === 'reddit' ? 'Subreddit Name' : 'Handle / ID'}
                            className="flex-1 bg-app-surface border border-app-border rounded px-2 py-1.5 text-xs focus:border-app-accent outline-none"
                        />
                    </div>
                    <div className="flex gap-2">
                         <input 
                            type="text"
                            value={newSourceLabel}
                            onChange={(e) => setNewSourceLabel(e.target.value)}
                            placeholder="Label (e.g. Spam, Vlog, Alt)"
                            className="flex-1 bg-app-surface border border-app-border rounded px-2 py-1.5 text-xs focus:border-app-accent outline-none"
                        />
                        <button 
                            onClick={handleAddSource}
                            disabled={!newSourceId}
                            className="bg-app-accent hover:bg-app-accent-hover disabled:opacity-50 disabled:cursor-not-allowed text-white px-3 py-1.5 rounded text-xs font-medium transition-colors"
                        >
                            Add
                        </button>
                    </div>
                </div>

              </div>

              {/* Context & Tags Card */}
              <div className="bg-app-surface border border-app-border rounded-xl p-6 space-y-4">
                 <div className="flex items-center gap-2 mb-2">
                  <Tag className="w-5 h-5 text-app-accent" />
                  <h3 className="font-semibold text-lg">Context & Keywords</h3>
                </div>
                <p className="text-xs text-app-muted mb-4">Keywords help the AI find relevant content and generate accurate captions.</p>
                
                <div className="flex flex-wrap gap-2 mb-2">
                  {formState.contextKeywords.map((kw, idx) => (
                    <span key={idx} className="bg-app-accent/10 text-app-accent px-2 py-1 rounded-md text-sm flex items-center gap-1">
                      {kw}
                      <button 
                        onClick={() => setFormState({...formState, contextKeywords: formState.contextKeywords.filter((_, i) => i !== idx)})}
                        className="hover:text-red-400"
                      >
                        <XIcon className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                   <input 
                    type="text" 
                    placeholder="Add keyword + Enter"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        const val = e.currentTarget.value.trim();
                        if (val) {
                          setFormState({ ...formState, contextKeywords: [...formState.contextKeywords, val] });
                          e.currentTarget.value = '';
                        }
                      }
                    }}
                    className="flex-1 bg-app-bg border border-app-border rounded px-3 py-1.5 text-sm"
                  />
                </div>

                <div className="pt-4 border-t border-app-border mt-4">
                   <h4 className="text-sm font-semibold mb-2">Entity Relationships</h4>
                   
                   {/* List Existing Relationships */}
                   <div className="space-y-2 mb-3">
                     {formState.relationships.map((rel, idx) => (
                       <div key={idx} className="flex items-center justify-between text-sm bg-app-bg p-2 rounded border border-app-border/50">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-app-muted">is</span>
                            <span className="text-app-text font-medium bg-app-surface px-1.5 py-0.5 rounded text-xs">{rel.type}</span>
                            <span className="text-app-muted">of</span>
                            <span className="font-medium text-app-accent">{identities[rel.targetId]?.name || rel.targetId}</span>
                          </div>
                          <button 
                            onClick={() => handleRemoveRelationship(rel.targetId)}
                            className="text-app-muted hover:text-red-400 p-1"
                            title="Remove Relationship"
                          >
                            <XIcon className="w-3 h-3" />
                          </button>
                       </div>
                     ))}
                     {formState.relationships.length === 0 && <p className="text-xs text-app-muted italic">No relationships mapped.</p>}
                   </div>

                   {/* Add New Relationship */}
                   <div className="flex flex-col gap-2 bg-app-bg/50 p-3 rounded-lg border border-app-border/50">
                      <div className="text-xs font-semibold text-app-muted uppercase">Add Relationship</div>
                      <div className="flex flex-col sm:flex-row gap-2">
                        <select 
                            value={newRelTargetId}
                            onChange={(e) => setNewRelTargetId(e.target.value)}
                            className="flex-1 bg-app-surface border border-app-border rounded px-2 py-1.5 text-xs focus:border-app-accent outline-none"
                        >
                            <option value="">Select Entity...</option>
                            {Object.values(identities)
                                .filter(id => id.id !== formState.id) // Exclude self
                                .map(id => (
                                    <option key={id.id} value={id.id}>{id.name}</option>
                                ))
                            }
                        </select>
                      </div>
                      <div className="flex gap-2">
                        <input 
                            type="text"
                            value={newRelType}
                            onChange={(e) => setNewRelType(e.target.value)}
                            placeholder="Type (e.g. Partner)"
                            className="flex-1 bg-app-surface border border-app-border rounded px-2 py-1.5 text-xs focus:border-app-accent outline-none"
                        />
                        <button 
                            onClick={handleAddRelationship}
                            disabled={!newRelTargetId || !newRelType}
                            className="bg-app-accent hover:bg-app-accent-hover disabled:opacity-50 disabled:cursor-not-allowed text-white px-3 py-1.5 rounded text-xs font-medium transition-colors"
                        >
                            Add
                        </button>
                      </div>
                   </div>
                </div>
              </div>

            </div>
            
            {/* Sticky Save Bar */}
            <div className="sticky bottom-6 flex justify-end">
              <button 
                onClick={handleSave}
                className="flex items-center gap-2 bg-app-accent hover:bg-app-accent-hover text-white px-6 py-3 rounded-full shadow-lg font-medium transition-all transform active:scale-95"
              >
                <Save className="w-5 h-5" />
                Save Changes
              </button>
            </div>

          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-app-muted">
            <Users className="w-16 h-16 mb-4 opacity-20" />
            <p className="text-lg">Select an entity to manage or create a new one.</p>
          </div>
        )}
      </div>
    </div>
  );
};

const XIcon = ({ className }: { className?: string }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
  >
    <path d="M18 6 6 18" />
    <path d="m6 6 18 18" />
  </svg>
);

