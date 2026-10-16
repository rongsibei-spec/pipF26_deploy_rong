-- Class intake schema for class_dataset.csv
-- netid is the student primary key (lowercased; strip @nyu.edu on load).
-- N-numbers are stored as netid when no NetID is present.
-- #NAME? in working_style is stored as NULL.

CREATE TABLE student (
    netid TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    school_year TEXT NOT NULL
        CHECK (school_year IN ('first_year', 'sophomore', 'junior', 'senior')),
    intro_programming TEXT NOT NULL
        CHECK (intro_programming IN ('took_it', 'equivalent', 'neither')),
    skill_programming SMALLINT NOT NULL
        CHECK (skill_programming BETWEEN 1 AND 5),
    skill_data_stats SMALLINT NOT NULL
        CHECK (skill_data_stats BETWEEN 1 AND 5),
    skill_frontend_design SMALLINT NOT NULL
        CHECK (skill_frontend_design BETWEEN 1 AND 5),
    skill_business_pitch SMALLINT NOT NULL
        CHECK (skill_business_pitch BETWEEN 1 AND 5),
    working_style TEXT,
    interests TEXT,
    semester_goal TEXT,
    submitted_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE tool (
    name TEXT PRIMARY KEY
);

CREATE TABLE student_tool (
    netid TEXT NOT NULL REFERENCES student (netid) ON DELETE CASCADE,
    tool_name TEXT NOT NULL REFERENCES tool (name) ON DELETE RESTRICT,
    PRIMARY KEY (netid, tool_name)
);

CREATE TABLE availability_slot (
    label TEXT PRIMARY KEY,
    day_part TEXT NOT NULL
        CHECK (day_part IN ('weekday', 'weekend')),
    time_of_day TEXT NOT NULL
        CHECK (time_of_day IN ('morning', 'afternoon', 'evening'))
);

CREATE TABLE student_availability (
    netid TEXT NOT NULL REFERENCES student (netid) ON DELETE CASCADE,
    slot_label TEXT NOT NULL REFERENCES availability_slot (label) ON DELETE RESTRICT,
    PRIMARY KEY (netid, slot_label)
);

INSERT INTO tool (name) VALUES
    ('Python'),
    ('SQL'),
    ('Excel'),
    ('JavaScript'),
    ('R');

INSERT INTO availability_slot (label, day_part, time_of_day) VALUES
    ('Weekday mornings', 'weekday', 'morning'),
    ('Weekday afternoons', 'weekday', 'afternoon'),
    ('Weekday evenings', 'weekday', 'evening'),
    ('Weekend mornings', 'weekend', 'morning'),
    ('Weekend afternoons', 'weekend', 'afternoon'),
    ('Weekend evenings', 'weekend', 'evening');
