-- Database Name: stores.db

/*
   Table Names and their description with connections:
   - customers    : This contains all customers data with 'customerNumber' as it's primary key.
                    Connections: 1. With 'orders' table on 'customerNumber' attribute.
				                 2. With 'payments' table on 'customerNumber'
		                         3. With 'employees' table via it's attribute 'salesRepEmployeeNumber'
   - employees    : This contains all employees information with 'employeeNumber' as it's primary key.
                    Connections: 1. Self referencing connection ON 'employeeNumber' and 'reportsTo' attributes
							     2. 'Offices' table ON 'officeCode' attribute
   - offices      : This contains all sales office info with 'officeCode' as primary key
   - orders       : This contains customer's sales order with 'orderNumber' as primary key
                    Connections: 1. 'orderdetails' table ON orderNumber
   - orderdetails : This contains sales order lines for each sales order with 'orderNumber' as primary key
                    Connections: 1. with 'products' table ON 'productCode' attribute
   - payments     : This contains customers' payment records with 'checkNumber' as primary key
   - products     : This has a list of scale model cars with 'productCode' attribute as primary key
                    Connections: 1. with 'productlines' table over 'productLine' attribute
   - productlines : This is a list of product line categories with 'productLine' as primary key.
*/

-- Identify all tables within the Database
SELECT *
FROM sqlite_master
WHERE type='table';

-- Customers table
SELECT 'Customers' AS table_name,
        COUNT(*) AS number_of_attributes,
		(SELECT COUNT(*) FROM customers) AS number_of_rows
  FROM PRAGMA_TABLE_INFO('customers')

UNION ALL

-- Products table
SELECT 'Products' AS table_name,
        COUNT(*) AS number_of_attributes,
		(SELECT COUNT(*) FROM products) AS number_of_rows
  FROM PRAGMA_TABLE_INFO('products')

UNION ALL

-- ProductLines table
SELECT 'ProductLines' AS table_name,
        COUNT(*) AS number_of_attributes,
		(SELECT COUNT(*) FROM productlines) AS number_of_rows
  FROM PRAGMA_TABLE_INFO('productlines')

UNION ALL

-- Orders table
SELECT 'Orders' AS table_name,
        COUNT(*) AS number_of_attributes,
		(SELECT COUNT(*) FROM orders) AS number_of_rows
  FROM PRAGMA_TABLE_INFO('orders')

UNION ALL

-- OrderDetails table
SELECT 'OrderDetails' AS table_name,
        COUNT(*) AS number_of_attributes,
		(SELECT COUNT(*) FROM orderdetails) AS number_of_rows
  FROM PRAGMA_TABLE_INFO('orderdetails')

UNION ALL

-- Payments table
SELECT 'Payments' AS table_name,
        COUNT(*) AS number_of_attributes,
		(SELECT COUNT(*) FROM payments) AS number_of_rows
  FROM PRAGMA_TABLE_INFO('payments')

UNION ALL

-- Employees table
SELECT 'Employees' AS table_name,
        COUNT(*) AS number_of_attributes,
		(SELECT COUNT(*) FROM employees) AS number_of_rows
  FROM PRAGMA_TABLE_INFO('employees')

UNION ALL

-- Offices table
SELECT 'Offices' AS table_name,
        COUNT(*) AS number_of_attributes,
		(SELECT COUNT(*) FROM offices) AS number_of_rows
  FROM PRAGMA_TABLE_INFO('offices');


-- Question 1: Which Products Should We Order More of or Less of?

-- Low Stock for each product
 SELECT productCode, ROUND((SELECT ROUND(SUM(quantityOrdered)*1.0, 2)
                              FROM orderdetails od
					         WHERE od.productCode = p.productCode) / quantityInStock, 2) AS low_stock
   FROM products p
  GROUP BY productCode
  ORDER BY low_stock DESC
  LIMIT 10;

-- Product Performance for each product
SELECT productCode, SUM(quantityOrdered * priceEach) AS product_performance
  FROM orderdetails od
 GROUP BY productCode
 ORDER BY product_performance DESC
 LIMIT 10;

 /* Priority Products for restocking.
    It is defined as those products which has high product performance that are in the brink of being out of stock (high low stock score) */

/*  CTE (Common Table Expression) will use both the previous
    queries as input to find which product code falls in both the table of high low stock rate and high performance rate */
 WITH
 low_stock_cte AS (
 SELECT productCode, ROUND((SELECT ROUND(SUM(quantityOrdered)*1.0, 2)
                              FROM orderdetails od
					         WHERE od.productCode = p.productCode) / quantityInStock, 2) AS low_stock
   FROM products p
  GROUP BY productCode
  ORDER BY low_stock DESC
  LIMIT 10
 ),
 product_performance_cte AS (
 SELECT productCode, SUM(quantityOrdered * priceEach) AS product_performance
  FROM orderdetails od
 WHERE productCode IN (SELECT productCode FROM low_stock_cte)
 GROUP BY productCode
 ORDER BY product_performance DESC
 LIMIT 10
 )

 -- Main query which calls and use the CTE queries from above
 SELECT productCode, productName, productLine
   FROM products
  WHERE /*productCode IN (SELECT productCode
                          FROM low_stock_cte)
				    AND*/
	    productCode IN (SELECT productCode
                          FROM product_performance_cte);

-- Question 2: How Should We Match Marketing and Communication Strategies to Customer Behavior?

CREATE VIEW CustomersByRevenue AS
SELECT ord.customerNumber,
       c.customerName,
       TRIM(c.contactFirstName) || ' ' || TRIM(c.contactLastName) as contactName,
       c.city,
       c.country,
       ROUND(SUM(ord_dts.quantityOrdered * (ord_dts.priceEach - p.buyPrice)), 2) AS profit
  FROM orders ord
  JOIN orderdetails ord_dts ON ord.orderNumber = ord_dts.orderNumber
  JOIN customers c ON ord.customerNumber = c.customerNumber
  JOIN products p ON ord_dts.productCode = p.productCode
 GROUP BY ord.customerNumber;

-- Top 5 Customers
SELECT *
  FROM CustomersByRevenue c_rev
 ORDER BY profit DESC
 LIMIT 5;

-- Bottom 5 Customers
SELECT *
  FROM CustomersByRevenue c_rev
 ORDER BY profit ASC
 LIMIT 5;

-- Question 3: How Much Can We Spend on Acquiring New Customers?

-- New Customers in the Period:
WITH

payment_with_year_month_table AS (
SELECT *,
       CAST(SUBSTR(paymentDate, 1,4) AS INTEGER)*100 + CAST(SUBSTR(paymentDate, 6,7) AS INTEGER) AS year_month
  FROM payments p
),

customers_by_month_table AS (
SELECT p1.year_month, COUNT(*) AS number_of_customers, SUM(p1.amount) AS total
  FROM payment_with_year_month_table p1
 GROUP BY p1.year_month
),

new_customers_by_month_table AS (
SELECT p1.year_month,
       COUNT(DISTINCT customerNumber) AS number_of_new_customers,
       SUM(p1.amount) AS new_customer_total,
       (SELECT number_of_customers
          FROM customers_by_month_table c
        WHERE c.year_month = p1.year_month) AS number_of_customers,
       (SELECT total
          FROM customers_by_month_table c
         WHERE c.year_month = p1.year_month) AS total
  FROM payment_with_year_month_table p1
 WHERE p1.customerNumber NOT IN (SELECT customerNumber
                                   FROM payment_with_year_month_table p2
                                  WHERE p2.year_month < p1.year_month)
 GROUP BY p1.year_month
)

SELECT year_month,
       ROUND(number_of_new_customers*100/number_of_customers,1) AS number_of_new_customers_props,
       ROUND(new_customer_total*100/total,1) AS new_customers_total_props
  FROM new_customers_by_month_table;

SELECT ROUND(AVG(profit), 2) AS avg_profit_per_customer
  FROM CustomersByRevenue c_rev;