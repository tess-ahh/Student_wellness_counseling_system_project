CREATE DATABASE IF NOT EXISTS Student_Wellness_DB;
USE Student_Wellness_DB;

CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    department VARCHAR(120) NOT NULL,
    year_of_study INT NOT NULL CHECK (year_of_study BETWEEN 1 AND 8),
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(30),
    consent_to_share BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS counselors (
    counselor_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    specialization VARCHAR(120),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wellness_records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    record_date DATE NOT NULL,
    wellness_status ENUM("Stable", "At Risk", "Critical") NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_wellness_student
        FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status ENUM("Scheduled", "Confirmed", "Completed", "Canceled") NOT NULL DEFAULT "Scheduled",
    student_id INT NOT NULL,
    counselor_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_appointment_student
        FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_appointment_counselor
        FOREIGN KEY (counselor_id) REFERENCES counselors(counselor_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS counseling_sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    counselor_id INT NOT NULL,
    session_date DATE NOT NULL,
    concerns TEXT NOT NULL,
    session_notes TEXT NOT NULL,
    risk_level ENUM("Low", "Moderate", "High", "Critical") NOT NULL,
    next_steps TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_session_student
        FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_session_counselor
        FOREIGN KEY (counselor_id) REFERENCES counselors(counselor_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    anonymized_student_key CHAR(64) NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comments TEXT,
    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS referrals (
    referral_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    counselor_id INT NOT NULL,
    referred_to VARCHAR(150) NOT NULL,
    reason TEXT NOT NULL,
    referral_date DATE NOT NULL,
    status ENUM("Open", "In Progress", "Closed") NOT NULL DEFAULT "Open",
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_referral_student
        FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_referral_counselor
        FOREIGN KEY (counselor_id) REFERENCES counselors(counselor_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS follow_up_actions (
    follow_up_id INT AUTO_INCREMENT PRIMARY KEY,
    referral_id INT NOT NULL,
    action_date DATE NOT NULL,
    action_taken TEXT NOT NULL,
    outcome TEXT,
    next_review_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_followup_referral
        FOREIGN KEY (referral_id) REFERENCES referrals(referral_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_appt_student_date ON appointments(student_id, appointment_date);
CREATE INDEX idx_referral_status ON referrals(status);
CREATE INDEX idx_followup_next_review ON follow_up_actions(next_review_date);

INSERT INTO counselors (full_name, email, specialization)
SELECT * FROM (
    SELECT "Dr. Asha Menon", "asha.menon@campus.edu", "Anxiety and Stress"
    UNION ALL
    SELECT "Mr. Ravi Kumar", "ravi.kumar@campus.edu", "Academic Burnout"
) AS init_rows
WHERE NOT EXISTS (SELECT 1 FROM counselors LIMIT 1);
