SELECT
	m.sales_order_id,
	p.product_desc as Материал,
	m.Допуск,
    m.Требуемые_ресурсы,
    m.Требуемая_мощность,
 	m.Дата_начала,
 	m.Дата_завершения
FROM
	mrp m
LEFT JOIN 
	Sales_Orders so
	ON m.sales_order_id = so.sales_order_id
INNER JOIN
	Product p 
 	ON p.product_id = so.product_id
ORDER BY
	m.sales_order_id ASC;