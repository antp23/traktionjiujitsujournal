# BJJ Tracker Team Product Design

## Product Thesis

BJJ Tracker is a private Brazilian Jiu-Jitsu training journal that turns detailed training logs into direct coaching-style advice, goals, and progress tracking.

For teams, athletes can join a gym workspace and selectively share goals, questions, notes, and coach-brief items with coaches. The product is not a gym management system, curriculum platform, or class-planning tool.

The core loop is:

1. Capture detailed training context.
2. Detect recurring patterns.
3. Give direct advice.
4. Convert advice into goals.
5. Track whether training behavior changes.

## Product Personality

The advice voice should feel like a direct coach:

- Blunt, practical, and specific.
- Willing to call out repeated mistakes.
- Evidence-aware, without sounding timid.
- Clear when a recommendation is based on sparse data.

Example:

> You keep getting caught by collar chokes. Stop adding new attacks until your posture and frames are cleaner from top half.

The app should avoid vague wellness-dashboard language. The home experience should answer: what is going wrong, what is improving, and what should I do next?

## Primary Surfaces

### Coach's Brief

The main home screen. It should synthesize the athlete's journal, goals, rolls, techniques, coach notes, and optional recovery data into a short, direct training brief.

Core sections:

- Today’s Call: one clear recommendation.
- Problem Pattern: the most important recurring issue.
- Training Assignment: a concrete focus for the next class or week.
- Technique Queue: review now, keep drilling, test live.
- Readiness Check: Oura-aware guidance when recovery is connected.
- Take This Personally: resurfaced coach notes or durable advice when relevant.

Each recommendation should show a confidence level and why it exists:

- High confidence: repeated logs or coach notes support the advice.
- Medium confidence: some pattern is present but needs more logging.
- Low confidence: useful guess, clearly labeled.

### Progress Console

The deeper analytics workspace. It should focus on useful training signals, not vanity metrics.

Core areas:

- Training volume and consistency.
- Gi/no-gi split.
- Position and submission trends.
- Recurring problems.
- Technique proficiency movement.
- Goal progress.
- Optional recovery correlation.

Win rate should not be the main roll metric. More useful roll signals include positions lost, submissions conceded, successful escapes, recurring threats, and whether the athlete attempted their current goals live.

### Journal

The private memory layer. This includes sessions, rolls, notes, techniques, recovery, and WhatsApp captures.

The journal should encourage richer logs by nudging for:

- What position failed?
- What did coach correct?
- What did you try live?
- What repeated?
- What should be tested next?

WhatsApp is the primary quick-capture channel. Portal journaling remains available but is not the main capture assumption.

### Goals

Goals are the accountability layer. Advice can become a goal.

Examples:

- Drill collar-choke defense for three sessions.
- Start five rounds from bottom half.
- Hit one De La Riva off-balance before sweeping.
- Log all submission losses for two weeks.

Goals may be short-term assignments or longer development arcs. The home screen should focus on the next concrete action so goals do not become abstract.

### Coach Notes

Coach Notes are durable advice objects, separate from ordinary journal notes.

They can come from:

- A human coach.
- Athlete self-reflection.
- AI pattern analysis.
- A pinned coach reply.

Fields:

- Source: coach, athlete, AI pattern.
- Category: mindset, cardio, technique detail, game plan, recovery.
- Status: active, internalized, archived.
- Linked goal, technique, position/problem, session, and date.

Coach Notes should resurface in Coach's Brief until internalized or archived.

## Team V1 Scope

The team version exists to support private athlete accounts under a gym workspace plus opt-in sharing with coaches.

### In Scope

- Gym workspace.
- Owner/admin role.
- Optional coach role.
- Athlete self-enrollment by invite link.
- Magic-link authentication.
- Athlete profile onboarding.
- WhatsApp identity capture during onboarding.
- Private journal by default.
- Share selected goals, notes, and brief items with coach.
- Coach reply threads.
- Pin important replies into Coach Notes.
- Basic member management.

### Out Of Scope

- Coach assignment system.
- Team curriculum.
- Class planning.
- Public team feeds.
- Automatic coach visibility into all athlete logs.
- Gym billing, attendance management, or CRM features.

## Roles

### Owner/Admin

The owner/admin manages the gym workspace.

Capabilities:

- Create and manage invite links.
- Approve or remove members.
- Assign roles: athlete, coach, owner/admin.
- View membership status.
- Configure gym name and basic workspace settings.

The system should support one owner/admin for V1 while allowing additional coaches later.

### Coach

The coach sees only athlete-shared items.

Capabilities:

- View shared inbox.
- Reply to shared items.
- Pin important replies as Coach Notes.
- View Coach Notes that the coach authored or that were shared with them.

Coaches do not see private journals, private rolls, private recovery data, or private goals unless explicitly shared.

### Athlete

The athlete owns their training data.

Capabilities:

- Join a gym workspace by invite.
- Complete training profile.
- Capture logs in the portal or by WhatsApp.
- View Coach's Brief, Progress Console, Journal, Goals, and Coach Notes.
- Share selected goals, notes, and brief items with coach.
- Mark coach notes internalized or archived.

## Privacy Model

Default privacy is athlete-only.

Private by default:

- Journal entries.
- Sessions.
- Rolls.
- Raw WhatsApp captures.
- Recovery/Oura data.
- Private goals.
- Private self-notes.

Shared only by explicit action:

- Selected goals.
- Selected notes or questions.
- Selected Coach's Brief recommendations.
- Selected progress snapshots.

Visible to athlete and relevant coach:

- Coach replies in shared threads.
- Pinned Coach Notes created from shared threads.

Team-wide visibility is not included in V1, except for basic workspace membership and admin controls.

## Enrollment Flow

1. Athlete opens a gym invite link.
2. Athlete enters email.
3. System sends a magic link.
4. Athlete opens magic link and creates profile.
5. Athlete completes student details.
6. Athlete optionally sets up WhatsApp capture.
7. Athlete lands in private dashboard.

### Student Profile Fields

Identity:

- Full name.
- Preferred name.
- Email.
- WhatsApp phone.
- Optional profile photo.

BJJ profile:

- Belt.
- Stripes.
- Start date or years training.
- Primary gym/team.
- Typical training frequency.
- Gi/no-gi preference.
- Competition interest.

Training context:

- Current focus.
- A-game or favorite positions.
- Problem positions.
- Injuries or limitations.
- Current goals.

Sharing defaults:

- Journal private.
- Recovery private.
- Shared-with-coach items visible to coach.
- WhatsApp captures private unless shared later.

### WhatsApp Setup

WhatsApp setup is optional but encouraged.

Enrollment should explain:

- WhatsApp messages become private journal drafts/logs.
- The athlete chooses what, if anything, to share with coach.
- Better detail produces better advice.

Example guidance:

- Weak: "trained today"
- Better: "trained gi 90 min, worked DLR. Got collar choked twice from top half. Coach said posture was too low."
- Best: "trained gi 90 min. Focus: DLR triangle setup. Live rounds: got passed when opponent stapled far leg. Goal: retain guard before chasing sweep."

## Sharing With Coach

Athlete can share:

- A goal.
- A note or question.
- A Coach's Brief recommendation.
- A progress snapshot.

Flow:

1. Athlete clicks "Ask coach" or "Share with coach."
2. Athlete adds optional context or question.
3. System creates a ShareThread.
4. Coach sees the item in Shared Inbox.
5. Coach replies conversationally.
6. Coach or athlete can pin an important reply.
7. Pinned reply becomes a Coach Note.

The thread remains useful for conversation. The pinned Coach Note becomes durable training memory.

## Navigation

### Athlete Navigation

- Coach's Brief.
- Progress.
- Journal.
- Goals.
- Coach Notes.
- Settings.

### Coach Navigation

- Shared Inbox.
- Athletes.
- Coach Notes.
- Settings.

Coach navigation should stay minimal. Do not introduce curriculum, class planning, or assignments in V1.

## Data Model

### User

Represents an authenticated person.

Fields:

- id.
- email.
- name.
- preferred_name.
- created_at.
- last_login_at.

### GymWorkspace

Represents a gym or team.

Fields:

- id.
- name.
- slug.
- owner_user_id.
- created_at.

### Membership

Connects users to gym workspaces.

Fields:

- id.
- user_id.
- gym_workspace_id.
- role: owner, coach, athlete.
- status: invited, active, removed.
- created_at.

### InviteLink

Supports self-enrollment.

Fields:

- id.
- gym_workspace_id.
- code.
- expires_at.
- max_uses.
- uses_count.
- created_by_user_id.
- created_at.

### AthleteProfile

Stores BJJ-specific profile data.

Fields:

- user_id.
- belt.
- stripes.
- started_training_on.
- years_training.
- typical_training_frequency.
- gi_nogi_preference.
- competition_interest.
- current_focus.
- favorite_positions.
- problem_positions.
- injuries_or_limitations.

### WhatsAppIdentity

Links WhatsApp capture to a user.

Fields:

- id.
- user_id.
- phone_number.
- verification_status.
- verified_at.
- created_at.

### Goal

Tracks athlete goals.

Fields:

- id.
- user_id.
- title.
- description.
- status: active, completed, paused, archived.
- visibility: private, shared_with_coach.
- target_date.
- created_at.
- updated_at.

### ShareThread

Represents an athlete-shared item and coach conversation.

Fields:

- id.
- owner_user_id.
- gym_workspace_id.
- shared_with_user_id or shared_with_role.
- source_type: goal, note, brief_item, progress_snapshot.
- source_id.
- status: open, resolved, archived.
- created_at.
- updated_at.

### ThreadMessage

Stores replies in a shared thread.

Fields:

- id.
- share_thread_id.
- author_user_id.
- body.
- pinned_as_coach_note_id.
- created_at.

### CoachNote

Stores durable advice.

Fields:

- id.
- athlete_user_id.
- author_user_id.
- source: coach, athlete, ai_pattern.
- category: mindset, cardio, technique_detail, game_plan, recovery.
- title.
- body.
- status: active, internalized, archived.
- linked_goal_id.
- linked_session_id.
- linked_technique_id.
- linked_position.
- created_at.
- updated_at.

## Implementation Phases

### Phase 1: Auth, Workspace, Enrollment

Goal: make the app multi-user and safe for semi-internal team use.

Build:

- Magic-link auth.
- User table.
- Gym workspace table.
- Membership roles.
- Invite links.
- Athlete profile onboarding.
- WhatsApp phone field.
- Private-by-default data ownership.

Migration note:

- Existing single-user data should be assigned to an initial owner/admin athlete account.

### Phase 2: Athlete Product Surfaces

Goal: adapt the current app around the new product model.

Build:

- Coach's Brief as home.
- Progress Console refinements.
- Goals surface.
- Coach Notes surface.
- Journal ownership and visibility labels.
- Better empty states for new athletes.

### Phase 3: Sharing With Coach

Goal: add selective collaboration without exposing private journals.

Build:

- Share button for goals, notes, and brief items.
- Shared Inbox for coach.
- ShareThread and ThreadMessage.
- Pin message as Coach Note.
- Coach Note resurfacing in athlete brief.

### Phase 4: Advice Quality

Goal: make advice more useful as logs get richer.

Build:

- Pattern detection for repeated submissions, positions, and coach corrections.
- Confidence labels.
- "Why this advice" evidence display.
- Goal suggestions from advice.
- WhatsApp prompt examples and richer capture nudges.

## Success Criteria

V1 is successful if:

- A teammate can join by invite without admin hand-holding.
- New athletes understand their journal is private by default.
- WhatsApp capture is optional but clearly encouraged.
- Athlete can share one goal or note with coach.
- Coach can reply.
- Important coach replies can become Coach Notes.
- Coach's Brief feels direct and useful, even if early recommendations are low-confidence.
- The product does not drift into class planning, curriculum management, or gym CRM.

## Open Implementation Decisions

- Exact magic-link provider: custom email token, Supabase Auth, Auth.js, or another service.
- Whether WhatsApp ingestion remains OpenClaw-based or moves behind a first-party endpoint.
- Whether Oura integration should remain local-only for team V1 or be deferred until user auth is complete.
- How to migrate existing data into an initial user-owned account.
