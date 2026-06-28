-- ============================================================
-- BOEHRINGER.GAME 초기 스키마
-- Supabase SQL 에디터에서 실행.
--   user_profiles  : 접근 레벨·표시 이름 (전 게임 공용)
--   provision_game : 게임별 테이블(app_data_<id>·app_log_<id>)을 만드는 함수
-- 게임 데이터 테이블 자체는 게임 추가 시 provision_game이 생성한다(컬럼은 전 게임 동일).
-- ============================================================

-- ── user_profiles ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_profiles (
    id            uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name  text,
    user_category text,
    access_level  int    NOT NULL DEFAULT 10,
    allowed_apps  text[] NOT NULL DEFAULT '{}',
    created_at    timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "본인 프로필만 접근" ON user_profiles;
CREATE POLICY "본인 프로필만 접근" ON user_profiles
    FOR ALL USING (auth.uid() = id);

-- 신규 가입 시 user_profiles 자동 생성. search_path=''·public.* 명시로
-- auth 관리자 컨텍스트에서도 동작하며, 실패해도 가입 자체는 막지 않는다.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = ''
AS $$
BEGIN
    INSERT INTO public.user_profiles (id, display_name)
    VALUES (NEW.id, split_part(NEW.email, '@', 1))
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ── provision_game(게임별 테이블 생성기) ─────────────────────
-- 모든 게임이 동일한 컬럼 스키마를 갖도록 한 곳에서 정의한다.
--   app_data_<id>: id · user_id · data_type · reference_id · payload · created_at
--   app_log_<id> : id · user_id · event · payload · created_at
CREATE OR REPLACE FUNCTION public.provision_game(p_game_id text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = ''
AS $$
DECLARE
    gid    text := lower(p_game_id);
    t_data text;
    t_log  text;
BEGIN
    IF gid !~ '^[a-z][a-z0-9_]{0,40}$' THEN
        RAISE EXCEPTION 'invalid game id: %', p_game_id;
    END IF;
    t_data := 'app_data_' || gid;
    t_log  := 'app_log_'  || gid;

    EXECUTE format('CREATE TABLE IF NOT EXISTS public.%I (
        id           bigserial PRIMARY KEY,
        user_id      uuid REFERENCES auth.users(id),
        data_type    text        NOT NULL DEFAULT ''default'',
        reference_id text,
        payload      jsonb       NOT NULL DEFAULT ''{}''::jsonb,
        created_at   timestamptz NOT NULL DEFAULT now()
    )', t_data);

    EXECUTE format('CREATE TABLE IF NOT EXISTS public.%I (
        id         bigserial PRIMARY KEY,
        user_id    uuid REFERENCES auth.users(id),
        event      text        NOT NULL,
        payload    jsonb       NOT NULL DEFAULT ''{}''::jsonb,
        created_at timestamptz NOT NULL DEFAULT now()
    )', t_log);

    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON public.%I (data_type, created_at DESC)',
                   'idx_' || t_data, t_data);

    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t_data);
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t_log);

    EXECUTE format('DROP POLICY IF EXISTS own_rows ON public.%I', t_data);
    EXECUTE format('CREATE POLICY own_rows ON public.%I FOR ALL USING (auth.uid() = user_id)', t_data);
    EXECUTE format('DROP POLICY IF EXISTS own_rows ON public.%I', t_log);
    EXECUTE format('CREATE POLICY own_rows ON public.%I FOR ALL USING (auth.uid() = user_id)', t_log);
END;
$$;

-- 서버(service key = service_role)가 RPC로 호출할 수 있도록 권한 부여
GRANT EXECUTE ON FUNCTION public.provision_game(text) TO service_role;
