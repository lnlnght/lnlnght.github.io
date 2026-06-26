-- ============================================================
-- Supabase 스키마: 주식·ETF 데이터
-- Supabase 대시보드 > SQL Editor에서 실행하세요.
-- ============================================================

-- 주식 테이블
CREATE TABLE IF NOT EXISTS stocks (
  code            TEXT PRIMARY KEY,
  name            TEXT,
  sector          TEXT,
  market          TEXT,
  currency        TEXT,
  current         DOUBLE PRECISION,
  change          DOUBLE PRECISION,
  change_pct      DOUBLE PRECISION,
  trailing_per    DOUBLE PRECISION,
  forward_per     DOUBLE PRECISION,
  pbr             DOUBLE PRECISION,
  psr             DOUBLE PRECISION,
  roe             DOUBLE PRECISION,
  eps             DOUBLE PRECISION,
  operating_income  BIGINT,
  net_income_ttm    BIGINT,
  forward_net_income BIGINT,
  forward_eps_krw   DOUBLE PRECISION,
  market_cap        BIGINT,
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ETF 테이블
CREATE TABLE IF NOT EXISTS etfs (
  code            TEXT PRIMARY KEY,
  name            TEXT,
  category        TEXT,
  market          TEXT,
  currency        TEXT,
  current         DOUBLE PRECISION,
  change          DOUBLE PRECISION,
  change_pct      DOUBLE PRECISION,
  expense_ratio   DOUBLE PRECISION,
  dividend_yield  DOUBLE PRECISION,
  total_assets    BIGINT,
  high_52w        DOUBLE PRECISION,
  low_52w         DOUBLE PRECISION,
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 누구나 읽을 수 있도록 공개 정책 (anon key로 SELECT 허용)
ALTER TABLE stocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE etfs   ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public read stocks" ON stocks FOR SELECT USING (true);
CREATE POLICY "public read etfs"   ON etfs   FOR SELECT USING (true);
