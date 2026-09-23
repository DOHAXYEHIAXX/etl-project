IF OBJECT_ID('dbo.Sales', 'U') IS NOT NULL
    DROP TABLE dbo.Sales;
GO

CREATE TABLE dbo.Sales (
    order_id INT NOT NULL,
    customer VARCHAR(201) NULL,
    product VARCHAR(255) NULL,
    quantity INT NULL,
    unit_price DECIMAL(18, 2) NULL,
    total_amount DECIMAL(18, 2) NULL
);
GO
