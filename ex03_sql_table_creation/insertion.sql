-- ============================================================
-- INSERTION DES DONNÉES DE RÉFÉRENCE
-- Tables de dimension - NYC Taxi Data Warehouse
-- projet_big_data_cy_tech
-- ============================================================

-- ============================================================
-- DIM_VENDOR: Fournisseurs de service
-- ============================================================

INSERT INTO dim_vendor (vendor_id, vendor_name) VALUES
(1, 'Creative Mobile Technologies, LLC'),
(2, 'Curb Mobility, LLC'),
(6, 'Myle Technologies Inc'),
(7, 'Helix');

-- ============================================================
-- DIM_PAYMENT: Types de paiement
-- ============================================================

INSERT INTO dim_payment (payment_type, payment_description) VALUES
(0, 'Flex Fare trip'),
(1, 'Credit card'),
(2, 'Cash'),
(3, 'No charge'),
(4, 'Dispute'),
(5, 'Unknown'),
(6, 'Voided trip');

-- ============================================================
-- DIM_RATE: Codes tarifaires
-- ============================================================

INSERT INTO dim_rate (rate_code_id, rate_description) VALUES
(1, 'Standard rate'),
(2, 'JFK'),
(3, 'Newark'),
(4, 'Nassau or Westchester'),
(5, 'Negotiated fare'),
(6, 'Group ride'),
(99, 'Null/unknown');



