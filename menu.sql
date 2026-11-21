DROP TABLE IF EXISTS menu_items;

CREATE TABLE menu_items (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    aliases TEXT[] NOT NULL,
    variants JSONB NOT NULL  
);

CREATE INDEX idx_menu_aliases ON menu_items USING GIN (aliases);

INSERT INTO menu_items (category, item_name, aliases, variants) VALUES
-- 1 to 7: Sandwiches
('Sandwiches', 'Beef Shawerma', ARRAY['شاورما لحمة', 'صاروخ لحمة', 'صاروخ شاورما لحمة', 'شاورما مصري لحمة'], '{"small": 65, "medium": 90, "large": 115}'),
('Sandwiches', 'Chicken Shawerma', ARRAY['شاورما فراخ', 'صاروخ فراخ', 'سوري فراخ', 'شاورما سوري'], '{"small": 60, "medium": 85, "large": 110}'),
('Sandwiches', 'Beef Burger', ARRAY['برجر لحمة', 'برجر', 'برغر', 'برقر', 'همبرجر', 'ساندوتش برجر', 'burger'], '{"single": 140, "double": 200, "triple": 260}'),
('Sandwiches', 'Chicken Burger', ARRAY['تشيكن برجر', 'برجر فراخ', 'ساندوتش فراخ بانيه'], '{"single": 125, "double": 180}'),
('Sandwiches', 'Shish Tawook', ARRAY['شيش طاووق', 'شيش', 'ساندوتش شيش'], '{"medium": 80, "large": 105}'),
('Sandwiches', 'Kofta Sandwich', ARRAY['كفتة', 'ساندوتش كفتة', 'كفتة حاتي', 'صاروخ كفتة'], '{"medium": 70, "large": 95}'),
('Sandwiches', 'Syrian Potatoes', ARRAY['بطاطس سوري', 'ساندوتش بطاطس', 'صاروخ بطاطس'], '{"medium": 45, "large": 60}'),

-- 8 to 12: Pizza
('Pizza', 'Margherita Pizza', ARRAY['مارجريتا', 'بيتزا مارجريتا', 'بيتزا جبنة', 'بيتزا سادة'], '{"small": 95, "medium": 140, "large": 185}'),
('Pizza', 'Pepperoni Pizza', ARRAY['بيبروني', 'بيتزا بيبروني', 'بيتزا سلامي'], '{"small": 120, "medium": 170, "large": 220}'),
('Pizza', 'Chicken Ranch Pizza', ARRAY['تشيكن رانش', 'بيتزا رانش', 'بيتزا فراخ رانش'], '{"small": 135, "medium": 190, "large": 245}'),
('Pizza', 'Chicken BBQ Pizza', ARRAY['تشيكن باربيكيو', 'بيتزا باربيكيو', 'بيتزا فراخ باربيكيو'], '{"small": 135, "medium": 190, "large": 245}'),
('Pizza', 'Mix Cheese Pizza', ARRAY['ميكس جبن', 'بيتزا مشكل جبن', 'بيتزا اربع جبن'], '{"small": 115, "medium": 165, "large": 215}'),

-- 13 to 17: Meals
('Meals', 'Half Grilled Chicken', ARRAY['نص فرخة', 'نص فرخة مشوية', 'نص شواية'], '{"regular": 190, "spicy": 195}'),
('Meals', 'Mix Grill Meal', ARRAY['ميكس جريل', 'وجبة مشويات', 'مشويات مشكلة'], '{"single": 280, "family": 750}'),
('Meals', 'Crispy Strips Meal', ARRAY['ستريبس', 'وجبة ستريبس', 'فراخ كريسبي', 'تشيكن ستريبس'], '{"3_pieces": 120, "5_pieces": 175}'),
('Meals', 'Kofta Meal', ARRAY['وجبة كفتة', 'طبق كفتة مشوية', 'نص كيلو كفتة'], '{"quarter_kilo": 150, "half_kilo": 290}'),
('Meals', 'Shawerma Fatteh', ARRAY['فتة شاورما', 'فتة', 'فتة سوري'], '{"chicken": 130, "beef": 145, "mix": 155}'),

-- 18 to 21: Sides & Salads
('Sides', 'French Fries', ARRAY['بطاطس', 'بطاطس محمرة', 'باكيت بطاطس', 'فرينش فرايز'], '{"small": 30, "medium": 45, "large": 60}'),
('Sides', 'Tahini Salad', ARRAY['سلطة', 'طحينة', 'سلطة طحينة', 'علبة طحينة'], '{"small": 15, "large": 25}'),
('Sides', 'Garlic Dip', ARRAY['تومية', 'سلطة تومية', 'علبة تومية'], '{"small": 15, "large": 25}'),
('Sides', 'Coleslaw', ARRAY['كول سلو', 'سلطة كول سلو', 'سلطة كرنب'], '{"small": 25, "large": 40}'),

-- 22 to 25: Drinks
('Drinks', 'Cola', ARRAY['كولا', 'بيبسي', 'كوكاكولا', 'حاجة ساقعة', 'كانز كولا'], '{"can": 25, "liter": 45}'),
('Drinks', 'Orange Soda', ARRAY['فانتا', 'ميرندا', 'برتقان غازي', 'كانز برتقان'], '{"can": 25, "liter": 45}'),
('Drinks', 'Fresh Orange Juice', ARRAY['عصير برتقان', 'برتقال فريش', 'عصير برتقال'], '{"cup": 45, "bottle": 80}'),
('Drinks', 'Mineral Water', ARRAY['ميه', 'مياه', 'قزازة ميه', 'مياه معدنية'], '{"small": 10, "large": 20}');


