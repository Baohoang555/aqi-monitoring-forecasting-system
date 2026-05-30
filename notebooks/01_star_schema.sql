-- ============================================================
-- PH-04: Star Schema DDL — MariaDB
-- Dataset: World Air Pollution & AQI 2014–2025
-- Chạy: mysql -u root -p aqi_dw < 01_star_schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS aqi_dw
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE aqi_dw;

-- ============================================================
-- DIMENSION TABLES
-- ============================================================

-- DIM_TIME
CREATE TABLE IF NOT EXISTS dim_time (
    time_key    INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    full_date   DATE         NOT NULL,
    year        SMALLINT     NOT NULL,
    month       TINYINT      NOT NULL,
    month_name  VARCHAR(20)  NOT NULL,
    quarter     TINYINT      NOT NULL,
    day         TINYINT      NOT NULL,
    week        TINYINT      NOT NULL,
    season      VARCHAR(10)  NOT NULL,  -- 'dry' / 'rainy'
    is_weekend  TINYINT(1)   NOT NULL DEFAULT 0,
    UNIQUE KEY uix_date (full_date)
) ENGINE=InnoDB;


-- DIM_LOCATION
CREATE TABLE IF NOT EXISTS dim_location (
    location_key  INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    city          VARCHAR(100) NOT NULL,
    country       VARCHAR(100) NOT NULL,
    country_code  CHAR(3),
    continent     VARCHAR(50),
    UNIQUE KEY uix_city_country (city, country)
) ENGINE=InnoDB;


-- DIM_POLLUTANT
CREATE TABLE IF NOT EXISTS dim_pollutant (
    pollutant_key  INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    pollutant_code VARCHAR(20)  NOT NULL UNIQUE,  -- PM2.5, PM10, NO2, SO2, CO, O3
    pollutant_name VARCHAR(100) NOT NULL,
    unit           VARCHAR(20)  NOT NULL           -- ug/m3, mg/m3, ppb
) ENGINE=InnoDB;


-- ============================================================
-- FACT TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_aqi_reading (
    reading_id    BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
    time_key      INT          NOT NULL,
    location_key  INT          NOT NULL,
    pollutant_key INT          NOT NULL,
    -- Measures
    concentration DECIMAL(10,4),
    aqi_value     SMALLINT,
    aqi_category  VARCHAR(50),
    -- Flags
    is_anomaly    TINYINT(1)   DEFAULT 0,
    batch_id      VARCHAR(30),
    loaded_at     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    -- FK
    FOREIGN KEY (time_key)      REFERENCES dim_time(time_key),
    FOREIGN KEY (location_key)  REFERENCES dim_location(location_key),
    FOREIGN KEY (pollutant_key) REFERENCES dim_pollutant(pollutant_key),
    INDEX idx_time_loc  (time_key, location_key),
    INDEX idx_pollutant (pollutant_key),
    INDEX idx_aqi       (aqi_value),
    INDEX idx_batch     (batch_id)
) ENGINE=InnoDB;


-- ============================================================
-- ICEBERG CUBE TABLES (thay thế Materialized View)
-- MariaDB không có MATERIALIZED VIEW → dùng bảng thường + stored procedure
-- ============================================================

-- Cube: City × Season × Pollutant
CREATE TABLE IF NOT EXISTS cube_city_season (
    id             BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
    city           VARCHAR(100) NOT NULL,
    country        VARCHAR(100) NOT NULL,
    season         VARCHAR(10)  NOT NULL,
    pollutant_code VARCHAR(20)  NOT NULL,
    reading_count  INT          NOT NULL,
    avg_aqi        DECIMAL(8,2),
    max_aqi        SMALLINT,
    avg_conc       DECIMAL(10,4),
    unhealthy_cnt  INT          DEFAULT 0,
    computed_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uix_cube_cs (city, season, pollutant_code),
    INDEX idx_season (season),
    INDEX idx_city   (city)
) ENGINE=InnoDB;


-- Cube: City × Month (trend theo tháng)
CREATE TABLE IF NOT EXISTS cube_city_month (
    id             BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
    city           VARCHAR(100) NOT NULL,
    country        VARCHAR(100) NOT NULL,
    year           SMALLINT     NOT NULL,
    month          TINYINT      NOT NULL,
    pollutant_code VARCHAR(20)  NOT NULL,
    reading_count  INT          NOT NULL,
    avg_aqi        DECIMAL(8,2),
    max_aqi        SMALLINT,
    computed_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uix_cube_cm (city, year, month, pollutant_code)
) ENGINE=InnoDB;


-- ============================================================
-- SEED: dim_pollutant
-- ============================================================

INSERT IGNORE INTO dim_pollutant (pollutant_code, pollutant_name, unit) VALUES
('PM2.5', 'Fine Particulate Matter',   'ug/m3'),
('PM10',  'Coarse Particulate Matter', 'ug/m3'),
('NO2',   'Nitrogen Dioxide',          'ug/m3'),
('SO2',   'Sulfur Dioxide',            'ug/m3'),
('CO',    'Carbon Monoxide',           'mg/m3'),
('O3',    'Ozone',                     'ug/m3'),
('NH3',   'Ammonia',                   'ug/m3'),
('NO',    'Nitric Oxide',              'ug/m3');


-- ============================================================
-- ETL LOG
-- ============================================================

CREATE TABLE IF NOT EXISTS etl_log (
    log_id      INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    batch_id    VARCHAR(30)  NOT NULL,
    run_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    rows_loaded INT,
    status      VARCHAR(20),
    notes       TEXT
) ENGINE=InnoDB;
