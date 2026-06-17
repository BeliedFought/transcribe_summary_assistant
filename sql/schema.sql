CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    source_filename TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_url TEXT,
    original_path TEXT NOT NULL,
    session_dir TEXT NOT NULL,
    file_size_bytes INTEGER,
    duration_seconds REAL,
    file_hash TEXT,
    whisper_model TEXT,
    whisper_language TEXT,
    whisper_confidence REAL,
    word_count INTEGER,
    speaker_count INTEGER,
    speakers_list TEXT,
    transcription_path TEXT,
    summary_path TEXT,
    article_path TEXT,
    summarizer_engine TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    email_status TEXT,
    article_email_status TEXT,
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    processing_time_seconds REAL
);

CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_hash ON sessions(file_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at);

CREATE TABLE IF NOT EXISTS processing_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    stage TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    error_message TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS translations (
    key TEXT NOT NULL,
    lang TEXT NOT NULL DEFAULT 'ru',
    value TEXT NOT NULL,
    PRIMARY KEY (key, lang)
);
