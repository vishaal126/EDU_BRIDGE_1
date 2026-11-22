# EduBridge AI

A Streamlit peer-learning prototype for students and tutors.

## Run on Windows

1. Extract the ZIP archive.
2. Open the **EduBridgeAI** folder in VS Code (the folder that contains `app.py` and `requirements.txt`).
3. Open **Terminal → New Terminal**.
4. (Recommended) Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
5. Install dependencies from this folder:
   ```powershell
   python -m pip install -r requirements.txt
   ```
6. Start the app:
   ```powershell
   python -m streamlit run app.py
   ```
7. Open the local URL printed by Streamlit, usually `http://localhost:8501`.

> If your terminal is in the outer extracted folder instead, run `python -m pip install -r .\EduBridgeAI\requirements.txt`, then `cd EduBridgeAI` before starting Streamlit.

## Updated features

- **Tutor + Skill Swap:** Students and tutors can invite another learner into a two-way skill exchange. Invitations can be accepted or declined; accepted groups appear in active exchanges. The same page includes problem-based tutor matching.
- **Problem-based tutor matching:** Students describe what they understand and where they are stuck. Tutors are ranked using skill/profile keyword overlap, XP as a secondary signal, and declared teaching languages. Students can request regular tutoring, a 10-minute introductory trial, or urgent 10-minute help.
- **Doubt support:** Students can use an offline guided problem-solving helper, post doubts for tutor replies, and mark urgent 10-minute help requests. Tutors see urgent doubts first and can respond from the Tutor replies tab.
- **Tutor sessions:** Tutors can accept or decline requests. The app records the requested duration and preferred language. It does not host live video or voice calls; students and tutors coordinate through Messages.
- **Session notes:** After an accepted session, tutors can save concepts, simple explanations, practice questions, homework, and next-session goals. Students can view those notes under My Sessions & Notes.
- **Local-language preferences:** Students and tutors can choose English, Telugu, Hindi, Tamil, Kannada, Malayalam, Bengali, Marathi, or Other in their profile.
- **XP & leaderboard:** Challenge XP is awarded after peer review, not by a one-click completion button.
- **Learning Rooms:** Room creation, unique room codes, joining with a code, member lists, and room posts/resources are supported. Existing rooms receive codes during database migration.
- **Opportunities:** The section remains removed from the navigation and dashboard.

## AI and prototype limitations

The doubt solver in this build is an offline guided tutor with topic-aware examples; it does **not** call a hosted generative-AI model. Tutor matching is keyword/profile based, not a trained recommendation model. Local-language preferences help match students with tutors who declare those languages; the built-in doubt solver does not translate answers. Trial and urgent sessions are requests for a 10-minute session, not a built-in video call or guarantee of immediate tutor availability. Smart notes are structured and saved by the tutor after the session; they are not automatically transcribed from a call.

## Data and upgrades

The app creates `edubridge.db` beside `app.py`. Existing databases are upgraded automatically with language preferences, room codes, skill-swap memberships, tutor sessions, doubt posts/replies, and session notes. **Back up your existing `edubridge.db` before replacing your old project.** Do not delete the database if you want to keep existing accounts and records.

This is a prototype. Account contact details are not OTP-verified, and peer-review decisions are not suitable as a high-stakes credential without stronger moderation.

---

# EduBridge v2 upgrade

This version keeps every existing feature (profiles, learning rooms, doubt solver, session notes, portfolio, XP/leaderboard, messages) and adds the marketplace, EduCoins, AI courses and mind maps. Same `edubridge.db`; new tables and columns are added automatically on start (**back up your `edubridge.db` first**).

## What is new

| Area | Where | Notes |
|---|---|---|
| Tutor dashboard | *Tutor Dashboard* | Profile + subjects, hourly/weekly/monthly pricing, availability, offline/online requests, students, earnings, reviews, booking history |
| Offline meetings / Online classes | *Offline Meetings*, *Online Classes* | Search, filters, tutor cards, price plans, slot picker, booking request |
| Booking workflow | *My Bookings* | Pending -> Accepted -> Confirmed -> Completed (or Rejected / Cancelled) |
| Location-based price guidance | Tutor pricing tab + tutor cards | Clearly labelled *estimate*; never changes a tutor's price |
| EduCoins | *EduCoins Wallet* | Ledger-based, server-side only, duplicate-proof, cannot go negative |
| AI courses | *AI Courses* | Needs `ANTHROPIC_API_KEY` |
| AI mind maps | *AI Mind Maps* | Needs `ANTHROPIC_API_KEY` |
| Skill swap | *Tutor + Skill Swap* | Matching, requests, auto-created swap rooms, scheduling, two-sided completion, coin rewards |

## Configuration (environment variables)

Set these in your terminal before `streamlit run`, or in `.streamlit/secrets.toml` (never commit it):

```powershell
$env:ANTHROPIC_API_KEY="sk-ant-..."        # AI courses, mind maps, branch explanations
$env:EDUBRIDGE_AI_MODEL="claude-sonnet-5-5" # optional override
$env:RAZORPAY_KEY_ID="rzp_test_..."         # payments
$env:RAZORPAY_KEY_SECRET="..."
```

Without `ANTHROPIC_API_KEY` the AI pages show a setup message and generate nothing. Without Razorpay keys, bookings that need payment stay at *Accepted* (they cannot be marked paid); bookings fully covered by EduCoins confirm without payment.

## How the important rules are enforced

* **Payments:** the app creates a Razorpay *Payment Link* on the server. A booking becomes *Confirmed* only after the server asks Razorpay whether that link was paid **for the exact amount**. The browser never reports success.
* **EduCoins:** one append-only ledger (`coin_txns`). Balance = sum of rows. Spending runs in a `BEGIN IMMEDIATE` transaction that checks the balance. A unique key on (user, kind, reference) stops duplicate rewards/refunds. There is no UI to grant coins.
* **Coin rewards** (see `services.py` constants): verified swap session (both partners confirm; caps per day and per pair), reply marked helpful by the asker, peer-approved challenge.
* **Authorisation:** every service function takes the acting user and re-checks role, ownership and current status.
* **Video classes:** each confirmed online booking gets an unguessable Jitsi Meet room (free, no key). It is as private as the link.

## Not built / needs a decision from you

1. **Paying tutors out.** The app records what each tutor earned; moving money to tutors (Razorpay Route/Payouts, bank details, KYC, commission) is not implemented.
2. **Who funds EduCoins paid to tutors.** Coins used for a booking reduce the student's price; nothing credits those coins to the tutor. You must decide how coin value is settled (e.g. you pay the tutor the rupee value).
3. **Refunds of paid bookings.** Cancelling a paid booking marks it `refund_due`; the refund itself is done in the Razorpay dashboard.
4. **Payment webhooks.** Verification happens when the student presses *Verify payment*. A webhook would confirm automatically but needs a public server URL.
5. **Real market prices.** Price guidance comes from the rate tables in `pricing.py` (city tiers, category base rates, experience, qualifications, demand keywords, online discount, travel fee). They are starting values to edit, not live data. Only the cities in `pricing.CITIES` get distances; others show "distance unknown". Prices are INR only, including for non-India countries (shown as converted estimates).
6. **EduCoin "learning resources".** There is no resource catalogue to redeem against yet.
7. **Weekly/monthly plans** book the first session slot; remaining dates are agreed in Messages.
8. **Coin farming.** Caps and two-sided confirmation reduce it, but two friends can still collude. Add moderation or identity checks before real value is attached to coins.
9. **PDF export of mind maps** uses the browser's print dialog. PNG export is attempted in-browser; SVG and Markdown downloads are generated by the server.
10. **Sign-up is still not OTP-verified**, and passwords/sessions are as in the original prototype. Streamlit has no built-in API layer, so "role-based authorisation" lives in `services.py`.

## Tests

```powershell
python -m unittest tests.test_services -v
```
Covers pricing, bookings, slot double-booking, EduCoins (no negative balance, no duplicates, refunds), payment verification with a mocked Razorpay, swap rooms/sessions/rewards, AI quota and course ownership.

## Files

`app.py` (existing app, extended) · `services.py` (backend rules) · `pricing.py` · `ai_client.py` · `mindmap_view.py` · `ui_market.py` · `ui_ai.py` · `tests/`

---

# v2.1 fixes and new look

**Fixed**
* **Learning Rooms crashed** with `TypeError: cannot pickle 'sqlite3.Row' object` right after creating/joining a room (Python 3.14 can no longer copy `sqlite3.Row`, and Streamlit copies dropdown options). All database rows are now plain-dict based (`services.Row`), which also fixes the same hidden crash in the peer pickers, Messages, skill-swap, AI course and mind-map dropdowns. Regression test added.
* **AI Courses / AI Mind Maps "need an API key" dead end.** Both pages now show a *Connect AI* box where you paste your Anthropic key for the session (kept in server memory only). The Generate buttons stay disabled until a key exists. Permanent options: `ANTHROPIC_API_KEY` environment variable, `.streamlit/secrets.toml` (copy `secrets.toml.example`), or just run `run_windows.bat`, which asks for it. Clearer errors for rejected keys, unknown models and rate limits.
* **My Sessions & Notes** told you to use a non-existent "Find a Tutor" page; the empty state now has a button that opens *Tutor + Skill Swap*.

**New look** (`theme.py`): animated gradient background, glass cards with hover lift, icon navigation with an active-page highlight, profile card in the sidebar, gradient buttons/tabs/progress bars, clickable dashboard cards, friendly empty states, toasts, a medal leaderboard, and confetti when a course is generated. Honors "reduce motion" and works on phones.


---

# v3: real sign-in (futuristic login integrated)

The animated EduBridge login/register screen from `Hackton login.html` is now the app's real front door.
It runs as a **Streamlit custom component** (`auth_component/index.html`, a single self-contained file with CSS and JS inlined) and talks to
the Python backend (`auth_ui.py` -> `auth_service.py`). The browser only asks; the server decides.

## What changed (and what did not)

* **Same database, same accounts.** Existing rows in `users` are untouched. Existing PBKDF2 hashes (`salt$hex`, 100 000 rounds)
  verify exactly as before. Only **new tables** are added on start: `auth_identities`, `oauth_states`, `auth_sessions`,
  `password_resets`, `auth_attempts`. Back up `edubridge.db` anyway before upgrading.
* **Sign in** with email *or* mobile number (as before) plus the Student/Tutor switch. A role mismatch is reported only after
  the password is correct.
* **Register** needs name, email, password (8+ characters, upper + lower case and a number or symbol), confirmation and
  the terms box. A real `users` row is inserted with the same defaults as before (XP 0, language English, city/state/country,
  optional skills). Nothing is stored in browser storage. The new user is signed in only after the insert commits.
* **Sessions are server-side.** `st.session_state.uid` is set only after real authentication, and every page load re-checks a
  hashed token in `auth_sessions`. Without "Remember me": 12 h. With it: 30 days. Sign-out and password reset revoke sessions.
* **Google / GitHub:** real OAuth 2.0 / OIDC, configured in `GOOGLE_SETUP.md`. Not configured = clear message, never a fake login.
* **Forgot password:** emailed single-use link (SMTP), hashed token, 30-minute expiry, all sessions revoked on use.
* The old Streamlit sign-in/sign-up forms were replaced; every other page is unchanged.

## Run

```powershell
python -m pip install -r requirements.txt
copy .streamlit\secrets.toml.example .streamlit\secrets.toml   # then edit it (see GOOGLE_SETUP.md)
python -m streamlit run app.py
```
Needs Streamlit 1.40 or newer (uses `st.context.cookies` and `st.query_params`).

## Security notes and honest limits

* **Account linking:** a social login whose verified email matches an existing *password* account is **not** linked
  automatically (that email was never verified when the password account was made). The user must enter that account's password once.
  If the account's email was already verified by another provider, it links silently. One Google/GitHub identity maps to one account.
* **OAuth hardening:** one-time `state` (hashed in DB, 10 min), `nonce`, PKCE (Google), and a browser-binding cookie so a callback
  cannot be replayed into a different browser. The ID token is verified server-side; the browser never supplies identity data.
* **Remember me cookie (`eb_rt`):** Streamlit cannot set HttpOnly cookies, so this cookie is written by the component's JavaScript
  (`SameSite=Strict`, `Secure` on HTTPS). It holds a random 256-bit token; only its hash is stored, it expires server-side,
  and it is deleted on sign-out. Because it is not HttpOnly, an XSS bug elsewhere in the app could read it. Do not
  render untrusted HTML with `unsafe_allow_html`.
* **Rate limiting:** 5 failed sign-ins per identifier per 15 minutes (this also means someone can lock out a known email for
  15 minutes), 3 reset emails per address per hour.
* Email/phone ownership is still not verified at sign-up (as in the original prototype). Phone-only legacy accounts can sign in
  and reset-by-email is only available to accounts that have an email.
* The sign-in screen is a full-viewport iframe. Opening the app inside an embedded frame or an unusual theme may need CSS tweaks in `auth_ui.py`.

## Tests

```powershell
python -m unittest tests.test_services -v
python -m unittest tests.test_auth -v
python -m unittest tests.test_auth_ui -v
```
Run the three modules separately (each creates its own temporary database). `test_auth` covers legacy-hash login, registration,
lockout, sessions, reset, Google ID-token claim checks (forged signature, wrong audience/issuer/nonce, expired, unverified email,
`alg=none`), state replay/expiry/browser binding, account linking and GitHub email handling with mocked providers.
`test_auth_ui` drives the server-side flow against a stub Streamlit.

---

# v3.1: frontend and backend wiring fixes

* **Animated sign-in is now the default** front door. The native Streamlit forms remain as a fallback at `?simple=1`
  (the component's "Use simple sign-in" button now uses it; previously it set a parameter the server ignored).
* **Google and GitHub buttons added** to the sign-in and register screens. They send `social_start` to `auth_ui.py`,
  which builds the provider URL via `auth_service.begin_oauth`; the browser only navigates. Buttons look dimmed when the
  provider's credentials are not configured on the server, and clicking explains why.
* `tests/test_auth_ui.py` now checks the `social_start` round trip and that the component sends every action the server handles.
