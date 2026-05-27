# Система начисления баллов — Parfindo

## Общая логика

Каждый парфюм из каталога получает **числовой score**. Топ-5 по баллам показываются пользователю.
Баллы начисляются по **5 критериям** путём сопоставления аккордов аромата с ответами пользователя.

Аккорды аромата берутся из базы 76k парфюмов (`fragrances_db.json`). Если аромат найден в базе — используются его аккорды; если нет — аккорды недоступны и аромат получает меньше баллов.

---

## Критерии и баллы

### 1. Направление (ветка) — до ~20 баллов
**+4 балла** за каждый совпавший аккорд из списка ветки.

| Ветка | Целевые аккорды |
|-------|----------------|
| Fresh Clean | Fresh, Citrus, Aquatic, Green, Clean |
| Warm Cozy | Warm, Gourmand, Vanilla, Amber, Balsamic, Sweet |
| Dark Sexy | Leather, Tobacco, Smoky, Spicy, Animal |
| Elegant Luxury | Floral, Powdery, Woody, Iris, Rose |
| Artistic Niche | Aromatic, Earthy, Incense, Animal, Herbal |
| Soft Skin Scent | Musky, Powdery, Clean, White Floral, Soapy |

---

### 2. Ноты — +3 балла за совпадение

Ищет ключевые слова в тексте нот (top/middle/base) аромата. Поиск по **русским и английским** словам.

| Выбор | Ключевые слова |
|-------|---------------|
| Цитрус | bergamot, lemon, grapefruit, бергамот, лимон, грейпфрут… |
| Флоральные | rose, jasmine, peony, роза, жасмин, пион… |
| Уд/Сандал | oud, agarwood, incense, уд, ладан… |
| Ваниль | vanilla, tonka, benzoin, ваниль, тонка… |
| Ветивер | vetiver, patchouli, moss, ветивер, пачули… |
| Амбра/Мускус | amber, ambroxan, labdanum, амбра, амброксан… |
| Фрукты | peach, cherry, pear, персик, вишня, груша… |
| Морские | sea, aquatic, ozone, salt, морской, океан… |
| Специи | pepper, cinnamon, cardamom, шафран, корица… |
| Дерево | cedar, sandalwood, кедр, сандал… |
| Кожа | leather, suede, кожа, замша… |
| Табак | tobacco, rum, whiskey, табак, ром… |
| Мускус | musk, cashmeran, мускус, кашмеран… |

---

### 3. Вайб — +4 балла за каждый совпавший аккорд

Каждый вайб-вариант маппится на список аккордов. Все выбранные вайбы суммируются.

Примеры:
| Вайб | Аккорды |
|------|---------|
| Люкс-отель | Fresh, Powdery, Clean, Citrus |
| Лето в Европе | Citrus, Fresh, Aquatic, Fruity |
| Мафия и роскошь | Leather, Tobacco, Spicy, Resinous |
| Пустыня в полночь | Resinous, Spicy, Oriental, Smoky |
| Вторая кожа | Musky, Clean, Powdery, Soft |
| Богатство без логотипов | Powdery, Iris, Woody, Musky |
| …и ещё 24 вайба | … |

---

### 4. Уточнение (sub_type) — +3 балла за каждый совпавший аккорд

Второй вопрос внутри ветки. Уточняет характер аромата.

Примеры:
| Sub_type | Аккорды |
|----------|---------|
| Морская свежесть | Marine, Aquatic |
| Ваниль и крем | Vanilla, Sweet, Gourmand |
| Кожа | Leathery, Animal |
| Тихая роскошь | Powdery, Woody, Clean |
| Дерево и смолы | Woody, Resinous, Balsamic |

---

### 5. Повод — +2 балла за каждый совпавший аккорд

| Повод | Аккорды |
|-------|---------|
| Каждый день | Fresh, Clean, Citrus, Aromatic |
| Офис / работа | Fresh, Powdery, Clean, Woody |
| Свидание | Oriental, Amber, Floral, Musky |
| Вечеринка | Spicy, Oriental, Fruity, Smoky |
| Осень/зима | Warm, Spicy, Woody, Amber |
| Уютный вечер | Vanilla, Warm, Gourmand, Amber |
| Спорт | Fresh, Citrus, Aquatic, Aromatic |

---

## Жёсткий фильтр — Бюджет

Применяется **до** показа результатов. Парфюмы вне выбранного диапазона **отсекаются полностью**, не важно какой у них score.

| Магазин | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---------|--------|--------|--------|--------|
| Parfbar | 0–2 500 ₽ | 2 500–4 000 ₽ | 4 000–6 000 ₽ | 6 000+ ₽ |
| Profumum | 0–15 000 ₽ | 15–30k ₽ | 30–50k ₽ | 50 000+ ₽ |

---

## Итоговая формула

```
score = баллы_направление + баллы_ноты + баллы_вайб + баллы_sub_type + баллы_повод
```

Парфюмы с `score <= 0` не показываются. Из оставшихся (прошедших фильтр бюджета) берётся топ-5.

---

## Источники данных

- **Аккорды** — из базы 76k парфюмов (`fragrances_db.json`), матч по названию бренд+имя
- **Ноты** — из каталога магазина (`fragrances_parfbar.json` / `fragrances_profumum.json`) + база 76k
- Если аромат не найден в базе 76k — аккорды недоступны, score формируется только по нотам
