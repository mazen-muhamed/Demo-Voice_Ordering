import Card from '../ui/Card'
import EmptyState from '../ui/EmptyState'
import Icon from '../ui/Icon'
import { formatClock } from '../../utils/formatters'

// Shows only what the voice agent said to the selected call, oldest first.
// `responses` is already limited to this session by the parent. Customer
// speech is never shown. In real mode the list stays empty until the backend
// starts sending response events (see utils/agentResponses.js).

function AgentResponses({ session, responses, isMock }) {
  let subtitle = 'What the voice agent said to the selected caller'
  if (isMock) subtitle = 'Mock Preview · sample responses, not from the backend'

  return (
    <Card
      id="agent-responses"
      title="Agent Responses"
      subtitle={subtitle}
      action={
        isMock && (
          <span className="rounded-full bg-purple-50 px-2.5 py-1 text-xs font-semibold text-purple-700 ring-1 ring-purple-600/20 ring-inset">
            Mock Preview
          </span>
        )
      }
    >
      {!session ? (
        <EmptyState
          icon="mic"
          title="No session selected"
          description="Select a session to see the responses the agent gave that caller."
        />
      ) : responses.length === 0 ? (
        <EmptyState
          icon="mic"
          title="No agent responses received yet."
          description={
            isMock
              ? 'This mock session has no sample responses.'
              : 'Waiting for Backend response-event integration.'
          }
        />
      ) : (
        <ol className="max-h-96 space-y-3 overflow-y-auto pr-1">
          {responses.map((response) => (
            <li key={response.id} className="flex items-start gap-3">
              <span
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-purple-100 text-purple-600"
                title="Agent"
              >
                <Icon name="mic" className="h-4 w-4" />
              </span>
              <div className="min-w-0 max-w-[85%] rounded-2xl rounded-tl-sm bg-gray-100 px-4 py-2.5">
                <p className="text-[11px] font-medium text-gray-500">
                  Agent
                  {response.at && (
                    <span className="ml-2 font-mono">{formatClock(response.at)}</span>
                  )}
                </p>
                <p dir="auto" className="mt-0.5 text-sm break-words text-gray-900">
                  {response.text}
                </p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}

export default AgentResponses
