-- Job Application Tracker: database creation script
-- Run with:  mysql -u root -p < schema.sql

DROP DATABASE IF EXISTS job_tracker;
CREATE DATABASE job_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE job_tracker;

CREATE TABLE companies (
    company_id   INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    industry     VARCHAR(50),
    website      VARCHAR(200),
    city         VARCHAR(50),
    state        VARCHAR(50),
    notes        TEXT
);

CREATE TABLE jobs (
    job_id       INT PRIMARY KEY AUTO_INCREMENT,
    company_id   INT NOT NULL,
    job_title    VARCHAR(100) NOT NULL,
    job_type     ENUM('Full-time','Part-time','Contract','Internship') DEFAULT 'Full-time',
    salary_min   INT,
    salary_max   INT,
    job_url      VARCHAR(300),
    date_posted  DATE,
    requirements JSON,  -- e.g. ["Python", "SQL", "Flask"]
    CONSTRAINT fk_jobs_company FOREIGN KEY (company_id)
        REFERENCES companies(company_id) ON DELETE CASCADE,
    CONSTRAINT chk_salary CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max)
);

CREATE TABLE applications (
    application_id   INT PRIMARY KEY AUTO_INCREMENT,
    job_id           INT NOT NULL,
    application_date DATE NOT NULL,
    status           ENUM('Applied','Screening','Interview','Offer','Rejected','Withdrawn') DEFAULT 'Applied',
    resume_version   VARCHAR(50),
    cover_letter_sent BOOLEAN DEFAULT FALSE,
    interview_data   JSON,  -- e.g. {"rounds": [{"type": "Phone", "date": "2026-02-01"}]}
    CONSTRAINT fk_applications_job FOREIGN KEY (job_id)
        REFERENCES jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE contacts (
    contact_id   INT PRIMARY KEY AUTO_INCREMENT,
    company_id   INT NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    title        VARCHAR(100),
    email        VARCHAR(100),
    phone        VARCHAR(20),
    linkedin_url VARCHAR(200),
    notes        TEXT,
    CONSTRAINT fk_contacts_company FOREIGN KEY (company_id)
        REFERENCES companies(company_id) ON DELETE CASCADE
);

-- Sample data so the app has something to show on first run
INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES
 ('TechCorp', 'Software', 'https://techcorp.example.com', 'Austin', 'TX', 'Referred by a classmate.'),
 ('DataCo', 'Analytics', 'https://dataco.example.com', 'Denver', 'CO', 'Hybrid, 2 days on site.'),
 ('CloudNine', 'Cloud Services', 'https://cloudnine.example.com', 'Seattle', 'WA', NULL);

INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
 (1, 'Software Developer', 'Full-time', 85000, 110000, 'https://techcorp.example.com/jobs/1', '2026-01-05', JSON_ARRAY('Python','SQL','Flask')),
 (2, 'Data Analyst', 'Full-time', 70000, 90000, 'https://dataco.example.com/jobs/7', '2026-01-12', JSON_ARRAY('Python','SQL','Tableau')),
 (3, 'Cloud Intern', 'Internship', 25000, 30000, NULL, '2026-01-20', JSON_ARRAY('Linux','AWS','Python','Docker'));

INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
 (1, '2026-01-08', 'Interview', 'v2-dev', TRUE, JSON_OBJECT('rounds', JSON_ARRAY(JSON_OBJECT('type','Phone screen','date','2026-01-20'), JSON_OBJECT('type','Technical','date','2026-01-27')))),
 (2, '2026-01-15', 'Applied', 'v1-data', FALSE, NULL),
 (3, '2026-01-22', 'Rejected', 'v2-dev', TRUE, NULL);

INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
 (1, 'Maria Lopez', 'Technical Recruiter', 'maria.lopez@techcorp.example.com', '512-555-0142', 'https://linkedin.com/in/marialopez', 'Met at career fair.'),
 (2, 'James Park', 'Hiring Manager', 'jpark@dataco.example.com', NULL, NULL, NULL);
