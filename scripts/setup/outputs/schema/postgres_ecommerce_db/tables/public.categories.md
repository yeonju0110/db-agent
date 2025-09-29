# Table: public.categories

## Columns

| Name | Type | Nullable | PK | FK | Default | Extra | Description |
|---|---|:---:|:--:|:--:|---|---|---|
| id | int4 | NO | Y |  |  |  |  |
| name | varchar | NO |  |  |  |  |  |
| parent_id | int4 | YES |  | Y |  |  |  |
| description | text | YES |  |  |  |  |  |
| display_order | int4 | YES |  |  | 0 |  |  |
| is_active | bool | YES |  |  | true |  |  |
| created_at | timestamptz | YES |  |  | now() |  |  |

## Primary Key

id

## Foreign Keys
- categories_parent_id_fkey: parent_id -> public.categories(id)

## Indexes
- categories_pkey (UNIQUE): id

## Sample Queries

```sql
SELECT * FROM public.categories LIMIT 10;
```

```sql
SELECT * FROM public.categories WHERE id = :id;
```

```sql
SELECT t.* FROM public.categories t JOIN public.categories r ON t.parent_id = r.id LIMIT 10;
```
