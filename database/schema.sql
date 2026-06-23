CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT,
    phone TEXT,
    address TEXT,
    profession TEXT,
    experience TEXT,
    status TEXT DEFAULT 'approved'
);

CREATE TABLE services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT,
    category TEXT,
    description TEXT,
    image TEXT
);

CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    service_id INTEGER,
    assigned_worker_id INTEGER,
    booking_date TEXT,
    address TEXT,
    status TEXT DEFAULT 'pending'
);