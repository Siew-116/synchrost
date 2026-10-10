import { useQuery } from '@tanstack/react-query'
import { agentAPI } from '../services/api'
import { ScrollText, Bot, Clock, CheckCircle, XCircle, Activity } from 'lucide-react'

export default function AgentLogs() {
  const { data: logs, isLoading } = useQuery({
    queryKey: ['agent-logs'],
    queryFn: () => agentAPI.logs(100).then(r => r.data),
  })

  const { data: tools } = useQuery({
    queryKey: ['agent-tools'],
    queryFn: () => agentAPI.tools().then(r => r.data),
  })

  if (isLoading) return <Loading />

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Agent Logs</h1>
        <p className="text-gray-500 text-sm">Execution trace of the OBSERVE-ANALYZE-PRIORITIZE-PLAN-ACT-VERIFY-LOG loop</p>
      </div>

      {/* Agent tools overview */}
      {tools && (
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <h2 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary-600" />
            Available Agent Tools ({tools.length || 0})
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {tools?.map((t: any) => (
              <div key={t.name} className="p-2 rounded-lg bg-gray-50">
                <div className="flex items-center gap-1.5">
                  <Bot className="w-3 h-3 text-gray-400 flex-shrink-0" />
                  <p className="text-xs font-medium text-gray-700 truncate">{t.name}</p>
                </div>
                {t.requires_approval && (
                  <span className="text-[10px] text-amber-600 mt-0.5 inline-block">needs approval</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Log entries */}
      <div className="space-y-2">
        {logs?.map((log: any) => (
          <div key={log.id} className="bg-white rounded-lg border border-gray-100 p-4">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  log.mode === 'deterministic' ? 'bg-blue-50 text-blue-600' : 'bg-purple-50 text-purple-600'
                }`}>
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{log.intent || 'general'}</p>
                  <p className="text-xs text-gray-400">{log.mode} mode</p>
                </div>
              </div>
              <span className="text-xs text-gray-400 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {log.created_at?.slice(0, 19).replace('T', ' ')}
              </span>
            </div>

            {/* User message */}
            {log.user_message && (
              <div className="bg-blue-50 rounded-lg p-2 mb-2">
                <p className="text-xs text-blue-600 font-medium mb-0.5">User:</p>
                <p className="text-sm text-gray-700">{log.user_message}</p>
              </div>
            )}

            {/* Agent response */}
            {log.response_text && (
              <div className="bg-gray-50 rounded-lg p-2 mb-2">
                <p className="text-xs text-gray-500 font-medium mb-0.5">Agent:</p>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{log.response_text}</p>
              </div>
            )}

            {/* Actions taken */}
            {log.actions_taken?.length > 0 && (
              <div className="mt-2">
                <p className="text-xs text-gray-500 font-medium mb-1">Actions:</p>
                <div className="space-y-1">
                  {log.actions_taken.map((action: any, i: number) => (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      {action.success ? (
                        <CheckCircle className="w-3 h-3 text-green-500" />
                      ) : (
                        <XCircle className="w-3 h-3 text-danger-500" />
                      )}
                      <span className="text-gray-600">{action.tool_name}</span>
                      {action.requires_approval && (
                        <span className="px-1.5 py-0.5 bg-amber-100 text-amber-600 rounded text-[10px]">approval</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Priority */}
            {log.priority && (
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs text-gray-400">Priority:</span>
                <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                  log.priority === 'critical' ? 'bg-red-100 text-red-700' :
                  log.priority === 'high' ? 'bg-amber-100 text-amber-700' :
                  'bg-gray-100 text-gray-600'
                }`}>{log.priority}</span>
              </div>
            )}
          </div>
        ))}
        {logs?.length === 0 && (
          <div className="text-center py-12">
            <ScrollText className="w-12 h-12 text-gray-300 mx-auto mb-2" />
            <p className="text-gray-400">No agent logs yet. Try chatting with the AI Assistant!</p>
          </div>
        )}
      </div>
    </div>
  )
}

function Loading() { return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div> }
