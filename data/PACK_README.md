# PS-053 – Marketplace Seller Rating and Penalty Engine with Performance Tiers — Sample Data Pack

Prepared by 10 SECONDS for Team T092.

Domain: Commerce — Marketplace Operations. Build the seller performance engine a marketplace uses to compute weekly metrics for every seller (late shipment rate, cancellation rate, return rate, response time, rating), assign performance tiers that change commission and visibility, levy penalties with caps and appeals, and run suspension and reinstatement as a state machine. Seller support teams use it to answer why a seller was downgraded. Command-file driven; no UI.

## Files

| File | What it holds | Rows |
|---|---|---|
| `sellers.csv` | Seller master as at 2026-08-03 | 30 |
| `orders_week_01.csv` | Orders placed in week 1 (2026-08-03 to 2026-08-09) with their full lifecycle | 179 |
| `messages_week_01.csv` | Buyer messages and seller replies for week 1 orders | 38 |
| `orders_week_02.csv` | Orders placed in week 2 (2026-08-10 to 2026-08-16) with their full lifecycle | 180 |
| `messages_week_02.csv` | Buyer messages and seller replies for week 2 orders | 36 |
| `orders_week_03.csv` | Orders placed in week 3 (2026-08-17 to 2026-08-23) with their full lifecycle | 235 |
| `messages_week_03.csv` | Buyer messages and seller replies for week 3 orders | 41 |
| `orders_week_04.csv` | Orders placed in week 4 (2026-08-24 to 2026-08-30) with their full lifecycle | 175 |
| `messages_week_04.csv` | Buyer messages and seller replies for week 4 orders | 29 |
| `orders_week_05.csv` | Orders placed in week 5 (2026-08-31 to 2026-09-06) with their full lifecycle | 134 |
| `messages_week_05.csv` | Buyer messages and seller replies for week 5 orders | 24 |
| `orders_week_06.csv` | Orders placed in week 6 (2026-09-07 to 2026-09-13) with their full lifecycle | 204 |
| `messages_week_06.csv` | Buyer messages and seller replies for week 6 orders | 42 |
| `orders_week_07.csv` | Orders placed in week 7 (2026-09-14 to 2026-09-20) with their full lifecycle | 133 |
| `messages_week_07.csv` | Buyer messages and seller replies for week 7 orders | 28 |
| `orders_week_08.csv` | Orders placed in week 8 (2026-09-21 to 2026-09-27) with their full lifecycle | 123 |
| `messages_week_08.csv` | Buyer messages and seller replies for week 8 orders | 22 |
| `orders_week_09.csv` | Orders placed in week 9 (2026-09-28 to 2026-10-04) with their full lifecycle | 93 |
| `messages_week_09.csv` | Buyer messages and seller replies for week 9 orders | 15 |
| `orders_week_10.csv` | Orders placed in week 10 (2026-10-05 to 2026-10-11) with their full lifecycle | 126 |
| `messages_week_10.csv` | Buyer messages and seller replies for week 10 orders | 25 |
| `orders_week_11.csv` | Orders placed in week 11 (2026-10-12 to 2026-10-18) with their full lifecycle | 86 |
| `messages_week_11.csv` | Buyer messages and seller replies for week 11 orders | 11 |
| `orders_week_12.csv` | Orders placed in week 12 (2026-10-19 to 2026-10-25) with their full lifecycle | 86 |
| `messages_week_12.csv` | Buyer messages and seller replies for week 12 orders | 18 |
| `courier_events.csv` | Courier confirmations used to auto-decide appeals | 19 |
| `commands.txt` | Command file; process strictly in file order. | 83 |

Volumes in this sample are reduced for email delivery; the hidden evaluation set is larger and uses the same schema.

Row counts exclude the header line (CSV) and comment lines (commands.txt).

## Column reference

Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals with at most 2 decimals (no commas, no symbol); percentages as plain numbers (12.5 = 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix.

### `sellers.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `seller_id` | string | SEL-nnn |  | Primary key |
| `seller_name` | string |  |  |  |
| `category` | enum |  | Electronics/Fashion/Home/Grocery | Fashion return threshold is 10% |
| `join_date` | date |  |  | New seller = fewer than 8 weeks before the review Monday |
| `current_tier` | enum |  | PLATINUM/GOLD/SILVER/WATCH | Tier at the start of week 1 |
| `prior_suspension_date` | date |  | may be empty | Date of an earlier suspension (6-month termination rule) |
| `prior_penalty_total` | decimal | Rs | >=0 | Informational |

### `orders_week_01.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `order_id` | string | ORD-nnnnnn |  | Unique across all weeks except one planted duplicate |
| `seller_id` | string |  | sellers.csv | FK |
| `order_ts` | timestamp |  |  | Order placed |
| `category` | enum |  |  | Seller category copied |
| `gmv` | decimal | Rs | >0 | Order value; weekly GMV = sum over the week's orders |
| `prepaid` | boolean |  | true/false | Seller cancellation of a prepaid order = Rs 200 |
| `promised_ship_date` | date |  |  | Shipment is late if shipped after this date (see weekend exception) |
| `shipped_ts` | timestamp |  | may be empty | Empty when cancelled |
| `cancelled_ts` | timestamp |  | may be empty |  |
| `cancelled_by` | enum |  | SELLER/BUYER or empty |  |
| `cancel_reason` | enum |  | OUT_OF_STOCK/PRICE_ERROR/DAMAGED_IN_WAREHOUSE/BUYER_REQUEST/ADDRESS_UNSERVICEABLE/CHANGED_MIND or empty | BUYER_REQUEST and ADDRESS_UNSERVICEABLE are excluded from SCR |
| `delivered_ts` | timestamp |  | may be empty | Delivered orders form the return-rate denominator |
| `return_reason` | enum |  | DEFECTIVE/NOT_AS_DESCRIBED/WRONG_ITEM/CHANGED_MIND or empty |  |
| `rating` | integer | stars | 1–5 or empty (one invalid 6 planted) |  |

### `messages_week_01.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `message_id` | string | MSG-nnnnnn |  |  |
| `order_id` | string |  | same week's orders file | FK |
| `seller_id` | string |  | sellers.csv | FK |
| `buyer_msg_ts` | timestamp |  |  | Only messages between 09:00:00 and 21:00:00 inclusive count |
| `seller_reply_ts` | timestamp |  | may be empty | Empty = never replied (treat as > 24 h breach) |

### `orders_week_02.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `order_id` | string | ORD-nnnnnn |  | Unique across all weeks except one planted duplicate |
| `seller_id` | string |  | sellers.csv | FK |
| `order_ts` | timestamp |  |  | Order placed |
| `category` | enum |  |  | Seller category copied |
| `gmv` | decimal | Rs | >0 | Order value; weekly GMV = sum over the week's orders |
| `prepaid` | boolean |  | true/false | Seller cancellation of a prepaid order = Rs 200 |
| `promised_ship_date` | date |  |  | Shipment is late if shipped after this date (see weekend exception) |
| `shipped_ts` | timestamp |  | may be empty | Empty when cancelled |
| `cancelled_ts` | timestamp |  | may be empty |  |
| `cancelled_by` | enum |  | SELLER/BUYER or empty |  |
| `cancel_reason` | enum |  | OUT_OF_STOCK/PRICE_ERROR/DAMAGED_IN_WAREHOUSE/BUYER_REQUEST/ADDRESS_UNSERVICEABLE/CHANGED_MIND or empty | BUYER_REQUEST and ADDRESS_UNSERVICEABLE are excluded from SCR |
| `delivered_ts` | timestamp |  | may be empty | Delivered orders form the return-rate denominator |
| `return_reason` | enum |  | DEFECTIVE/NOT_AS_DESCRIBED/WRONG_ITEM/CHANGED_MIND or empty |  |
| `rating` | integer | stars | 1–5 or empty (one invalid 6 planted) |  |

### `messages_week_02.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `message_id` | string | MSG-nnnnnn |  |  |
| `order_id` | string |  | same week's orders file | FK |
| `seller_id` | string |  | sellers.csv | FK |
| `buyer_msg_ts` | timestamp |  |  | Only messages between 09:00:00 and 21:00:00 inclusive count |
| `seller_reply_ts` | timestamp |  | may be empty | Empty = never replied (treat as > 24 h breach) |

### `orders_week_03.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `order_id` | string | ORD-nnnnnn |  | Unique across all weeks except one planted duplicate |
| `seller_id` | string |  | sellers.csv | FK |
| `order_ts` | timestamp |  |  | Order placed |
| `category` | enum |  |  | Seller category copied |
| `gmv` | decimal | Rs | >0 | Order value; weekly GMV = sum over the week's orders |
| `prepaid` | boolean |  | true/false | Seller cancellation of a prepaid order = Rs 200 |
| `promised_ship_date` | date |  |  | Shipment is late if shipped after this date (see weekend exception) |
| `shipped_ts` | timestamp |  | may be empty | Empty when cancelled |
| `cancelled_ts` | timestamp |  | may be empty |  |
| `cancelled_by` | enum |  | SELLER/BUYER or empty |  |
| `cancel_reason` | enum |  | OUT_OF_STOCK/PRICE_ERROR/DAMAGED_IN_WAREHOUSE/BUYER_REQUEST/ADDRESS_UNSERVICEABLE/CHANGED_MIND or empty | BUYER_REQUEST and ADDRESS_UNSERVICEABLE are excluded from SCR |
| `delivered_ts` | timestamp |  | may be empty | Delivered orders form the return-rate denominator |
| `return_reason` | enum |  | DEFECTIVE/NOT_AS_DESCRIBED/WRONG_ITEM/CHANGED_MIND or empty |  |
| `rating` | integer | stars | 1–5 or empty (one invalid 6 planted) |  |

### `messages_week_03.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `message_id` | string | MSG-nnnnnn |  |  |
| `order_id` | string |  | same week's orders file | FK |
| `seller_id` | string |  | sellers.csv | FK |
| `buyer_msg_ts` | timestamp |  |  | Only messages between 09:00:00 and 21:00:00 inclusive count |
| `seller_reply_ts` | timestamp |  | may be empty | Empty = never replied (treat as > 24 h breach) |

### `orders_week_04.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `order_id` | string | ORD-nnnnnn |  | Unique across all weeks except one planted duplicate |
| `seller_id` | string |  | sellers.csv | FK |
| `order_ts` | timestamp |  |  | Order placed |
| `category` | enum |  |  | Seller category copied |
| `gmv` | decimal | Rs | >0 | Order value; weekly GMV = sum over the week's orders |
| `prepaid` | boolean |  | true/false | Seller cancellation of a prepaid order = Rs 200 |
| `promised_ship_date` | date |  |  | Shipment is late if shipped after this date (see weekend exception) |
| `shipped_ts` | timestamp |  | may be empty | Empty when cancelled |
| `cancelled_ts` | timestamp |  | may be empty |  |
| `cancelled_by` | enum |  | SELLER/BUYER or empty |  |
| `cancel_reason` | enum |  | OUT_OF_STOCK/PRICE_ERROR/DAMAGED_IN_WAREHOUSE/BUYER_REQUEST/ADDRESS_UNSERVICEABLE/CHANGED_MIND or empty | BUYER_REQUEST and ADDRESS_UNSERVICEABLE are excluded from SCR |
| `delivered_ts` | timestamp |  | may be empty | Delivered orders form the return-rate denominator |
| `return_reason` | enum |  | DEFECTIVE/NOT_AS_DESCRIBED/WRONG_ITEM/CHANGED_MIND or empty |  |
| `rating` | integer | stars | 1–5 or empty (one invalid 6 planted) |  |

### `messages_week_04.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `message_id` | string | MSG-nnnnnn |  |  |
| `order_id` | string |  | same week's orders file | FK |
| `seller_id` | string |  | sellers.csv | FK |
| `buyer_msg_ts` | timestamp |  |  | Only messages between 09:00:00 and 21:00:00 inclusive count |
| `seller_reply_ts` | timestamp |  | may be empty | Empty = never replied (treat as > 24 h breach) |

### `orders_week_05.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `order_id` | string | ORD-nnnnnn |  | Unique across all weeks except one planted duplicate |
| `seller_id` | string |  | sellers.csv | FK |
| `order_ts` | timestamp |  |  | Order placed |
| `category` | enum |  |  | Seller category copied |
| `gmv` | decimal | Rs | >0 | Order value; weekly GMV = sum over the week's orders |
| `prepaid` | boolean |  | true/false | Seller cancellation of a prepaid order = Rs 200 |
| `promised_ship_date` | date |  |  | Shipment is late if shipped after this date (see weekend exception) |
| `shipped_ts` | timestamp |  | may be empty | Empty when cancelled |
| `cancelled_ts` | timestamp |  | may be empty |  |
| `cancelled_by` | enum |  | SELLER/BUYER or empty |  |
| `cancel_reason` | enum |  | OUT_OF_STOCK/PRICE_ERROR/DAMAGED_IN_WAREHOUSE/BUYER_REQUEST/ADDRESS_UNSERVICEABLE/CHANGED_MIND or empty | BUYER_REQUEST and ADDRESS_UNSERVICEABLE are excluded from SCR |
| `delivered_ts` | timestamp |  | may be empty | Delivered orders form the return-rate denominator |
| `return_reason` | enum |  | DEFECTIVE/NOT_AS_DESCRIBED/WRONG_ITEM/CHANGED_MIND or empty |  |
| `rating` | integer | stars | 1–5 or empty (one invalid 6 planted) |  |

### `messages_week_05.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `message_id` | string | MSG-nnnnnn |  |  |
| `order_id` | string |  | same week's orders file | FK |
| `seller_id` | string |  | sellers.csv | FK |
| `buyer_msg_ts` | timestamp |  |  | Only messages between 09:00:00 and 21:00:00 inclusive count |
| `seller_reply_ts` | timestamp |  | may be empty | Empty = never replied (treat as > 24 h breach) |

### `orders_week_06.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `order_id` | string | ORD-nnnnnn |  | Unique across all weeks except one planted duplicate |
| `seller_id` | string |  | sellers.csv | FK |
| `order_ts` | timestamp |  |  | Order placed |
| `category` | enum |  |  | Seller category copied |
| `gmv` | decimal | Rs | >0 | Order value; weekly GMV = sum over the week's orders |
| `prepaid` | boolean |  | true/false | Seller cancellation of a prepaid order = Rs 200 |
| `promised_ship_date` | date |  |  | Shipment is late if shipped after this date (see weekend exception) |
| `shipped_ts` | timestamp |  | may be empty | Empty when cancelled |
| `cancelled_ts` | timestamp |  | may be empty |  |
| `cancelled_by` | enum |  | SELLER/BUYER or empty |  |
| `cancel_reason` | enum |  | OUT_OF_STOCK/PRICE_ERROR/DAMAGED_IN_WAREHOUSE/BUYER_REQUEST/ADDRESS_UNSERVICEABLE/CHANGED_MIND or empty | BUYER_REQUEST and ADDRESS_UNSERVICEABLE are excluded from SCR |
| `delivered_ts` | timestamp |  | may be empty | Delivered orders form the return-rate denominator |
| `return_reason` | enum |  | DEFECTIVE/NOT_AS_DESCRIBED/WRONG_ITEM/CHANGED_MIND or empty |  |
| `rating` | integer | stars | 1–5 or empty (one invalid 6 planted) |  |

### `messages_week_06.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `message_id` | string | MSG-nnnnnn |  |  |
| `order_id` | string |  | same week's orders file | FK |
| `seller_id` | string |  | sellers.csv | FK |
| `buyer_msg_ts` | timestamp |  |  | Only messages between 09:00:00 and 21:00:00 inclusive count |
| `seller_reply_ts` | timestamp |  | may be empty | Empty = never replied (treat as > 24 h breach) |

### `orders_week_07.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `order_id` | string | ORD-nnnnnn |  | Unique across all weeks except one planted duplicate |
| `seller_id` | string |  | sellers.csv | FK |
| `order_ts` | timestamp |  |  | Order placed |
| `category` | enum |  |  | Seller category copied |
| `gmv` | decimal | Rs | >0 | Order value; weekly GMV = sum over the week's orders |
| `prepaid` | boolean |  | true/false | Seller cancellation of a prepaid order = Rs 200 |
| `promised_ship_date` | date |  |  | Shipment is late if shipped after this date (see weekend exception) |
| `shipped_ts` | timestamp |  | may be empty | Empty when cancelled |
| `cancelled_ts` | timestamp |  | may be empty |  |
| `cancelled_by` | enum |  | SELLER/BUYER or empty |  |
| `cancel_reason` | enum |  | OUT_OF_STOCK/PRICE_ERROR/DAMAGED_IN_WAREHOUSE/BUYER_REQUEST/ADDRESS_UNSERVICEABLE/CHANGED_MIND or empty | BUYER_REQUEST and ADDRESS_UNSERVICEABLE are excluded from SCR |
| `delivered_ts` | timestamp |  | may be empty | Delivered orders form the return-rate denominator |
| `return_reason` | enum |  | DEFECTIVE/NOT_AS_DESCRIBED/WRONG_ITEM/CHANGED_MIND or empty |  |
| `rating` | integer | stars | 1–5 or empty (one invalid 6 planted) |  |

### `messages_week_07.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `message_id` | string | MSG-nnnnnn |  |  |
| `order_id` | string |  | same week's orders file | FK |
| `seller_id` | string |  | sellers.csv | FK |
| `buyer_msg_ts` | timestamp |  |  | Only messages between 09:00:00 and 21:00:00 inclusive count |
| `seller_reply_ts` | timestamp |  | may be empty | Empty = never replied (treat as > 24 h breach) |

### `orders_week_08.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `order_id` | string | ORD-nnnnnn |  | Unique across all weeks except one planted duplicate |
| `seller_id` | string |  | sellers.csv | FK |
| `order_ts` | timestamp |  |  | Order placed |
| `category` | enum |  |  | Seller category copied |
| `gmv` | decimal | Rs | >0 | Order value; weekly GMV = sum over the week's orders |
| `prepaid` | boolean |  | true/false | Seller cancellation of a prepaid order = Rs 200 |
| `promised_ship_date` | date |  |  | Shipment is late if shipped after this date (see weekend exception) |
| `shipped_ts` | timestamp |  | may be empty | Empty when cancelled |
| `cancelled_ts` | timestamp |  | may be empty |  |
| `cancelled_by` | enum |  | SELLER/BUYER or empty |  |
| `cancel_reason` | enum |  | OUT_OF_STOCK/PRICE_ERROR/DAMAGED_IN_WAREHOUSE/BUYER_REQUEST/ADDRESS_UNSERVICEABLE/CHANGED_MIND or empty | BUYER_REQUEST and ADDRESS_UNSERVICEABLE are excluded from SCR |
| `delivered_ts` | timestamp |  | may be empty | Delivered orders form the return-rate denominator |
| `return_reason` | enum |  | DEFECTIVE/NOT_AS_DESCRIBED/WRONG_ITEM/CHANGED_MIND or empty |  |
| `rating` | integer | stars | 1–5 or empty (one invalid 6 planted) |  |

### `messages_week_08.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `message_id` | string | MSG-nnnnnn |  |  |
| `order_id` | string |  | same week's orders file | FK |
| `seller_id` | string |  | sellers.csv | FK |
| `buyer_msg_ts` | timestamp |  |  | Only messages between 09:00:00 and 21:00:00 inclusive count |
| `seller_reply_ts` | timestamp |  | may be empty | Empty = never replied (treat as > 24 h breach) |

### `orders_week_09.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `order_id` | string | ORD-nnnnnn |  | Unique across all weeks except one planted duplicate |
| `seller_id` | string |  | sellers.csv | FK |
| `order_ts` | timestamp |  |  | Order placed |
| `category` | enum |  |  | Seller category copied |
| `gmv` | decimal | Rs | >0 | Order value; weekly GMV = sum over the week's orders |
| `prepaid` | boolean |  | true/false | Seller cancellation of a prepaid order = Rs 200 |
| `promised_ship_date` | date |  |  | Shipment is late if shipped after this date (see weekend exception) |
| `shipped_ts` | timestamp |  | may be empty | Empty when cancelled |
| `cancelled_ts` | timestamp |  | may be empty |  |
| `cancelled_by` | enum |  | SELLER/BUYER or empty |  |
| `cancel_reason` | enum |  | OUT_OF_STOCK/PRICE_ERROR/DAMAGED_IN_WAREHOUSE/BUYER_REQUEST/ADDRESS_UNSERVICEABLE/CHANGED_MIND or empty | BUYER_REQUEST and ADDRESS_UNSERVICEABLE are excluded from SCR |
| `delivered_ts` | timestamp |  | may be empty | Delivered orders form the return-rate denominator |
| `return_reason` | enum |  | DEFECTIVE/NOT_AS_DESCRIBED/WRONG_ITEM/CHANGED_MIND or empty |  |
| `rating` | integer | stars | 1–5 or empty (one invalid 6 planted) |  |

### `messages_week_09.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `message_id` | string | MSG-nnnnnn |  |  |
| `order_id` | string |  | same week's orders file | FK |
| `seller_id` | string |  | sellers.csv | FK |
| `buyer_msg_ts` | timestamp |  |  | Only messages between 09:00:00 and 21:00:00 inclusive count |
| `seller_reply_ts` | timestamp |  | may be empty | Empty = never replied (treat as > 24 h breach) |

### `orders_week_10.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `order_id` | string | ORD-nnnnnn |  | Unique across all weeks except one planted duplicate |
| `seller_id` | string |  | sellers.csv | FK |
| `order_ts` | timestamp |  |  | Order placed |
| `category` | enum |  |  | Seller category copied |
| `gmv` | decimal | Rs | >0 | Order value; weekly GMV = sum over the week's orders |
| `prepaid` | boolean |  | true/false | Seller cancellation of a prepaid order = Rs 200 |
| `promised_ship_date` | date |  |  | Shipment is late if shipped after this date (see weekend exception) |
| `shipped_ts` | timestamp |  | may be empty | Empty when cancelled |
| `cancelled_ts` | timestamp |  | may be empty |  |
| `cancelled_by` | enum |  | SELLER/BUYER or empty |  |
| `cancel_reason` | enum |  | OUT_OF_STOCK/PRICE_ERROR/DAMAGED_IN_WAREHOUSE/BUYER_REQUEST/ADDRESS_UNSERVICEABLE/CHANGED_MIND or empty | BUYER_REQUEST and ADDRESS_UNSERVICEABLE are excluded from SCR |
| `delivered_ts` | timestamp |  | may be empty | Delivered orders form the return-rate denominator |
| `return_reason` | enum |  | DEFECTIVE/NOT_AS_DESCRIBED/WRONG_ITEM/CHANGED_MIND or empty |  |
| `rating` | integer | stars | 1–5 or empty (one invalid 6 planted) |  |

### `messages_week_10.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `message_id` | string | MSG-nnnnnn |  |  |
| `order_id` | string |  | same week's orders file | FK |
| `seller_id` | string |  | sellers.csv | FK |
| `buyer_msg_ts` | timestamp |  |  | Only messages between 09:00:00 and 21:00:00 inclusive count |
| `seller_reply_ts` | timestamp |  | may be empty | Empty = never replied (treat as > 24 h breach) |

### `orders_week_11.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `order_id` | string | ORD-nnnnnn |  | Unique across all weeks except one planted duplicate |
| `seller_id` | string |  | sellers.csv | FK |
| `order_ts` | timestamp |  |  | Order placed |
| `category` | enum |  |  | Seller category copied |
| `gmv` | decimal | Rs | >0 | Order value; weekly GMV = sum over the week's orders |
| `prepaid` | boolean |  | true/false | Seller cancellation of a prepaid order = Rs 200 |
| `promised_ship_date` | date |  |  | Shipment is late if shipped after this date (see weekend exception) |
| `shipped_ts` | timestamp |  | may be empty | Empty when cancelled |
| `cancelled_ts` | timestamp |  | may be empty |  |
| `cancelled_by` | enum |  | SELLER/BUYER or empty |  |
| `cancel_reason` | enum |  | OUT_OF_STOCK/PRICE_ERROR/DAMAGED_IN_WAREHOUSE/BUYER_REQUEST/ADDRESS_UNSERVICEABLE/CHANGED_MIND or empty | BUYER_REQUEST and ADDRESS_UNSERVICEABLE are excluded from SCR |
| `delivered_ts` | timestamp |  | may be empty | Delivered orders form the return-rate denominator |
| `return_reason` | enum |  | DEFECTIVE/NOT_AS_DESCRIBED/WRONG_ITEM/CHANGED_MIND or empty |  |
| `rating` | integer | stars | 1–5 or empty (one invalid 6 planted) |  |

### `messages_week_11.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `message_id` | string | MSG-nnnnnn |  |  |
| `order_id` | string |  | same week's orders file | FK |
| `seller_id` | string |  | sellers.csv | FK |
| `buyer_msg_ts` | timestamp |  |  | Only messages between 09:00:00 and 21:00:00 inclusive count |
| `seller_reply_ts` | timestamp |  | may be empty | Empty = never replied (treat as > 24 h breach) |

### `orders_week_12.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `order_id` | string | ORD-nnnnnn |  | Unique across all weeks except one planted duplicate |
| `seller_id` | string |  | sellers.csv | FK |
| `order_ts` | timestamp |  |  | Order placed |
| `category` | enum |  |  | Seller category copied |
| `gmv` | decimal | Rs | >0 | Order value; weekly GMV = sum over the week's orders |
| `prepaid` | boolean |  | true/false | Seller cancellation of a prepaid order = Rs 200 |
| `promised_ship_date` | date |  |  | Shipment is late if shipped after this date (see weekend exception) |
| `shipped_ts` | timestamp |  | may be empty | Empty when cancelled |
| `cancelled_ts` | timestamp |  | may be empty |  |
| `cancelled_by` | enum |  | SELLER/BUYER or empty |  |
| `cancel_reason` | enum |  | OUT_OF_STOCK/PRICE_ERROR/DAMAGED_IN_WAREHOUSE/BUYER_REQUEST/ADDRESS_UNSERVICEABLE/CHANGED_MIND or empty | BUYER_REQUEST and ADDRESS_UNSERVICEABLE are excluded from SCR |
| `delivered_ts` | timestamp |  | may be empty | Delivered orders form the return-rate denominator |
| `return_reason` | enum |  | DEFECTIVE/NOT_AS_DESCRIBED/WRONG_ITEM/CHANGED_MIND or empty |  |
| `rating` | integer | stars | 1–5 or empty (one invalid 6 planted) |  |

### `messages_week_12.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `message_id` | string | MSG-nnnnnn |  |  |
| `order_id` | string |  | same week's orders file | FK |
| `seller_id` | string |  | sellers.csv | FK |
| `buyer_msg_ts` | timestamp |  |  | Only messages between 09:00:00 and 21:00:00 inclusive count |
| `seller_reply_ts` | timestamp |  | may be empty | Empty = never replied (treat as > 24 h breach) |

### `courier_events.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| `courier_event_id` | string | CEV-nnnn |  |  |
| `order_id` | string |  |  | Not every order has an event |
| `event_ts` | timestamp |  |  | When the courier logged it — an appeal auto-succeeds only if this is on or before the appeal decision date |
| `event_type` | enum |  | PICKUP_FAILED/WEATHER_DELAY/PICKED_UP | PICKUP_FAILED and WEATHER_DELAY confirm appeals |
| `note` | string |  |  |  |

### General notes

- Weeks run Monday–Sunday; week 1 is 2026-08-03 to 2026-08-09. Each orders file holds the orders PLACED in that week with their whole lifecycle; attribute each event (ship, cancel, deliver, return, rating) to the week containing its own timestamp when computing trailing windows.
- Where the brief is silent: metrics are computed at the review Monday over the trailing N completed weeks; a seller with no orders in a week has that week's metrics as 0 and no tier change.

## Command file format

`commands.txt` holds one command per line in the form `COMMAND_NAME|arg1|arg2|...`. Commands MUST be processed strictly in file order. Lines starting with `#` are comments and blank lines are ignored. Every command used in this pack, with its argument order:

| Command | Arguments (in order) | Meaning |
|---|---|---|
| `LOAD_SELLERS` | `file` | Load seller master |
| `LOAD_COURIER_EVENTS` | `file` | Load courier confirmations |
| `PROCESS_WEEK` | `week_no|orders_file|messages_file` | Ingest the week's orders and messages |
| `REVIEW_TIERS` | `monday_date` | Compute trailing metrics, tiers, penalties and state transitions as of that Monday for the week just closed |
| `APPEAL` | `appeal_id|filed_date|seller_id|order_id|reason|evidence_flag` | Seller appeals the penalty on that order |
| `DECIDE_APPEAL` | `appeal_id|decision_date|ACCEPTED or REJECTED|note` | Manual decision for appeals that cannot auto-succeed |
| `REINSTATE` | `date|seller_id` | Reinstate a SUSPENDED seller (>= 14 days) into PROBATION |
| `COUNTERFEIT_CONFIRMED` | `date|seller_id|order_id` | Confirmed counterfeit report |
| `PRINT_SCORECARD` | `seller_id` | Append the seller's 12 weekly rows to scorecards.csv |
| `PRINT_PENALTY_LEDGER` | `` | Write penalty_ledger.csv |
| `PRINT_STATES` | `` | Write state_transitions.csv |

## Planted scenarios

Every edge case from the brief is planted at the location given. Line numbers count the header as line 1 for CSVs and count every physical line (including comments) for commands.txt.

- **EC1: Seller with exactly 20 shipped orders in the 4-week window** — SEL-021 ships exactly 5 orders in each of weeks 1–4 (20 shipped in the trailing 4-week window at the 2026-08-31 review → LSR IS evaluated) and 4 per week after, so at the 2026-09-07 review the window holds 19 → not evaluated on LSR
- **EC2: Shipment on Saturday exactly 24 hours after a Friday promise** — orders_week_01.csv ORD-000178 (line 48): promised_ship_date 2026-08-07 (Friday), shipped_ts 2026-08-08 23:59:59 (Saturday, exactly 24 h after the end of the promised day → NOT late under the weekend rule); orders_week_01.csv ORD-000179 (line 49) shipped 2026-08-09 00:00:00 → late. State your interpretation of the promise instant in your README.
- **EC3: SCR exactly 2.5% with one BUYER_REQUEST cancellation** — SEL-022 weeks 1–4: exactly 200 orders, 5 cancelled by SELLER (OUT_OF_STOCK/PRICE_ERROR) and 1 with reason BUYER_REQUEST → SCR = 5/200 = 2.5% exactly at the 2026-08-31 review (the BUYER_REQUEST row is excluded; 2.5% is not < 2.5%, so GOLD fails)
- **EC4: Fashion seller with return rate exactly 10%** — SEL-023 (Fashion) weeks 1–8: exactly 300 delivered orders and 30 returns with qualifying reasons (plus 4 CHANGED_MIND, excluded) → return rate 10.00% at the 2026-09-28 review; Fashion threshold is 10%
- **EC5: Seller eligible for PLATINUM from WATCH (one step up only)** — SEL-024 starts in WATCH (sellers.csv current_tier) with perfect metrics every week → may rise only one step per review: SILVER on 2026-08-10, GOLD on 2026-08-17, PLATINUM on 2026-08-24
- **EC6: Weekly penalties where 5% of GMV is below Rs 5,000** — SEL-025 week 6 (orders_week_06.csv): 80 shipped orders of exactly 750.00 each (GMV 60,000.00), 70 late → late penalty 67 x 50 = 3,350 but the cap is min(5,000, 5% x 60,000 = 3,000) → 3,000 levied
- **EC7: Appeal filed on day 7 with courier confirmation arriving on day 8** — commands.txt line 18: APPEAL filed 2026-09-14 (day 7 after the 2026-09-07 penalty) for order ORD-000898; courier_events.csv confirms PICKUP_FAILED only on 2026-09-15 (day 8) → the appeal is timely but the confirmation arrives after filing; auto-success applies when the confirmation exists at decision time (document your decision date)
- **EC8: Second suspension exactly 6 months after the first** — SEL-026 has prior_suspension_date 2026-04-12; week 10 has 6 seller cancellations out of 40 (15% > 10%) → suspension at the review on 2026-10-12 (commands.txt line 48), exactly 6 months after the first → decide whether 'within 6 months' includes the boundary and TERMINATE or SUSPEND accordingly
- **Extra: suspension and reinstatement to PROBATION** — SEL-027 week 3: 8 of 60 orders cancelled by seller (13.3%) → SUSPENDED at the 2026-08-24 review; REINSTATE on 2026-09-07 (commands.txt line 28, 14 days later) → PROBATION for 4 weeks with doubled penalties and tier capped at SILVER
- **Extra: new seller capped at GOLD** — SEL-028 joined 2026-07-27 with perfect metrics → capped at GOLD until the first review at or after 2026-09-21 (8 weeks)
- **Extra: counterfeit** — commands.txt lines 31 and 44: COUNTERFEIT_CONFIRMED for SEL-029 and SEL-012 → Rs 25,000 penalty exempt from the weekly cap and immediate SUSPENDED
- **Extra: appeal filed on day 8** — commands.txt line 19: appeal filed 8 days after the penalty → REJECTED_LATE even though courier_events.csv confirms the pickup failure
- **Extra: message window boundary** — messages_week_01.csv MSG-000036 buyer message at 21:00:00 (counts) and MSG-000037 at 21:00:01 (does not count); MSG-000038 has no reply → counts as a > 24 h breach
- **Extra: invalid rows** — orders_week_02.csv ORD-000357 (line 75) shipped_ts is before order_ts → reject row INVALID_SEQUENCE; orders_week_02.csv ORD-000358 (line 14) rating 6 → ignore the rating, keep the order; orders_week_02.csv ORD-000190 appears on lines 80 and 81 with identical fields (duplicate) → process once
- **Extra: weekly cap vs appeal reversal** — SEL-004 week 5 has 6 late shipments; 4 have courier PICKUP_FAILED confirmations before the appeal → those appeals auto-succeed, reverse the penalty and exclude the orders from LSR

## What is NOT in this pack

Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-nn). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation

Produce these files (CSV, header row, same conventions as above, rows in the order stated). Numeric columns must be plain decimals with exactly the decimals stated.

### `scorecards.csv`

One row per seller per review (12 per seller), ordered by seller_id then week_no.

Columns in order: `seller_id`, `week_no`, `review_date`, `shipped_4w`, `lsr_pct`, `lsr_evaluated`, `scr_pct`, `return_rate_pct`, `median_response_hours`, `avg_rating`, `rating_count`, `breaches`, `tier`, `commission_adj_pp`, `search_boost`, `state`, `week_gmv`, `week_penalty_levied`

### `penalty_ledger.csv`

One row per penalty incident, in levy order.

Columns in order: `penalty_id`, `seller_id`, `week_no`, `order_id`, `penalty_type`, `amount`, `amount_after_cap`, `status`, `appeal_id`, `reversal_date`

### `state_transitions.csv`

Every seller state change in date order.

Columns in order: `seller_id`, `transition_date`, `from_state`, `to_state`, `trigger`
