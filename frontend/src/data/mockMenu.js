// Sample menu used only by the mock sessions and the "Menu Reference" card.
// Item fields (item_id, name, unit_price) mirror the item shape used in sessions.
// In Phase 3 this can be replaced by data from the real backend.

export const MOCK_MENU = [
  {
    id: 'pizzas',
    name: 'Pizzas',
    items: [
      { item_id: 'pizza-margherita', name: 'Margherita Pizza', unit_price: 9.5 },
      { item_id: 'pizza-pepperoni', name: 'Pepperoni Pizza', unit_price: 11.0 },
      { item_id: 'pizza-veggie', name: 'Veggie Supreme Pizza', unit_price: 12.0 },
    ],
  },
  {
    id: 'sides',
    name: 'Sides',
    items: [
      { item_id: 'side-garlic-bread', name: 'Garlic Bread', unit_price: 4.5 },
      { item_id: 'side-caesar-salad', name: 'Caesar Salad', unit_price: 6.5 },
      { item_id: 'side-wings', name: 'Chicken Wings', unit_price: 8.0 },
    ],
  },
  {
    id: 'drinks',
    name: 'Drinks',
    items: [
      { item_id: 'drink-cola', name: 'Cola', unit_price: 2.5 },
      { item_id: 'drink-lemonade', name: 'Lemonade', unit_price: 3.0 },
      { item_id: 'drink-sparkling-water', name: 'Sparkling Water', unit_price: 2.0 },
    ],
  },
  {
    id: 'desserts',
    name: 'Desserts',
    items: [
      { item_id: 'dessert-tiramisu', name: 'Tiramisu', unit_price: 5.5 },
      { item_id: 'dessert-brownie', name: 'Chocolate Brownie', unit_price: 4.5 },
    ],
  },
]
