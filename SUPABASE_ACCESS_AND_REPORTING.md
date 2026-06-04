# Supabase SQL Access, Tracking, and Reporting Guide
### Nexus Hestia × Cosmic Buildings

This guide provides instructions and SQL queries to access, query, track, and report on data stored in the **Supabase PostgreSQL database** for the Cosmic Buildings Data Audit app.

---

## 1. How to Access the Database

There are two primary ways to access the database:

### Method A: The Supabase Web Console (Easiest)
1. Log into your account at [Supabase Dashboard](https://supabase.com/dashboard).
2. Select your project (e.g., `nexushestia-cosmic`).
3. You can view/edit data using two built-in tools:
   * **Table Editor** (spreadsheet-like interface in the left sidebar): Great for looking at rows or editing them manually.
   * **SQL Editor** (terminal icon in the left sidebar): Best for running the reporting and tracking queries listed in Section 3 of this document.

### Method B: External Database Clients (DBeaver, TablePlus, etc.)
You can connect direct reporting tools (like DBeaver, TablePlus, or PowerBI/Looker Studio) using your project's connection details:
1. Go to **Settings** (gear icon) → **Database** in the Supabase Dashboard.
2. Under **Connection Info**, copy the credentials:
   * **Host**: `aws-0-us-west-2.pooler.supabase.com` (or similar)
   * **Port**: `5432` (or `6543` for connection pooling)
   * **Database**: `postgres`
   * **Username**: `postgres`
   * **Password**: *The database password you created when spinning up the project.*
   * **SSL**: Required (check "Require SSL" in your client)

---

## 2. Quick Schema Reference

The app uses three main tables and two pre-configured views:

```
                  ┌─────────────────┐
                  │      users      │  (App authorization list)
                  └────────┬────────┘
                           │
                  ┌────────┴────────┐
                  │  stream_checks  │  (Currently checked/audited data streams)
                  └────────┬────────┘
                           │
                  ┌────────┴────────┐
                  │    audit_log    │  (Historical trace of all user changes)
                  └─────────────────┘
```

* **`stream_checks`**: Tracks each audited data stream, who marked it, and the completion %.
* **`audit_log`**: Historical immutable record of actions: `signin`, `stream_checked`, `stream_unchecked`, `stream_updated`, `invite_sent`, `user_approved`, `user_denied`, `user_removed`.
* **`users`**: Authorized access list containing user emails, roles (`viewer` or `admin`), and approval status.

---

## 3. Useful SQL Queries for Tracking & Reporting

Run these queries in the **Supabase SQL Editor** to generate reports.

### Query 1: Overall Audit Progress
Provides a high-level summary of total audited streams and the average completion percentage across all streams currently checked.
```sql
SELECT 
  COUNT(*) AS total_checked_streams,
  ROUND(AVG(completion_pct), 1) AS average_completion_percentage,
  COUNT(DISTINCT checked_by_email) AS total_active_auditors
FROM stream_checks
WHERE checked = TRUE;
```

### Query 2: Progress by Domain (Category)
Breaks down completion statistics by Domain ID (e.g., `d1` to `d8`) to see which sections are completed or lagging.
```sql
SELECT 
  domain_id,
  COUNT(*) AS total_checked,
  ROUND(AVG(completion_pct), 1) AS avg_completion_pct,
  MIN(updated_at) AS first_checked_at,
  MAX(updated_at) AS last_updated_at
FROM stream_checks
GROUP BY domain_id
ORDER BY domain_id;
```
*(Alternatively, you can just query the built-in view: `SELECT * FROM domain_progress;`)*

### Query 3: Auditor Leaderboard (Tracking User Activity)
Tracks how many streams each user has checked/audited. Great for team progress reports.
```sql
SELECT 
  checked_by_name AS auditor_name,
  checked_by_email AS auditor_email,
  COUNT(*) AS total_streams_audited,
  ROUND(AVG(completion_pct), 1) AS avg_stream_completion
FROM stream_checks
GROUP BY checked_by_name, checked_by_email
ORDER BY total_streams_audited DESC;
```

### Query 4: Detailed Activity History (Auditing & Security)
An historical feed showing exactly when streams were checked, unchecked, or modified, and by whom.
```sql
SELECT 
  created_at AS timestamp,
  actor_email AS user,
  action,
  stream_id,
  completion_pct AS pct,
  detail
FROM audit_log
ORDER BY created_at DESC;
```
*(Or use the view: `SELECT * FROM recent_activity;`)*

### Query 5: User Access & Approval Registry
Retrieves a list of all invited users, their approval status, and who invited them.
```sql
SELECT 
  email,
  role,
  approved,
  invited_by,
  created_at AS registration_date
FROM users
ORDER BY approved ASC, created_at DESC;
```

---

## 4. Connecting to External BI Tools (Looker Studio / Power BI)

You can build interactive, real-time dashboards for clients/stakeholders:

### Google Looker Studio (Free & Easy)
1. Go to [Looker Studio](https://lookerstudio.google.com).
2. Click **Create** → **Data Source**.
3. Select the **Postgres** connector.
4. Input your Supabase Database credentials (see Section 1, Method B).
5. Tick **Enable SSL**.
6. Select the table/view you want to visualize (e.g. `domain_progress` or `stream_checks`).
7. Build graphs, pie charts, and tables using drag-and-drop elements.

### Microsoft Power BI
1. Open **Power BI Desktop**.
2. Click **Get Data** → **PostgreSQL database**.
3. Enter Server Host and Database (`postgres`).
4. Select **Import** or **DirectQuery** (DirectQuery updates in real-time).
5. Enter Database username (`postgres`) and your password.
