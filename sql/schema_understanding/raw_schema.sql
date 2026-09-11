-- Question:        What are the operational tables, their grains and the keys that connect them?
-- Why it matters:  Every later measure depends on joining identity, access, catalogue and playback
--                  at the right grain. Precision and nullability here decide what can be measured.
-- Analytical use:  Reference DDL for an empty MySQL 8 schema. It does not load or replace data
--                  and should not be run against a database that already holds these tables.
USE ott_viewership;

CREATE TABLE accounts (
  account_id            CHAR(7)      NOT NULL,
  account_created_date  DATE         NOT NULL,
  home_region           VARCHAR(20)  NOT NULL,
  CONSTRAINT pk_accounts PRIMARY KEY (account_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE profiles (
  profile_id            CHAR(7)      NOT NULL,
  account_id            CHAR(7)      NOT NULL,
  profile_created_date  DATE         NOT NULL,
  CONSTRAINT pk_profiles PRIMARY KEY (profile_id),
  CONSTRAINT fk_profiles_account
    FOREIGN KEY (account_id) REFERENCES accounts (account_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE subscription_cycles (
  subscription_cycle_id CHAR(8)      NOT NULL,
  account_id            CHAR(7)      NOT NULL,
  plan_family           VARCHAR(20)  NOT NULL,
  plan_language_group   VARCHAR(12)  NOT NULL,
  cycle_start_date      DATE         NOT NULL,
  cycle_end_date        DATE         NOT NULL,
  subscription_source   VARCHAR(24)  NOT NULL,
  billing_cycle         VARCHAR(14)  NOT NULL,
  payment_method        VARCHAR(12)  NULL,
  payment_status        VARCHAR(16)  NOT NULL,
  auto_renew_flag       TINYINT(1)   NULL,
  CONSTRAINT pk_subscription_cycles PRIMARY KEY (subscription_cycle_id),
  CONSTRAINT fk_subscription_cycles_account
    FOREIGN KEY (account_id) REFERENCES accounts (account_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE content_catalogue (
  content_id            CHAR(7)      NOT NULL,
  parent_title_id       CHAR(7)      NOT NULL,
  title_name            VARCHAR(100) NOT NULL,
  series_name           VARCHAR(100) NULL,
  content_type          VARCHAR(10)  NOT NULL,
  program_type          VARCHAR(24)  NOT NULL,
  origin_type           VARCHAR(24)  NOT NULL,
  season_number         TINYINT UNSIGNED  NULL,
  episode_number        SMALLINT UNSIGNED NULL,
  runtime_minutes       DECIMAL(5,1) NOT NULL,
  release_date          DATE         NOT NULL,
  original_language     VARCHAR(16)  NOT NULL,
  primary_genre         VARCHAR(16)  NOT NULL,
  catalogue_entry_date  DATE         NOT NULL,
  catalogue_exit_date   DATE         NULL,
  CONSTRAINT pk_content_catalogue PRIMARY KEY (content_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE content_audio_languages (
  parent_title_id       CHAR(7)      NOT NULL,
  language              VARCHAR(16)  NOT NULL,
  is_original_language  TINYINT(1)   NOT NULL,
  CONSTRAINT pk_content_audio_languages PRIMARY KEY (parent_title_id, language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE viewing_sessions (
  session_id            CHAR(9)      NOT NULL,
  profile_id            CHAR(7)      NOT NULL,
  session_start_ts      DATETIME(6)  NOT NULL,
  session_end_ts        DATETIME(6)  NOT NULL,
  device_type           VARCHAR(14)  NOT NULL,
  CONSTRAINT pk_viewing_sessions PRIMARY KEY (session_id),
  CONSTRAINT fk_viewing_sessions_profile
    FOREIGN KEY (profile_id) REFERENCES profiles (profile_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE view_events (
  view_event_id           CHAR(10)   NOT NULL,
  session_id              CHAR(9)    NOT NULL,
  content_id              CHAR(7)    NOT NULL,
  event_start_ts          DATETIME(6) NOT NULL,
  event_end_ts            DATETIME(6) NOT NULL,
  watch_seconds           MEDIUMINT UNSIGNED NOT NULL,
  playback_start_position MEDIUMINT UNSIGNED NOT NULL,
  playback_end_position   MEDIUMINT UNSIGNED NOT NULL,
  audio_language          VARCHAR(16) NOT NULL,
  is_autoplay             TINYINT(1)  NOT NULL,
  CONSTRAINT pk_view_events PRIMARY KEY (view_event_id),
  CONSTRAINT fk_view_events_session
    FOREIGN KEY (session_id) REFERENCES viewing_sessions (session_id),
  CONSTRAINT fk_view_events_content
    FOREIGN KEY (content_id) REFERENCES content_catalogue (content_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
