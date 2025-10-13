-- =========================
-- Catálogos y entidades
-- =========================

use prometheus
go

CREATE TABLE currency (
    currency_code CHAR(3) PRIMARY KEY,      -- ISO 4217 (e.g., 'USD', 'EUR')
    name NVARCHAR(MAX) NOT NULL,
    symbol NVARCHAR(MAX) NOT NULL,           -- e.g., '$', '€'
    decimal_places SMALLINT NOT NULL DEFAULT 2,
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2
);

CREATE TABLE accounting_entity (
    entity_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    name NVARCHAR(MAX) NOT NULL,
    base_currency CHAR(3) NOT NULL REFERENCES currency(currency_code),
    razon_social NVARCHAR(MAX),
    ruc NVARCHAR(MAX),
    representante_legal NVARCHAR(MAX),
    parent_entity_id UNIQUEIDENTIFIER REFERENCES accounting_entity(entity_id),
    timezone NVARCHAR(100) NOT NULL DEFAULT 'UTC',
    is_consolidated BIT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2,
    deleted_at DATETIME2
);

CREATE TABLE fiscal_period (
    period_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    entity_id UNIQUEIDENTIFIER NOT NULL REFERENCES accounting_entity(entity_id),
    period_code NVARCHAR(50) NOT NULL,            -- e.g., '2025-08'
    fiscal_year AS (CAST(SUBSTRING(period_code, 1, 4) AS INT) )PERSISTED,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_closed BIT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2,
    deleted_at DATETIME2,
    UNIQUE (entity_id, period_code),
    CHECK (start_date <= end_date)
);

-- =========================
-- Plan de cuentas
-- =========================
CREATE TABLE account (
    account_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    entity_id UNIQUEIDENTIFIER NOT NULL REFERENCES accounting_entity(entity_id),
    account_code NVARCHAR(60) NOT NULL,            -- e.g., '1000', '1100.01'
    account_name NVARCHAR(100) NOT NULL,
    description NVARCHAR(150),
    category NVARCHAR(50) NOT NULL,                 -- Change to NVARCHAR for ENUM
    normal_side NVARCHAR(50) NOT NULL,              -- Change to NVARCHAR for ENUM
    parent_account_id UNIQUEIDENTIFIER REFERENCES account(account_id),
    is_postable BIT NOT NULL DEFAULT 1,
    is_active BIT NOT NULL DEFAULT 1,
    currency_code CHAR(3) NOT NULL REFERENCES currency(currency_code),
    level INT NOT NULL DEFAULT 1,                   -- Nivel en jerarquía
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2,
    deleted_at DATETIME2,
    UNIQUE(entity_id, account_code),
    CHECK (account_id <> parent_account_id),
    CHECK (account_code LIKE '[0-9]%')
);

-- =========================
-- Dimensiones analíticas
-- =========================
CREATE TABLE cost_center (
    cost_center_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    entity_id UNIQUEIDENTIFIER NOT NULL REFERENCES accounting_entity(entity_id),
    code NVARCHAR(50) NOT NULL,
    name NVARCHAR(100) NOT NULL,
    description NVARCHAR(150),
    parent_id UNIQUEIDENTIFIER REFERENCES cost_center(cost_center_id),
    budget_amount DECIMAL(18, 2),
    budget_currency CHAR(3) REFERENCES currency(currency_code),
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2,
    deleted_at DATETIME2,
    UNIQUE(entity_id, code)
);

CREATE TABLE project (
    project_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    entity_id UNIQUEIDENTIFIER NOT NULL REFERENCES accounting_entity(entity_id),
    code NVARCHAR(50) NOT NULL,
    name NVARCHAR(100) NOT NULL,
    description NVARCHAR(150),
    parent_id UNIQUEIDENTIFIER REFERENCES project(project_id),
    budget_amount DECIMAL(18, 2),
    budget_currency CHAR(3) REFERENCES currency(currency_code),
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2,
    deleted_at DATETIME2,
    UNIQUE(entity_id, code)
);

-- =========================
-- Tablas de soporte para negocios
-- =========================
CREATE TABLE exchange_rate (
    rate_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    from_currency CHAR(3) NOT NULL REFERENCES currency(currency_code),
    to_currency CHAR(3) NOT NULL REFERENCES currency(currency_code),
    rate_date DATE NOT NULL,
    rate DECIMAL(15, 6) NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2,
    UNIQUE(from_currency, to_currency, rate_date)
);

CREATE TABLE tax_code (
    tax_code_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    entity_id UNIQUEIDENTIFIER NOT NULL REFERENCES accounting_entity(entity_id),
    code NVARCHAR(50) NOT NULL,
    name NVARCHAR(100) NOT NULL,
    rate DECIMAL(5, 2) NOT NULL,
    account_id UNIQUEIDENTIFIER REFERENCES account(account_id),
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2,
    deleted_at DATETIME2,
    UNIQUE(entity_id, code)
);

CREATE TABLE partner (
    partner_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    entity_id UNIQUEIDENTIFIER NOT NULL REFERENCES accounting_entity(entity_id),
    name NVARCHAR(100) NOT NULL,
    type NVARCHAR(50) CHECK (type IN ('CUSTOMER', 'VENDOR', 'EMPLOYEE')),
    tax_id NVARCHAR(50),
    address NVARCHAR(100),
    currency_code CHAR(3) REFERENCES currency(currency_code),
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2,
    deleted_at DATETIME2
);

CREATE TABLE product (
    product_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    entity_id UNIQUEIDENTIFIER NOT NULL REFERENCES accounting_entity(entity_id),
    code NVARCHAR(50) NOT NULL,
    name NVARCHAR(100) NOT NULL,
    type NVARCHAR(50) CHECK (type IN ('GOOD', 'SERVICE')),
    unit_price DECIMAL(18, 2),
    cost_account_id UNIQUEIDENTIFIER REFERENCES account(account_id),
    revenue_account_id UNIQUEIDENTIFIER REFERENCES account(account_id),
    inventory_account_id UNIQUEIDENTIFIER REFERENCES account(account_id),
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2,
    deleted_at DATETIME2,
    UNIQUE(entity_id, code)
);

CREATE TABLE inventory (
    inventory_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    product_id UNIQUEIDENTIFIER NOT NULL REFERENCES product(product_id),
    quantity DECIMAL(18, 2) NOT NULL,
    as_of_date DATE NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2,
    deleted_at DATETIME2
);

-- =========================
-- Transacciones
-- =========================
CREATE TABLE journal_entry (
    entry_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    entity_id UNIQUEIDENTIFIER NOT NULL REFERENCES accounting_entity(entity_id),
    period_id UNIQUEIDENTIFIER NOT NULL REFERENCES fiscal_period(period_id),
    entry_date DATE NOT NULL,
    description NVARCHAR(150),
    is_posted BIT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2,
    deleted_at DATETIME2
);

CREATE TABLE ledger_line (
    line_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    entry_id UNIQUEIDENTIFIER NOT NULL REFERENCES journal_entry(entry_id),
    account_id UNIQUEIDENTIFIER NOT NULL REFERENCES account(account_id),
    debit DECIMAL(18, 2) NOT NULL DEFAULT 0,
    credit DECIMAL(18, 2) NOT NULL DEFAULT 0,
    currency_code CHAR(3) NOT NULL REFERENCES currency(currency_code),
    amount_foreign DECIMAL(18, 2),
    cost_center_id UNIQUEIDENTIFIER REFERENCES cost_center(cost_center_id),
    project_id UNIQUEIDENTIFIER REFERENCES project(project_id),
    partner_id UNIQUEIDENTIFIER REFERENCES partner(partner_id),
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2,
    CHECK (debit >= 0 AND credit >= 0 AND (debit + credit > 0))
);

-- =========================
-- Plantillas de asientos
-- =========================
CREATE TABLE journal_template (
    template_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    entity_id UNIQUEIDENTIFIER NOT NULL REFERENCES accounting_entity(entity_id),
    code NVARCHAR(50) NOT NULL,
    name NVARCHAR(100) NOT NULL,
    description NVARCHAR(150),
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2,
    deleted_at DATETIME2,
    UNIQUE(entity_id, code)
);

CREATE TABLE journal_template_line (
    line_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    template_id UNIQUEIDENTIFIER NOT NULL REFERENCES journal_template(template_id),
    account_id UNIQUEIDENTIFIER REFERENCES account(account_id),
    account_category NVARCHAR(50),                 -- Change to NVARCHAR for ENUM
    normal_side NVARCHAR(50) NOT NULL,             -- Change to NVARCHAR for ENUM
    amount_expression NVARCHAR(200) NOT NULL,
    currency_code CHAR(3) REFERENCES currency(currency_code),
    cost_center_id UNIQUEIDENTIFIER REFERENCES cost_center(cost_center_id),
    project_id UNIQUEIDENTIFIER REFERENCES project(project_id),
    partner_type NVARCHAR(50) CHECK (partner_type IN ('CUSTOMER', 'VENDOR', 'EMPLOYEE')),
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2,
    CHECK (account_id IS NOT NULL OR account_category IS NOT NULL),
    CHECK (amount_expression <> '')
);