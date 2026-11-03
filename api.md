# Akal Alumni Portal API Reference and Chatbot Integration Analysis

> **Scope and verification.** This document describes the API routes in
> `backend/app/Config/Routes.php` and the implementation visible in the
> controllers, filters, config, and migrations in this repository. No code,
> routes, or database objects were changed to produce it. The source schema is
> migration-defined; a live MySQL connection and current production rows were
> not inspected. Where a method's exact accepted fields or failure behavior is
> not explicit in the inspected implementation, it is marked **Not verified**.
> Example records below are illustrative and are not actual database values.

## 1. Project Overview

The backend is a CodeIgniter 4 application providing alumni/student accounts,
public portal content, admin content management, event registration, job
applications, mentorship, donations, and birthday-email administration. The
React frontend uses the API, but the API route definitions and PHP controllers
are the source of truth for this document.

The API is JSON-oriented and generally uses a shared response envelope. One
media route returns file bytes rather than JSON.

## 2. Backend Architecture

- **Routing:** `backend/app/Config/Routes.php`
- **Auto-routing:** `backend/app/Config/Routing.php` sets `$autoRoute=false`;
  only explicitly defined routes are intended to resolve.
- **API controllers:** `backend/app/Controllers/Api/`
- **Authentication and permissions:** `backend/app/Filters/AuthFilter.php` and
  `backend/app/Filters/PermissionFilter.php`
- **Response envelope:** `backend/app/Traits/ApiResponseTrait.php`
- **JWT implementation:** `backend/app/Libraries/JwtService.php`
- **Database configuration:** `backend/app/Config/Database.php`
- **Schema history:** `backend/app/Database/Migrations/`
- **Models:** no CI4 model classes were found; `backend/app/Models/` contains
  only `.gitkeep`. Controllers query the database through CI4's query builder.
- **Validation:** most API validation is implemented inline in controllers.
  `backend/app/Config/Validation.php` exists, but the routes do not define
  request-specific validation rules centrally.

Routes do not declare explicit API response content types or API version
prefixes. CRUD route bodies and some controller-specific output fields are not
uniformly validated or documented in source; see individual sections and the
route inventory.

## 3. API Base URL and Configuration

The CI4 `App` config sets the local root to `http://localhost:8080/` and
`indexPage` to `index.php`. The React API client sets its local API base to
`http://localhost:8080/api`. The documented local API root is therefore:

```text
http://localhost:8080/api
```

In deployments, configure the backend origin and web-server rewrite behavior
for that environment. The actual production URL is **Not verified**.

`backend/app/Config/Database.php` defines a MySQLi connection group with
`utf8mb4`, port `3306`, and the usual host/database/user/password configuration
keys. Values in the committed config are empty/default placeholders; actual
environment-provided connection values are not documented here. Do not copy
credentials into API requests or this document.

## 4. Authentication and Authorization

### Bearer token

Protected routes require:

```http
Authorization: Bearer <JWT returned by login>
```

`POST /api/auth/login` issues a signed JWT. `AuthFilter` validates the bearer
token and expiration, attaches its claims to the request, and returns `401` if
the header is missing or the token is invalid/expired. The configured token
lifetime in the implementation is seven days. The implementation uses a
hard-coded signing secret; its value is intentionally omitted. This is a
critical deployment risk: move signing material to protected configuration,
rotate any exposed signing key, and invalidate tokens signed with it.

Alumni access is additionally checked against current database status on every
authenticated request. Pending or rejected/suspended alumni are denied even if
their token has not expired.

### Roles

| Route group | Required role |
|---|---|
| `/api/public/*` | None |
| `/api/auth/login`, `/api/auth/register` | None |
| `/api/auth/me` | Any authenticated role |
| `/api/user/*` | Any authenticated role; job application controller additionally allows only alumni/student |
| `/api/alumni/*` | `alumni` |
| `/api/student/*` | `student` |
| `/api/admin/*` | `admin` or `superadmin` |

The auth filter permits `superadmin` through admin-role checks. Admin
permissions are a separate filter; a listed comma-separated permission set
uses **OR** logic (any one is sufficient). Superadmins bypass granular
permissions. Some admin operations perform additional controller-level checks.

Permission identifiers used in routes include `verify_alumni`,
`manage_alumni`, `manage_students`, `manage_users`, `manage_events`,
`manage_settings`, `manage_stories`, `manage_news`, `manage_chapters`,
`manage_jobs`, `manage_gallery`, `manage_donations`,
`view_audit_logs`, and `manage_birthday_emails`.
`view_reports` and `manage_admins` are in the permission catalogue, but the
routes shown here do not attach those permission names to a route.

### Common JSON envelope

Success methods using `ApiResponseTrait` return:

```json
{
  "status": true,
  "message": "Resource retrieved",
  "data": {},
  "errors": []
}
```

Failure methods using the trait return:

```json
{
  "status": false,
  "message": "Validation failed",
  "data": null,
  "errors": {
    "field": "Explanation"
  }
}
```

The `errors` value is normalized to an array by `respondError`; validation
errors may be represented as an object/map or list depending on JSON
serialization. Filter-generated `401`/`403` responses use a similar shape.
Do not assume every CI4/framework error uses this envelope.

## 5. Complete API Route Inventory

All paths below are relative to `/api`. `{id}`-style values represent the
numeric or segment placeholders in the route declaration. The optional
permission column means an admin needs at least one of the listed permissions;
superadmin bypasses the permission filter. A `—` means the route itself has no
additional permission filter.

### Public, authentication, and user routes

| Method | Path | Controller method | Authentication / permission |
|---|---|---|---|
| OPTIONS | `/{any}` | Inline preflight response | None |
| GET | `/event-report-photo/{filename}` | `AdminController::getEventReportPhoto` | None |
| GET | `/public/event-report-photo/{filename}` | `AdminController::getEventReportPhoto` | None |
| GET | `/public/settings` | `PublicController::getSettings` | None |
| GET | `/public/stats` | `PublicController::getStats` | None |
| GET | `/public/alumni` | `PublicController::getAlumni` | None |
| GET | `/public/alumni/{idOrAlumniId}` | `PublicController::getAlumniDetail` | None |
| GET | `/public/events` | `PublicController::getEvents` | None |
| POST | `/public/events/{eventId}/register` | `PublicController::registerForEvent` | None |
| GET | `/public/jobs` | `PublicController::getJobs` | None |
| GET | `/public/chapters` | `PublicController::getChapters` | None |
| GET | `/public/stories` | `PublicController::getStories` | None |
| GET | `/public/news` | `PublicController::getNews` | None |
| GET | `/public/gallery` | `PublicController::getGallery` | None |
| GET | `/public/donations` | `PublicController::getDonationCampaigns` | None |
| POST | `/auth/login` | `AuthController::login` | None |
| POST | `/auth/register` | `AuthController::register` | None |
| GET | `/auth/me` | `AuthController::me` | Authenticated |
| POST | `/user/donate` | `PublicController::makeDonation` | Any authenticated role |
| POST | `/user/jobs/{jobId}/apply` | `PublicController::applyForJob` | Authenticated; alumni/student enforced by controller |

### Alumni routes

| Method | Path | Controller method | Authentication / permission |
|---|---|---|---|
| GET | `/alumni/profile` | `AlumniController::getProfile` | `alumni` |
| PUT | `/alumni/profile` | `AlumniController::updateProfile` | `alumni` |
| GET | `/alumni/id-card` | `AlumniController::getIdCard` | `alumni` |
| POST | `/alumni/jobs` | `AlumniController::postJob` | `alumni` |
| GET | `/alumni/jobs` | `AlumniController::getMyJobs` | `alumni` |
| GET | `/alumni/jobs/{jobId}/applications` | `AlumniController::getMyJobApplications` | `alumni`; owner check |
| GET | `/alumni/mentorship-requests` | `AlumniController::getMentorshipRequests` | `alumni` |
| PUT | `/alumni/mentorship-requests/{requestId}` | `AlumniController::updateMentorshipStatus` | `alumni`; mentor ownership in update query |

### Student routes

| Method | Path | Controller method | Authentication / permission |
|---|---|---|---|
| GET | `/student/profile` | `StudentController::getProfile` | `student` |
| PUT | `/student/profile` | `StudentController::updateProfile` | `student` |
| POST | `/student/mentorship-request` | `StudentController::requestMentorship` | `student` |
| GET | `/student/my-mentorships` | `StudentController::getMyMentorships` | `student` |
| GET | `/student/my-activities` | `StudentController::getMyActivities` | `student` |
| POST | `/student/events/{eventId}/register` | `PublicController::registerForEvent` | `student` group; same handler as public event registration |

### Admin routes

| Method | Path | Controller method | Additional permission |
|---|---|---|---|
| GET | `/admin/birthday-emails` | `BirthdayEmailController::getSettings` | `manage_birthday_emails` |
| PUT | `/admin/birthday-emails` | `BirthdayEmailController::saveSettings` | `manage_birthday_emails` |
| POST | `/admin/birthday-emails/preview` | `BirthdayEmailController::preview` | `manage_birthday_emails` |
| POST | `/admin/birthday-emails/test` | `BirthdayEmailController::sendTest` | `manage_birthday_emails` |
| GET | `/admin/birthday-emails/history` | `BirthdayEmailController::history` | `manage_birthday_emails` |
| GET | `/admin/dashboard` | `AdminController::getDashboard` | — |
| GET | `/admin/mentorship-requests` | `AdminController::getMentorshipRequests` | — |
| GET | `/admin/alumni-mentors` | `AdminController::getAlumniMentorRoster` | — |
| GET | `/admin/alumni-mentors/{mentorUserId}/students` | `AdminController::getMentorStudents` | — |
| GET | `/admin/verifications` | `AdminController::getPendingVerifications` | `verify_alumni` OR `manage_alumni` OR `manage_users` |
| POST | `/admin/verifications/{userId}/approve` | `AdminController::approveVerification` | `verify_alumni` OR `manage_alumni` OR `manage_users` |
| POST | `/admin/verifications/{userId}/reject` | `AdminController::rejectVerification` | `verify_alumni` OR `manage_alumni` OR `manage_users` |
| GET | `/admin/users` | `AdminController::getAllUsers` | `manage_users` OR `manage_alumni` OR `manage_students` |
| GET | `/admin/reports/alumni` | `AdminController::getAlumniReport` | — |
| GET | `/admin/users/{userId}/detail` | `AdminController::getUserDetail` | `manage_users` OR `manage_alumni` OR `manage_students` |
| PUT | `/admin/users/{userId}/role` | `AdminController::updateUserRole` | Controller check; superadmin only |
| PUT | `/admin/users/{userId}/status` | `AdminController::updateUserStatus` | Controller permission/status checks |
| GET | `/admin/admins` | `AdminController::getAdmins` | Controller check; superadmin only |
| GET | `/admin/admin-permissions` | `AdminController::getAdminPermissionsCatalogue` | Controller check; superadmin only |
| POST | `/admin/admins` | `AdminController::createAdmin` | Controller check; superadmin only |
| PUT | `/admin/admins/{userId}` | `AdminController::updateAdminPermissions` | Controller check; superadmin only |
| PUT | `/admin/admins/{userId}/permissions` | `AdminController::updateAdminPermissions` | Controller check; superadmin only |
| DELETE | `/admin/admins/{userId}` | `AdminController::deleteAdmin` | Controller check; superadmin only |
| POST | `/admin/events` | `AdminController::saveEvent` | `manage_events` |
| DELETE | `/admin/events/{eventId}` | `AdminController::deleteEvent` | `manage_events` |
| GET | `/admin/events/{eventId}/registrations` | `AdminController::getEventRegistrations` | `manage_events` |
| GET | `/admin/events/{eventId}/report` | `AdminController::getEventReport` | `manage_events` |
| POST | `/admin/events/{eventId}/report` | `AdminController::saveEventReport` | `manage_events` |
| GET | `/admin/settings` | `AdminController::getSettings` | `manage_settings` |
| POST | `/admin/settings` | `AdminController::saveSettings` | `manage_settings` |
| POST | `/admin/settings/custom` | `AdminController::addCustomSetting` | `manage_settings` |
| DELETE | `/admin/settings/{key}` | `AdminController::deleteSetting` | `manage_settings` |
| GET | `/admin/stories` | `AdminController::getStories` | — |
| POST | `/admin/stories` | `AdminController::saveStory` | `manage_stories` |
| DELETE | `/admin/stories/{id}` | `AdminController::deleteStory` | `manage_stories` |
| GET | `/admin/news` | `AdminController::getNews` | — |
| POST | `/admin/news` | `AdminController::saveNews` | `manage_news` |
| DELETE | `/admin/news/{id}` | `AdminController::deleteNews` | `manage_news` |
| GET | `/admin/chapters` | `AdminController::getChapters` | — |
| POST | `/admin/chapters` | `AdminController::saveChapter` | `manage_chapters` |
| DELETE | `/admin/chapters/{id}` | `AdminController::deleteChapter` | `manage_chapters` |
| GET | `/admin/jobs` | `AdminController::getJobs` | `manage_jobs` |
| GET | `/admin/jobs/{jobId}/applications` | `AdminController::getJobApplications` | `manage_jobs` |
| POST | `/admin/jobs` | `AdminController::saveJob` | `manage_jobs` |
| DELETE | `/admin/jobs/{id}` | `AdminController::deleteJob` | `manage_jobs` |
| GET | `/admin/gallery` | `AdminController::getGallery` | — |
| POST | `/admin/gallery` | `AdminController::saveGallery` | `manage_gallery` |
| DELETE | `/admin/gallery/{id}` | `AdminController::deleteGallery` | `manage_gallery` |
| GET | `/admin/donation-campaigns` | `AdminController::getDonationCampaigns` | `manage_donations` |
| POST | `/admin/donation-campaigns` | `AdminController::saveDonationCampaign` | `manage_donations` |
| DELETE | `/admin/donation-campaigns/{id}` | `AdminController::deleteDonationCampaign` | `manage_donations` |
| GET | `/admin/donations` | `AdminController::getDonations` | `manage_donations` |
| GET | `/admin/audit-logs` | `AdminController::getAuditLogs` | `view_audit_logs` |

**Route count:** 87 API route declarations: 86 explicit HTTP route patterns and
one catch-all `OPTIONS` declaration. The `OPTIONS` declaration matches API
subpaths; it is not an individual API resource. The separate non-API `GET /`
home route is excluded.

## 6. Public API Documentation

Public API routes do not require a bearer token. JSON endpoints use the common
envelope unless otherwise noted. For public GETs with no supported query
parameters, extra query parameters are ignored or unused by the controller;
pagination is not implemented unless explicitly stated.

### `GET /public/settings`

- **Handler:** `PublicController::getSettings`
- **Tables/fields:** Reads all rows from `system_settings`; returns a map
  `setting_key => setting_value`.
- **Visibility:** No allowlist or publication filter. Any secret or
  administrative value stored in this table would be exposed.
- **Search/filter/sort/pagination:** None.
- **Mode:** Read-only.
- **Response data example:** `{"site_name":"Akal University"}` (illustrative).
- **Errors/status:** Standard success envelope; database/framework failure
  behavior is **Not verified**.
- **Chatbot:** Do not call until settings are allowlisted and reviewed.

### `GET /public/stats`

- **Handler:** `PublicController::getStats`
- **Tables:** `users`, `events`, `jobs`, `alumni_profiles`, `chapters`,
  `success_stories`, `news_announcements`, `gallery_albums`.
- **Data fields:** `data.counts` includes `total_alumni`, `verified_alumni`,
  `total_students`, `total_events`, `total_jobs`, `total_mentors`,
  `total_chapters`, `total_chapter_members`, `total_stories`, `total_news`,
  `total_albums`; `data.departments` and `data.batches` are distinct values
  read from alumni profiles.
- **Conditions:** Active role alumni for `total_alumni`; verified role alumni
  for `verified_alumni` without an active-status condition; all rows with
  student role for `total_students`; published/non-deleted events; approved/
  non-deleted jobs; `is_mentor=1` alumni profiles; active chapters; published
  stories/news/gallery. Department and batch lists have non-null conditions
  only and include private/unverified profiles.
- **Search/filter/sort/pagination:** None.
- **Mode:** Read-only aggregate.
- **Privacy/chatbot:** Counts are aggregate, but the student count is not
  filtered by active status; mentor count and filter lists do not apply public
  profile/verification constraints. Avoid these lists for personalized
  answers; use an approved department catalogue instead.
- **Example data:** `{"counts":{"total_alumni":0,"verified_alumni":0,"total_students":0,"total_events":0,"total_jobs":0,"total_mentors":0,"total_chapters":0,"total_chapter_members":0,"total_stories":0,"total_news":0,"total_albums":0},"departments":[],"batches":[]}`.

### `GET /public/alumni`

- **Handler:** `PublicController::getAlumni`
- **Tables/fields:** Joins `alumni_profiles` to `users`. Selected profile fields:
  `id`, `user_id`, `first_name`, `last_name`, `degree`, `department`,
  `batch_year`, `graduation_year`, `current_company`,
  `current_designation`, `location_city`, `location_country`, `bio`,
  `skills`, `is_distinguished`, `distinguished_title`, `is_mentor`,
  `mentorship_topics`, `linkedin_url`, `profile_photo`,
  `show_email_public`, plus computed `public_email` and
  `users.verification_status`.
- **Visibility:** Requires `alumni_profiles.is_public_profile=1`,
  `users.status='active'`, and verification status not pending/rejected.
  Other statuses such as `unverified` are not excluded by this condition.
- **Email/phone:** `public_email` is `users.email` only when
  `show_email_public=1`; otherwise it is null. Phone is not selected. `user_id`,
  `show_email_public`, and verification status are still returned.
- **Query parameters:** Optional `search` searches first/last name, company,
  designation, skills, and city; `department`; `batch` (compared to
  `batch_year`); `mentor=1|true`; `distinguished=1|true`.
- **Sorting/pagination:** Distinguished first, then profile ID descending.
  No pagination or response limit.
- **Mode:** Read-only.
- **Example item:** `{"id":12,"user_id":34,"first_name":"Example","last_name":"Alumnus","department":"CS","batch_year":"2020","public_email":null}`; actual response includes selected fields above.
- **Error/status:** Standard success envelope; no-match returns an empty list.
- **Chatbot:** Can be a source of public professional information only after
  consuming an explicit field allowlist, dropping `user_id`, email, photo,
  verification flags, and other personal fields not needed to answer the
  question. Do not expose email or phone in chatbot replies.

### `GET /public/alumni/{idOrAlumniId}`

- **Handler:** `PublicController::getAlumniDetail`
- **Identifier:** Numeric segment is matched to `alumni_profiles.id`;
  nonnumeric segment is matched to `alumni_profiles.alumni_id`.
- **Tables/fields:** Joins `alumni_profiles` and `users`; selects
  `alumni_profiles.*`, computed consent-gated `public_email`, and
  `users.verification_status`.
- **Visibility:** Same `is_public_profile=1`, active user, and verification
  status-not-pending/rejected conditions as the directory.
- **Privacy:** Because `*` is returned, this includes fields such as phone,
  alternate email, enrollment/registration identifiers, AUID, DOB, internal
  admin notes, status/study/job details, `show_phone_public`, and profile
  visibility controls when those columns exist. `show_phone_public` does not
  redact the raw `phone` field. `alt_email` is not filtered. This is a
  verified personal-data exposure risk even for profiles flagged public.
- **Query parameters/pagination:** None.
- **Mode:** Read-only.
- **Success data example:** Object containing the full profile row and the
  computed `public_email`; specific values omitted.
- **Errors/status:** `404` with `"Alumni profile not found"` if no matching
  eligible row; otherwise standard success envelope.
- **Chatbot:** **Do not use.** It should not be exposed to a public chatbot
  before a server-side allowlist serializer removes all private fields.

### `GET /public/events`

- **Handler:** `PublicController::getEvents`
- **Tables/fields:** Reads `events.*` and computed
  `registration_count` from `event_registrations`.
- **Visibility:** `is_published=1` and `deleted_at IS NULL`.
- **Query parameters:** `filter=upcoming|past` compares `start_datetime` to
  current server time; `department` filters exact department.
- **Sorting/pagination:** `start_datetime` ascending; no pagination.
- **Mode:** Read-only. The response includes all event columns, not just public
  display fields. The migration includes internal creator, virtual link,
  registration capacity, and other fields. Registration count is derived from
  registrations.
- **Chatbot:** Public event facts may be useful, but normalize to an allowlist
  (title, type, department, description, dates, venue/virtual flag, public
  registration URL). Avoid internal creator IDs, raw virtual meeting links,
  exact attendee/registration data, and unconstrained long descriptions.

### `POST /public/events/{eventId}/register`

- **Handler:** `PublicController::registerForEvent`
- **Authentication:** Not required on the public path. On the student alias,
  the student group requires a token and the handler may associate that user.
- **Tables:** Reads `events`, `event_registrations`; writes a registration.
- **Body:** `{"attendee_name":"Example Visitor","attendee_email":"visitor@example.test","attendee_phone":"optional"}`.
- **Validation:** Event must exist, be published and not deleted; name
  required; email must be valid; registration deadline must not have passed;
  duplicate email (and authenticated duplicate user) is rejected; capacity is
  checked against total tickets.
- **Responses:** Success data contains `id` and `registration_count`.
- **Errors/status:** `400` closed registration; `404` unavailable event; `409`
  duplicate or capacity reached; `422` invalid name/email; `500` storage/write
  failure. PII is collected. Not suitable as a chatbot retrieval API.
- **Mode:** Writes private registration data including attendee name, email,
  phone, and user linkage.

### `GET /public/jobs`

- **Handler:** `PublicController::getJobs`
- **Tables/fields:** Reads `jobs.*`; adds `application_count` from
  `job_applications`.
- **Visibility:** `jobs.status='approved'` and `deleted_at IS NULL`.
  Expired deadlines are not filtered.
- **Query parameters/sorting/pagination:** None; created date descending; no
  pagination.
- **Mode:** Read-only. The response includes all job columns, including
  `contact_email`, applicant/owner identifiers, `apply_link`, and other stored
  fields. Application count is an aggregate; individual applications are not
  returned here.
- **Chatbot:** Use only sanitized job title, company, job type, location,
  experience/salary if public, description, requirements, deadline, and
  application URL. Exclude contact email, poster/user identifiers, and
  application counts. Check deadline before presenting as open.

### `GET /public/chapters`

- **Handler:** `PublicController::getChapters`
- **Tables/fields:** Reads all columns from `chapters`.
- **Visibility/sorting:** `is_active=1`; `member_count` descending.
- **Query parameters/pagination:** None.
- **Mode:** Read-only. Includes fields such as `lead_user_id`; no direct join
  resolves or exposes that person's profile.
- **Chatbot:** Suitable after dropping internal account IDs and limiting output
  to public name, city/state/country, description, and approved chapter
  contact/URL fields (if present and vetted).

### `GET /public/stories`

- **Handler:** `PublicController::getStories`
- **Tables/fields:** Reads all columns from `success_stories`.
- **Visibility/sorting:** `is_published=1`; featured descending then created
  date descending.
- **Query parameters/pagination:** None.
- **Mode:** Read-only. Migration fields include story text, associated alumni
  user ID, feature/publication flags, and views.
- **Chatbot:** Publicly published story text is a candidate source. Exclude
  `alumni_user_id` and internal fields unless specifically needed.

### `GET /public/news`

- **Handler:** `PublicController::getNews`
- **Tables/fields:** Reads all columns from `news_announcements`.
- **Visibility/sorting:** `is_published=1`; pinned descending, then
  `published_at` descending. It does not exclude future publication dates.
- **Query parameters/pagination:** None.
- **Mode:** Read-only. Includes `created_by` and publication/admin metadata.
- **Chatbot:** Suitable after allowlisting public news fields and enforcing
  `published_at` not in the future in the retrieval layer. The backend's
  current query has no future-date guard.

### `GET /public/gallery`

- **Handler:** `PublicController::getGallery`
- **Tables/fields:** Reads published `gallery_albums` and left-joins
  `event_reports`. Selected album fields: `id`, `title`, `category`,
  `cover_image`, `description`, `event_date`, `is_published`, `photos_json`.
  Selected report fields include `email_address`, `coordinators`,
  `department`, `event_type`, `event_date`, `speaker_name`, `speaker_uid`,
  `participants_count`, report details/outcomes, and report photo JSON.
- **Visibility/sorting:** `gallery_albums.is_published=1`; event date
  descending. No pagination.
- **Mode:** Read-only.
- **Privacy:** Report email and speaker UID are returned in a public endpoint.
  Content and photos may also contain personal information.
- **Chatbot:** Do not ingest raw endpoint output. Remove report email and
  speaker UID, review descriptions/photo captions, and apply an image/content
  moderation and privacy process before use.

### `GET /public/donations`

- **Handler:** `PublicController::getDonationCampaigns`
- **Tables/fields:** Reads `donation_campaigns`; for each campaign queries
  `donations` for completed donation count and total amount. Returns campaign
  columns except `created_by`, plus `total_donors` and `raised_amount`.
- **Visibility/sorting:** `is_published=1`; featured descending, created date
  descending. Donation totals include only `status='completed'`.
- **Query parameters/pagination:** None.
- **Mode:** Read-only. Donor names, contact details, messages, and individual
  transactions are not included by this endpoint.
- **Chatbot:** Public campaign titles, descriptions, goals, dates, and aggregate
  fundraising values may be suitable after verifying campaign text is
  approved.

### Public media photo routes

`GET /event-report-photo/{filename}` and
`GET /public/event-report-photo/{filename}` both call
`AdminController::getEventReportPhoto`. It applies `basename()` to the
filename and reads a file below `writable/uploads/event-reports`. It returns
the bytes with detected content type and a one-day public cache header; missing
files return `404`. The route has no authentication and does not check whether
the associated event report or gallery album is published. Treat file
publication and uploaded photo content as independently sensitive.

### Public route query parameter summary

| Endpoint | Implemented query parameters | Sort | Pagination |
|---|---|---|---|
| `/public/alumni` | `search`, `department`, `batch`, `mentor`, `distinguished` | Distinguished desc, ID desc | No |
| `/public/events` | `filter=upcoming|past`, `department` | Start datetime asc | No |
| `/admin/birthday-emails/history` | Admin-only; documented in section 8 | Created date desc, ID desc | Yes |
| Other public GET data routes | None detected | Controller-specific fixed order or unspecified | No |

## 7. Authenticated API Documentation

All write/read endpoints in this section require `Authorization: Bearer <JWT>`.
Unless stated otherwise, request body examples use JSON. The shared response
envelope applies to trait-backed responses. Exact fields not listed here are
**Not verified** rather than inferred from database columns.

### Authentication endpoints

| Endpoint | Method / access | Request and validation | Tables / effect |
|---|---|---|---|
| `/auth/login` | POST, public | JSON `{"email":"person@example.test","password":"..."}`; both required | Reads `users`, matching role profile table, `user_educations`; writes `audit_logs`; returns JWT, user identity/status, profile, education and permissions. Password is verified against stored hash and not returned. |
| `/auth/register` | POST, public | JSON. Requires valid `email`, password length >=6, `first_name`; role defaults to alumni and only student/alumni are intended. Alumni requires unique 9-digit `auid`, valid `current_status`; conditional job/study fields required. Optional DOB is valid date, not future, age 17–100. Student/alumni profile and education-specific additional fields depend on role; exact exhaustive schema is **Not verified**. | Writes `users`, `alumni_profiles` or `student_profiles`, and education/profile-related records; exact branch writes vary. Registration response varies by role/approval status. |
| `/auth/me` | GET, authenticated | No body | Reads `users`, role-specific profile, and `user_educations`; returns `user` (with `password_hash` removed), `profile`, `educations`, and `permissions`. Missing auth/user errors are `401`/`404`. |

`login` returns `data.token`, `data.user` (`id`, `email`, `role`, `status`,
`verification_status`), `data.profile`, `data.educations`, and `data.permissions`.
Registration creates accounts but does not permit self-registering as admin.

### Shared authenticated actions

| Endpoint | Method / access | Body and validation | Tables / effect |
|---|---|---|---|
| `/user/donate` | POST, any authenticated role | `campaign_id` positive and `amount` >0; optional `is_anonymous`, `donor_phone`, `message`, `payment_method`. | Reads published `donation_campaigns` and role-specific profile; writes `donations`. Donation record is marked completed by this handler. |
| `/user/jobs/{jobId}/apply` | POST, authenticated; controller restricts to alumni/student | No meaningful body fields are used by the handler. Job must be approved, not deleted, not past deadline; self-application and duplicate application are rejected. | Reads `jobs`, `job_applications`; writes `job_applications`. PII shown to job owners through separate applications routes. |

### Alumni endpoints

| Endpoint | Method | Behavior, body, and data |
|---|---|---|
| `/alumni/profile` | GET | Own profile; reads `alumni_profiles`, `users`, and `user_educations`. Returns profile columns, user email/status/verification status, and education rows. |
| `/alumni/profile` | PUT | Allows profile fields including names, contact info, work/study, public visibility and email/phone consent toggles, education summary, DOB, and social links. Department must be in `DepartmentCatalog::ALL`; current status and job type are checked; profile photo must be JPG/PNG/WEBP URL or data URL, base64 size about 2 MB max. Writes profile and `audit_logs`. |
| `/alumni/id-card` | GET | Reads or auto-generates the signed-in alumni's card from `alumni_id_cards`, `alumni_profiles`, and `users`; writes may occur on first retrieval. Exact complete response fields **Not verified**. |
| `/alumni/jobs` | POST | Requires `title`, `company_name`; accepts job posting fields including type, location, experience, salary, description, requirements, apply URL, contact email, deadline. Creates a pending `jobs` record; department comes from alumni profile. |
| `/alumni/jobs` | GET | Reads own non-deleted `jobs`, with `application_count`; ordered newest first. |
| `/alumni/jobs/{jobId}/applications` | GET | Owner-only; returns job data and applicant rows including email, role, name, contact number, and UID derived from alumni/student profile. Reads `jobs`, `job_applications`, `users`, alumni/student profiles. Private data; never chatbot content. |
| `/alumni/mentorship-requests` | GET | Reads own `mentorship_programs` joined to `student_profiles` and `users`; includes mentee email, phone, enrollment, and academic fields. Private data. |
| `/alumni/mentorship-requests/{requestId}` | PUT | Body accepts `status` (default `accepted`) and optional `notes`; updates only where request belongs to current mentor. Supported status validation is **Not verified** in this method. |

The above profile and job endpoints use `alumni_profiles`, `user_educations`,
`jobs`, `job_applications`, `users`, `alumni_id_cards`, `mentorship_programs`,
`student_profiles`, and `audit_logs` as applicable.

### Student endpoints

| Endpoint | Method | Behavior, body, and data |
|---|---|---|
| `/student/profile` | GET | Own student profile joined to `users`, plus `user_educations`, ordered by education ID. Includes own profile and email/status fields. |
| `/student/profile` | PUT | Updates only the allowed student profile fields: first/last name, phone, degree, department, current year, semester, bio, career interests, social URLs, profile photo. Department must match `DepartmentCatalog::ALL`. |
| `/student/mentorship-request` | POST | JSON requires `mentor_user_id` and non-empty `topic`; optional `message`. Writes `mentorship_programs` and mentor `notifications`. |
| `/student/my-mentorships` | GET | Reads current student's `mentorship_programs` joined with mentor profiles and users; mentor email is included. |
| `/student/my-activities` | GET | Reads current user's `job_applications` joined to `jobs` and `event_registrations` joined to `events`; matches email-only public registrations to the student's account email where user ID is null. Returns applications and event registrations. |
| `/student/events/{eventId}/register` | POST | Same event registration handler and body as the public route; auth filter requires student role. |

Student routes access `student_profiles`, `users`, `user_educations`,
`mentorship_programs`, `notifications`, `job_applications`, `jobs`,
`event_registrations`, and `events` as applicable. They expose private student
activity and contact data to the authenticated student only.

## 8. Admin API Documentation

All routes require an admin or superadmin JWT. Additional permission filters
and controller-level superadmin checks are listed in the route inventory.
Admin responses and bodies vary by operation; where the exact request schema
is not explicitly established in the inspected source, it is **Not verified**.
Admin endpoints are never suitable as a public chatbot data source.

### Admin data groups and database access

| Operations | Tables used in controller | Notes |
|---|---|---|
| Dashboard, reports, verifications, users, admins, and mentor roster | `users`, `alumni_profiles`, `student_profiles`, `admin_profiles`, `user_educations`, `alumni_id_cards`, `mentorship_programs`, `audit_logs`, and related aggregate tables | User/report methods can return detailed personal/account data; department scoping is enforced in some admin methods. Exact filters differ by method. |
| Events and event reports | `events`, `event_registrations`, `event_reports`, `gallery_albums` | Event report saves accept multipart form data and/or JSON; upload fields `photo1`–`photo4` accept JPG/PNG/WebP up to 8 MB; detailed report is 300–400 words, learning outcomes and other required metadata are checked. Saving a report creates/updates and publishes its gallery album. |
| Settings | `system_settings` | Admin CRUD; public endpoint separately exposes every setting row without a public allowlist. |
| Story/news/chapter/job/gallery CMS | `success_stories`, `news_announcements`, `chapters`, `jobs`, `gallery_albums`, related `users` | Content fields and save validation vary by handler. Read routes under `/admin` still require an admin role even when no granular permission filter is attached. |
| Donations | `donation_campaigns`, `donations` | Campaign management and donation records. Donations include donor PII. |
| Audit logs | `audit_logs`, and possibly joined `users` | Contains IP, user-agent, action, and target details; sensitive operational data. |
| Birthday email settings/history | `birthday_email_settings`, `birthday_email_logs`, `users`, `alumni_profiles` | Test sends use fixed recipient, and are rate-limited to one per minute. History supports pagination/status/search. |

### Birthday email endpoints

These are admin-only and require `manage_birthday_emails`.

| Endpoint | Method | Verified request/query and response |
|---|---|---|
| `/admin/birthday-emails` | GET | Returns template `subject`, `message_body`, `is_enabled`, `last_run_at`, sent/failed counts, and fixed test recipient. |
| `/admin/birthday-emails` | PUT | JSON requires `subject` (non-empty, <=255 chars, no line breaks), `message_body` (non-empty, <=10,000 chars), and boolean-like `is_enabled`. Writes settings. |
| `/admin/birthday-emails/preview` | POST | JSON `subject` and `message_body` validated as above; returns rendered preview. |
| `/admin/birthday-emails/test` | POST | Requires JSON object; if template fields are supplied they are validated, else stored template is used. SMTP misconfiguration returns `503`, throttled request `429`, send failure `502`; successful sends return recipient. |
| `/admin/birthday-emails/history` | GET | Query: `page` (minimum 1), `per_page` in 10/20/50 else defaults to 20, `status=sent|failed`, `search` truncated to 100 chars. Returns `items` and pagination `{page,per_page,total,total_pages}`. Includes recipient email, subject, error text, status, and alumni name. |

The history and settings endpoints are private. Their outputs must never be
fed to the public chatbot.

### Admin API behavior and payload certainty

The exact per-field JSON schemas for many admin CRUD methods are implemented
inside a large `AdminController` rather than a central OpenAPI/schema file.
The method names and permission filters are verified in the route inventory;
every field, validation boundary, and error code for all 53 admin route
patterns is **Not verified in this reference** unless described above. Consult
the named controller method before building an admin integration; do not infer
write payloads from database columns alone.

## 9. Database Tables and Relationships

The migrations establish these tables and logical relationships. Foreign-key
constraints are explicitly declared only where noted; many links are
application-level IDs rather than enforced foreign keys.

| Table(s) | Main fields / relationship relevant to APIs |
|---|---|
| `users` | Unique email, password hash, role, status, verification status, timestamps/soft delete. Profile tables link by `user_id`. |
| `alumni_profiles` | User profile, academic/work/location data, phone/alternate email, public-profile and contact visibility flags, admin notes; links to `users.id`. Later migrations add AUID/alumni ID, DOB, gender and status fields. |
| `student_profiles` | Student identity, enrollment, degree/department, year/semester, phone, bio/career data; links to `users.id`. Gender added later. |
| `admin_profiles` | Admin identity, department, designation, phone and permission JSON; links to `users.id`. |
| `user_educations` | Education rows with `user_id`, level, degree, department, years, grades/research; one-to-many from user. |
| `events` | Event text/type/department, virtual/venue details, schedule, registration deadline/capacity, publication flag, soft-delete, creator. |
| `event_registrations` | `event_id`, optional `user_id`, attendee name/email/phone, tickets/check-in fields. Application joins to events and user. |
| `jobs` | Job data, contact email, deadline, poster user, department, status, soft-delete. |
| `job_applications` | `job_id`, `user_id`, timestamps; unique composite `(job_id,user_id)` per migration. |
| `mentorship_programs` | Mentor and mentee user IDs, topic, message, notes, status, timestamps. |
| `chapters` | Name/location/description, lead user ID, member count, active flag. |
| `success_stories` | Story content, optional alumni user ID, publication and featured flags. |
| `news_announcements` | News content/category, publication/pinned flags and dates, creator. |
| `gallery_albums` | Album metadata, publication flag; later migration adds event ID and photo JSON. |
| `event_reports` | Unique event association, coordinator/report contact, speaker/batch/participant data, detailed report, outcomes, photo JSON. Joined by `event_id`. |
| `system_settings` | `setting_key` and `setting_value`; public settings handler reads every row. |
| `donation_campaigns` | Public campaign content/goal/date/publication fields, creator. |
| `donations` | Campaign/user links, donor name/email/phone, amount/message, transaction/status/anonymity data. |
| `audit_logs` | User, role, action, target, IP, user-agent, details, timestamp. |
| `notifications` | User-linked message, type, read status. |
| `alumni_id_cards` | User-linked card number, issue/expiry, QR payload and status. |
| `birthday_email_settings` | One-row-style subject/body/enable and send timestamps. |
| `birthday_email_logs` | User/year, recipient, subject, status, error and timestamps; unique user/year; user FK uses cascade/set-null. |

### Migration verification limits

Migrations in this repository define the above structures, including later
schema changes. Migration files are not proof that every migration has been
run in the live database, and no live schema introspection was performed.
Unique constraints or relationships not stated above are **Not verified**.

## 10. Public Data and Visibility Rules

| Public source | Actual inclusion condition |
|---|---|
| Alumni list/detail | `alumni_profiles.is_public_profile=1`; joined user `status='active'`; verification status not `pending` or `rejected`. |
| Events | `events.is_published=1` and `deleted_at IS NULL`. |
| Jobs | `jobs.status='approved'` and `deleted_at IS NULL`; no deadline/expiry condition in public list. |
| News/announcements | `news_announcements.is_published=1`; no future `published_at` exclusion. |
| Stories | `success_stories.is_published=1`. |
| Gallery | `gallery_albums.is_published=1`; joined report columns have no independent publication filter. |
| Chapters | `chapters.is_active=1`. |
| Donation campaigns | `donation_campaigns.is_published=1`; aggregate donation totals include `donations.status='completed'`. |
| Public settings | No allowlist or visibility condition. All rows in `system_settings` are returned. |
| Stats | Counts use varying conditions; department/batch lists filter only for non-null and include hidden profiles. See `GET /public/stats`. |

These rules are read directly from the public controller implementation, not
inferred from field names. In particular, jobs are filtered by `status`,
chapters by `is_active`, and alumni by profile/user visibility checks rather
than a universal `is_published`.

## 11. Alumni Privacy Analysis

- Alumni profiles have `is_public_profile`, `show_email_public`, and
  `show_phone_public` controls in migration schema. The alumni profile update
  endpoint accepts changes to these controls. `is_public_profile` defaults to
  true in the base migration; email/phone display flags default false.
- The source confirms visibility toggles, not a separate affirmative consent
  workflow or consent audit trail. Whether the current default-public setting
  is backed by valid user consent is **Not verified**.
- The directory respects `is_public_profile` and uses `show_email_public` to
  conditionally populate `public_email`. It does not return the `phone` column.
- The detail endpoint returns `alumni_profiles.*`, including raw phone and
  alternate email, and also returns other sensitive/internal fields. It does
  not redact phone according to `show_phone_public`. The returned
  `public_email` is consent-gated, but other email fields are not.
- The field `show_phone_public` exists but is not used to protect the phone
  field in the current public detail response.
- Alumni must be active and not pending/rejected to appear, but `unverified`
  verification is not excluded by the current predicate.
- A public profile flag is not an equivalent privacy review/consent process for
  every field. Do not use the raw public detail response for chatbot grounding.
- **Safe chatbot fields** should be limited to approved, explicitly public
  professional details (for example display name, degree/department,
  graduation/batch year, company/designation, city/country, skills and approved
  public biography). Do not use email, phone, alternate email, AUID/alumni ID,
  enrollment/registration identifiers, DOB, private profile fields,
  admin notes, account identifiers, or raw social/contact data unless a
  separately vetted public policy specifically permits it.

## 12. AI CHATBOT INTEGRATION ANALYSIS

Architecture under consideration:

```text
React Chatbot UI -> Python FastAPI -> CI4 Public APIs -> MySQL
                                       + PDF-based RAG knowledge base
```

FastAPI should retrieve only approved public content through CI4. It must not
connect directly to MySQL or call authenticated/admin routes. Keep the PDF RAG
corpus and live records as separate evidence sources and identify which source
supports each answer.

### Category-to-endpoint mapping

| Category | Existing API | Verified public data / condition | Public access | Chatbot suitability |
|---|---|---|---|---|
| Events | `GET /public/events` | Published, non-deleted `events`; supports upcoming/past and department filters. | Yes | **Conditional.** Sanitize `events.*`; avoid raw internal IDs, report/registration information, and private virtual links. No pagination. |
| Jobs | `GET /public/jobs` | Approved, non-deleted jobs. | Yes | **Conditional.** Remove contact email/poster IDs and application count; reject expired deadlines. No pagination. |
| Alumni | `GET /public/alumni`; detail `GET /public/alumni/{id}` | Directory honors public profile and active/non-pending/rejected account; optional email consent. Detail leaks full profile row. | Yes | **Directory only, after allowlisting and PII removal.** Detail endpoint is unsuitable until fixed. |
| Departments | No dedicated department endpoint. `GET /public/stats` includes distinct alumni-profile department values; `DepartmentCatalog` is validation code, not an API. | Stats department list includes private/unverified alumni and may not list every university department. | Partial | **Not suitable as an authoritative catalog.** Obtain a separately approved department list; do not assume stats list is complete or safe. |
| Announcements | `GET /public/news` | Published `news_announcements`, but future `published_at` values are not excluded. | Yes | **Conditional.** Filter future content and allowlist public text. No pagination. |
| News | `GET /public/news` | Same endpoint/table as announcements. | Yes | **Conditional**, same future-date and payload constraints. No separate news/announcement routes. |
| Stories | `GET /public/stories` | Published `success_stories`. | Yes | **Conditional.** Use public story fields and exclude user IDs/internal metadata. |
| Gallery | `GET /public/gallery` | Published albums joined with event reports. | Yes | **Not suitable raw.** Response includes report email and speaker UID; review image/caption content. |
| Chapters | `GET /public/chapters` | Active chapters, ordered by member count. | Yes | **Conditional.** Remove internal lead user ID and use public fields only. |
| Statistics | `GET /public/stats` | Aggregates plus department/batch lists, with some counts/lists broader than public profile rules. | Yes | **Conditional.** Limit to non-sensitive approved aggregates; do not use student counts or private-derived dept/batch lists without privacy review. |

### Reuse and remediation

- **Potentially reusable after payload allowlisting:** events, jobs, alumni
  directory, news/announcements, stories, chapters, and donation campaigns.
- **Not suitable raw:** alumni detail, settings, gallery, and stats as a
  department/student-profile source. The photo media route should not be used
  to ingest arbitrary event report photos.
- **Required improvements before public chatbot use:** server-side field
  allowlists for `events.*`, `jobs.*`, alumni details and gallery report join;
  public settings key allowlist; filter future news; expire jobs; review the
  verification rule for alumni; redact/remove contact and identifiers;
  enforce bounded response size and public profile-field policy.
- **Missing category API:** a dedicated approved department directory.
- **Response simplification:** return compact, stable records with only
  question-answer-relevant fields, normalized timestamps, source IDs/URLs
  suitable for citations, and no internal IDs or PII.
- **Pagination/limits:** none of the public list APIs implement pagination or
  limits. Add server-side bounds before relying on them for chatbot requests;
  do not rely on client-side truncation to protect the backend.
- **Never retrieve:** student registrations/profiles, alumni private fields,
  contact information, mentorship requests, job applicants/applications,
  admins/permissions, audit/activity logs, unpublished records, or settings
  without an allowlist.

## 13. Live Data Fetching Strategy

FastAPI can make fresh HTTP requests to the deployed CI4 public API whenever a
user asks a question. Source changes committed to MySQL and made visible by a
public API become available on the next successful API request; the language
model does not need retraining. The PDF RAG index is separate and needs its own
refresh process when PDF sources change.

| Setting | Recommendation / verified value |
|---|---|
| API root | Configure per environment; local source config establishes `http://localhost:8080/api`. |
| Paths | Use only approved public GET paths listed above. |
| Headers | `Accept: application/json`; `Content-Type` is unnecessary for GET. No authorization header required for public GETs. |
| Query | `search`, `department`, `batch`, `mentor`, `distinguished` only for alumni; `filter`, `department` only for events. Other public list endpoints currently have no implemented query filters. |
| Pagination | Not supported on the public list routes. Keep response sizes bounded at a proxy/service layer until the CI4 endpoints support limits. |
| Timeout | Set a bounded connect/read timeout (for example 5 seconds connect and 10 seconds total); tune from deployment measurements. This is a recommendation, not a CI4 requirement. |
| Freshness | Fetch on user request or use a short explicitly bounded cache (for example 30–60 seconds) with cache invalidation/expiry. Avoid long-lived embeddings of changing database records. |
| Failures | Handle timeout, network, non-2xx, invalid JSON, and `status:false` explicitly. Do not tell users a failed fetch was current; respond with an availability caveat or use only separately timestamped cached data. |
| Cache policy | Event photo endpoint sets public max-age 86400; data JSON endpoints do not set explicit cache headers in their controller implementations. Intermediary defaults are **Not verified**. Use request-level revalidation/no-cache policy for live chatbot retrieval. |

`Config/Filters.php` also lists `pagecache` as a required before/after filter.
Whether and how it caches these API responses depends on the CI4 filter/runtime
configuration and has not been measured. Verify cache behavior in the target
deployment and exclude live chatbot data paths from stale page caching or
ensure its TTL is acceptably short.

The chatbot should record retrieval timestamps and source URLs internally for
answer traceability, while keeping user-visible citations to public content
pages. Do not cache private data, and do not send raw API responses directly to
the model.

## 14. Security Analysis

| Risk | Source evidence / impact | Recommendation |
|---|---|---|
| Hard-coded JWT signing secret | `JwtService` embeds signing material in source. Anyone with source access can forge tokens; rotating it invalidates issued tokens. | Move to a secret manager/environment configuration, rotate immediately if deployed, validate key length/rotation strategy, and invalidate old tokens. Secret value is intentionally not reproduced. |
| Public alumni detail returns private fields | `alumni_profiles.*` includes raw phone, alternate email, identifiers, DOB/admin notes and other fields; phone visibility flag is not enforced there. | Replace wildcard select with an explicit public projection; redact fields server-side; test with an account whose consent flags are false. |
| Public alumni directory leaks metadata | Exposes user/profile IDs, verification status, email visibility flag; email may be returned when opted in. | Remove internal identifiers/flags; do not return email to chatbot; confirm and document consent semantics. |
| Public settings has no allowlist | Every setting row is returned. A future/private setting would be exposed automatically. | Maintain an explicit public-key allowlist or dedicated public settings projection. |
| Public event response is `events.*` | May include internal creator, private virtual link, capacity, and other non-display data; registration count is inferred from private registrations. | Use explicit public projection, review link/access semantics, and remove unnecessary aggregate fields. |
| Public jobs returns `jobs.*` | Includes `contact_email`, poster IDs and other fields; approved deadline may have expired. | Explicit public projection, no personal contact disclosure by default, expiry filter and response limit. |
| Public gallery includes report PII | The join explicitly returns report email, coordinators, and speaker UID; content/photos can also reveal people. | Remove those fields from public serializer; obtain content consent and moderate uploaded photos. |
| Stats include data beyond public profiles | Student counts lack active-state condition; department/batch and mentor counts do not consistently enforce public/verified visibility. | Define privacy-reviewed aggregate metrics and use consistent visibility conditions. |
| Missing pagination/response caps | Public list endpoints can return every matching record and large text/photos. | Add pagination, max page sizes, field-size limits, caching and abuse monitoring. |
| Public content publication edge cases | News endpoint lacks future publication filter; jobs list lacks deadline filter; media route does not verify associated report/album publication. | Add publication-time/expiry/asset visibility checks and regression tests. |
| Public registration abuse | Event registration accepts anonymous name/email/phone and creates records; capacity/de-duplication checks exist but API-level rate limiting is not configured in project filter config. | Apply per-IP/event rate limits, CAPTCHA/abuse controls as appropriate, input size limits, monitoring and retention policy. |
| CORS | Global CORS filter enabled. Config allows `localhost:5173`, `127.0.0.1:5173`, `localhost:3000`, credentials, common headers/methods. | Restrict origins to trusted deployed frontends; review credentials policy. CORS is not authentication and does not stop non-browser clients. |
| API rate limiting | No general API rate-limit filter is registered in `Config/Filters.php`; birthday email test has its own one-per-minute DB throttle. | Add global/per-route rate limits, especially login, registration, public forms, directory/search and media. |
| Auto-routing/filter scope | `Config/Routing.php` sets `$autoRoute=false`; route file explicitly declares methods. | Keep auto-routing disabled and test unauthorized HTTP verbs on deployment. |
| Admin authorization | Admin group is role-gated; some methods have no granular filter, while critical mutations use route permissions or controller checks. | Audit every method's object/department scope and write authorization; do not infer safety from admin group alone. |
| Authenticated PII endpoints | Student/alumni own profile, mentorship and application routes legitimately return sensitive data to authenticated users. | Keep behind JWT/role/ownership checks; never proxy these endpoints to chatbot. |

## 15. API Testing Examples

These commands use the locally configured API base. They test public reads
only; no credentials or write requests are needed. Responses should contain
`status`, `message`, `data`, and `errors`. Actual database values vary.

### Settings

Browser: `http://localhost:8080/api/public/settings`

```powershell
Invoke-RestMethod -Method Get -Uri 'http://localhost:8080/api/public/settings' -Headers @{ Accept = 'application/json' }
```

Verify `data` is a key/value map. **Do not assume the keys are safe for
chatbot use.**

### Statistics

Browser: `http://localhost:8080/api/public/stats`

```powershell
Invoke-RestMethod -Method Get -Uri 'http://localhost:8080/api/public/stats' -Headers @{ Accept = 'application/json' }
```

Verify `data.counts`, `data.departments`, and `data.batches`; compare count
conditions to the rules in section 6.

### Alumni directory

Browser: `http://localhost:8080/api/public/alumni?department=CS&batch=2020`

```powershell
Invoke-RestMethod -Method Get -Uri 'http://localhost:8080/api/public/alumni?search=engineer&department=CS&batch=2020&mentor=true' -Headers @{ Accept = 'application/json' }
```

Verify `data` is an array and check that `public_email` is null when
`show_email_public` is false. Do not test by exposing real alumni PII in logs.

### Alumni detail

Browser: `http://localhost:8080/api/public/alumni/1`

```powershell
Invoke-RestMethod -Method Get -Uri 'http://localhost:8080/api/public/alumni/1' -Headers @{ Accept = 'application/json' }
```

Expected: `data` is a profile object or `404`. This endpoint returns sensitive
columns under current source; use only in a controlled security verification,
not in the chatbot.

### Events

Browser: `http://localhost:8080/api/public/events?filter=upcoming`

```powershell
Invoke-RestMethod -Method Get -Uri 'http://localhost:8080/api/public/events?filter=upcoming&department=CS' -Headers @{ Accept = 'application/json' }
```

Verify records satisfy `is_published=1`, `deleted_at=null`, and upcoming
`start_datetime`; response rows include `registration_count`.

### Jobs

Browser: `http://localhost:8080/api/public/jobs`

```powershell
Invoke-RestMethod -Method Get -Uri 'http://localhost:8080/api/public/jobs' -Headers @{ Accept = 'application/json' }
```

Verify `status=approved`, no soft-deleted record, and inspect deadlines.
Response includes all job columns and `application_count`, so avoid sharing
raw output.

### Chapters

Browser: `http://localhost:8080/api/public/chapters`

```powershell
Invoke-RestMethod -Method Get -Uri 'http://localhost:8080/api/public/chapters' -Headers @{ Accept = 'application/json' }
```

Verify every row has `is_active=1`; inspect output for internal lead IDs.

### Stories

Browser: `http://localhost:8080/api/public/stories`

```powershell
Invoke-RestMethod -Method Get -Uri 'http://localhost:8080/api/public/stories' -Headers @{ Accept = 'application/json' }
```

Verify `is_published=1` and inspect public text/image fields.

### News and announcements

Browser: `http://localhost:8080/api/public/news`

```powershell
Invoke-RestMethod -Method Get -Uri 'http://localhost:8080/api/public/news' -Headers @{ Accept = 'application/json' }
```

Verify `is_published=1`, ordering by pinned/published date, and check future
`published_at` rows are not presented prematurely.

### Gallery

Browser: `http://localhost:8080/api/public/gallery`

```powershell
Invoke-RestMethod -Method Get -Uri 'http://localhost:8080/api/public/gallery' -Headers @{ Accept = 'application/json' }
```

Verify `is_published=1`; check that joined report email and speaker UID fields
are not sent into chatbot retrieval.

### Donation campaigns

Browser: `http://localhost:8080/api/public/donations`

```powershell
Invoke-RestMethod -Method Get -Uri 'http://localhost:8080/api/public/donations' -Headers @{ Accept = 'application/json' }
```

Verify campaigns are published and aggregate totals only count completed
donations. No donor-level records should appear.

### Public report photo

Browser: `http://localhost:8080/api/event-report-photo/{filename}`

```powershell
Invoke-WebRequest -Method Get -Uri 'http://localhost:8080/api/event-report-photo/{filename}'
```

Replace `{filename}` with a known test asset. This endpoint returns binary
content, not the standard JSON envelope; absent files return `404`.

## 16. Missing APIs and Limitations

- No dedicated public API for an authoritative department catalogue. The
  stats endpoint's department list is derived from all non-null alumni
  departments, including profiles not publicly visible.
- No separate announcements endpoint: `/public/news` reads the combined
  `news_announcements` table.
- Public content lists do not implement pagination or response caps.
- No public API exposes a safe, consent-aware alumni detail projection distinct
  from the current `alumni_profiles.*` endpoint.
- No OpenAPI/Swagger specification or centralized API request/response schema
  was found in the inspected project.
- No general API rate-limit filter is configured.
- The live database contents, migration state, actual deployed host, and
  production proxy/cache behavior are **Not verified**.
- Exact per-field schemas and response structures for every admin mutation
  were not exhaustively verified here; consult each controller method before
  writing an admin client.

## 17. Recommendations

1. Do not connect chatbot code directly to MySQL or authenticated/admin routes.
2. Before integration, fix the alumni-detail wildcard exposure and audit every
   public wildcard/whole-row response (`settings`, events, jobs, chapters,
   stories, news, gallery).
3. Use server-side field allowlists and never send email, phone, IDs, student
   information, mentorship, applications, or audit data to the model.
4. Require privacy review/approval of source records and publication dates;
   filter future news and expired jobs.
5. Add pagination, hard response limits, rate limits, request timeouts,
   logging/monitoring with PII-safe logs, and cache policy.
6. Restrict CORS origins to deployed frontends and treat CORS only as a browser
   policy, not an API security boundary.
7. Move JWT signing secrets out of source, rotate the deployed value, and
   assess issued tokens.
8. Add automated tests for anonymous access, role/permission denial,
   ownership/department scopes, consent flags, publication filters, PII
   absence, and response size.
9. Have FastAPI normalize results into compact chatbot-specific records with
   provenance, retrieval time, and user-safe citations. Never provide raw
   database rows to the model.

## 18. Final Chatbot Integration Readiness Report

**Overall readiness: Not ready for direct public chatbot integration.**

There are public read APIs for events, jobs, alumni, news/announcements,
stories, gallery, chapters, statistics, and donation campaigns. Several are
useful as source material, but the current API does not provide a consistently
safe chatbot contract: the alumni detail returns private profile fields, the
public settings endpoint returns all settings, gallery exposes report contact
and speaker identifiers, and several list endpoints return complete rows
without pagination. Publication rules also omit future-news and expired-job
checks. A chatbot can be made safer by consuming only sanitized, allowlisted
fields after the API visibility issues are resolved; no API changes are made
as part of this documentation task.

- **Total existing API routes:** 87 declarations (86 explicit HTTP route
  patterns plus the catch-all OPTIONS route).
- **Total public GET APIs:** 13 route patterns: 11 public content/data GET
  routes and two public event-report-photo routes.
- **Public GET APIs suitable for chatbot:** 0 fully safe for unfiltered direct
  consumption. Up to 9 public content/data sources, including donation
  campaigns, are conditional candidates after server-side field allowlisting
  and the mitigations above; public photo routes are not counted as chatbot
  data APIs.
- **APIs requiring security/visibility improvements:** 9 public data routes
  flagged for field minimization, privacy, or publication/expiry handling:
  `/public/settings`, `/public/stats`, `/public/alumni`,
  `/public/alumni/{idOrAlumniId}`, `/public/events`, `/public/jobs`,
  `/public/chapters`, `/public/news`, and `/public/gallery`. The two
  event-report-photo route patterns also need a publication/visibility check.
- **Missing API categories:** a dedicated authoritative public department
  catalogue. News and announcements share the existing `/public/news` API.
- **Readiness decision:** integrate only after privacy/security remediation,
  bounded responses, rate limiting, and tests confirming that no private,
  unpublished, or unapproved data reaches FastAPI or the model.
