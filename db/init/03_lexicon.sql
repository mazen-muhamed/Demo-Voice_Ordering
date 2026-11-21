-- Optional: confirmation / intent lexicon used by the demo dashboard and by
-- any future DB-driven router.  The live router in voice_agent/processors.py
-- still uses the Python rules; this table is the shared source of truth for
-- the phrases the team agreed on (Abdallah's seed).
CREATE TABLE IF NOT EXISTS lexicon (
    id     SERIAL PRIMARY KEY,
    intent TEXT NOT NULL,
    phrase TEXT NOT NULL,
    UNIQUE (intent, phrase)
);

INSERT INTO lexicon (intent, phrase) VALUES
    ('confirm_order', 'خلاص كده'),
    ('confirm_order', 'ده الطلب'),
    ('confirm_order', 'كده كفاية'),
    ('confirm_order', 'بس كده'),
    ('confirm_order', 'خلاص'),
    ('confirm_yes',   'أيوه'),
    ('confirm_yes',   'ايوه'),
    ('confirm_yes',   'أيوة'),
    ('confirm_yes',   'تمام'),
    ('confirm_yes',   'ماشي'),
    ('confirm_yes',   'اكيد'),
    ('confirm_yes',   'اه'),
    ('confirm_no',    'لأ'),
    ('confirm_no',    'لا'),
    ('confirm_no',    'مش'),
    ('modify',        'خلي'),
    ('modify',        'شيل'),
    ('modify',        'ضيف'),
    ('modify',        'زود'),
    ('modify',        'بدل'),
    ('modify',        'لأ استنى'),
    ('order',         'عايز'),
    ('order',         'عاوز'),
    ('order',         'اطلب'),
    ('order',         'هات'),
    ('ask_delivery',  'بتوصلوا'),
    ('ask_delivery',  'توصيل'),
    ('ask_delivery',  'دليفري'),
    ('status',        'فين طلبي'),
    ('status',        'إيه أخبار'),
    ('hours',         'بتفتحوا'),
    ('hours',         'ساعات'),
    ('complaint',     'مش راضي'),
    ('complaint',     'شكوى'),
    ('human',         'موظف'),
    ('human',         'حد يتكلم'),
    ('thanks',        'شكرا'),
    ('thanks',        'متشكر')
ON CONFLICT (intent, phrase) DO NOTHING;
