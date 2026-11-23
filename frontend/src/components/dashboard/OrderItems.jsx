import Card from '../ui/Card'
import EmptyState from '../ui/EmptyState'
import { removeItem, setItemQuantity } from '../../services/api'
import { countItems } from '../../utils/sessionHelpers'
import { formatCurrency } from '../../utils/formatters'

// The backend limits one line to 50 units (MAX_LINE_QTY in service.py).
const MAX_QUANTITY = 50

const SMALL_BUTTON =
  'flex h-7 w-7 items-center justify-center rounded-lg bg-gray-100 text-gray-800 hover:bg-gray-200 focus-visible:outline-2 focus-visible:outline-purple-500 disabled:cursor-not-allowed disabled:opacity-40'

// `actions` is only passed in real mode. Items can only change while the
// session is ORDERING (the backend answers 409 otherwise).
function OrderItems({ session, actions }) {
  const items = session.items ?? []
  const units = countItems(items)
  const editable = Boolean(actions) && session.state === 'ORDERING' && !session.ui.timedOutLocally
  const busy = Boolean(actions) && actions.pending

  function changeQuantity(item, quantity) {
    actions.run(session.id, `${item.name}: quantity set to ${quantity}`, () =>
      setItemQuantity(session.id, item.item_id, quantity),
    )
  }

  function remove(item) {
    actions.run(session.id, `${item.name} removed`, () => removeItem(session.id, item.item_id))
  }

  return (
    <Card
      title="Order Details"
      subtitle={`${units} ${units === 1 ? 'item' : 'items'} · ${items.length} ${
        items.length === 1 ? 'line' : 'lines'
      }`}
    >
      {items.length === 0 ? (
        <EmptyState
          icon="cart"
          title="Cart is empty"
          description="The caller has not added any items to this order yet."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[420px] text-sm">
            <thead>
              <tr className="text-left text-xs tracking-wide text-gray-500 uppercase">
                <th scope="col" className="pb-2 font-medium">
                  Item
                </th>
                <th scope="col" className="pb-2 text-right font-medium">
                  Unit price
                </th>
                <th scope="col" className="pb-2 text-right font-medium">
                  Qty
                </th>
                <th scope="col" className="pb-2 text-right font-medium">
                  Line total
                </th>
                {editable && (
                  <th scope="col" className="pb-2 text-right font-medium">
                    <span className="sr-only">Remove</span>
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.map((item) => (
                <tr key={item.item_id}>
                  <td className="py-3 pr-3">
                    <p dir="auto" className="font-medium text-gray-900">
                      {item.name}
                    </p>
                    <p className="font-mono text-xs text-gray-400">#{item.item_id}</p>
                  </td>
                  <td className="py-3 text-right text-gray-600">
                    {formatCurrency(item.unit_price)}
                  </td>
                  <td className="py-3 text-right font-medium text-gray-900">
                    {editable ? (
                      <span className="inline-flex items-center gap-2">
                        <button
                          type="button"
                          aria-label={`Decrease quantity of ${item.name}`}
                          disabled={busy || item.quantity <= 1}
                          onClick={() => changeQuantity(item, item.quantity - 1)}
                          className={SMALL_BUTTON}
                        >
                          −
                        </button>
                        <span className="min-w-6 text-center">{item.quantity}</span>
                        <button
                          type="button"
                          aria-label={`Increase quantity of ${item.name}`}
                          disabled={busy || item.quantity >= MAX_QUANTITY}
                          onClick={() => changeQuantity(item, item.quantity + 1)}
                          className={SMALL_BUTTON}
                        >
                          +
                        </button>
                      </span>
                    ) : (
                      <>×{item.quantity}</>
                    )}
                  </td>
                  <td className="py-3 text-right font-semibold text-gray-900">
                    {formatCurrency(item.line_total)}
                  </td>
                  {editable && (
                    <td className="py-3 pl-3 text-right">
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => remove(item)}
                        className="rounded-lg px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        Remove
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t border-gray-200">
                <th scope="row" colSpan={3} className="pt-4 text-right text-sm text-gray-500">
                  Order total
                </th>
                <td className="pt-4 text-right text-lg font-bold text-purple-700">
                  {formatCurrency(session.total)}
                </td>
                {editable && <td />}
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </Card>
  )
}

export default OrderItems
