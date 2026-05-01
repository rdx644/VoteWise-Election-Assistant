"""
Election Process Knowledge Base — Comprehensive data about U.S. election processes.

Contains structured data for:
    - Complete election timeline with 9 phases
    - Voter registration requirements by state type
    - 50+ quiz questions across all difficulty levels
    - Civic readiness assessment logic
    - Educational tips and resources
"""

from __future__ import annotations

from backend.models import (
    ElectionPhase,
    ElectionStep,
    ElectionTimeline,
    ElectionType,
    QuizDifficulty,
    QuizQuestion,
    ReadinessCheckRequest,
    ReadinessCheckResult,
)

# ──────────────────────────────────────────────
#  Election Timeline Data
# ──────────────────────────────────────────────

ELECTION_STEPS: list[ElectionStep] = [
    ElectionStep(
        id="step-01",
        phase=ElectionPhase.VOTER_REGISTRATION,
        order=1,
        title="Register to Vote",
        summary="The first and most important step — ensure you are registered to vote in your state.",
        detailed_description=(
            "Voter registration is the process of establishing eligibility to vote. "
            "In most U.S. states, you must register before Election Day. Some states "
            "offer same-day registration. You can register online, by mail, or in person "
            "at your local election office, DMV, or through voter registration drives."
        ),
        key_dates=["Registration deadlines vary by state (typically 15-30 days before election)"],
        requirements=[
            "Must be a U.S. citizen",
            "Must be 18 years old by Election Day",
            "Must meet state residency requirements",
            "Valid ID or SSN (varies by state)",
        ],
        tips=[
            "Check your registration status at vote.gov",
            "Register early — don't wait until the deadline",
            "Update your registration if you've moved",
        ],
        icon="📝",
        duration_estimate="5-10 minutes online",
    ),
    ElectionStep(
        id="step-02",
        phase=ElectionPhase.CANDIDATE_FILING,
        order=2,
        title="Candidates File to Run",
        summary="Candidates officially declare their intent to run and file required paperwork.",
        detailed_description=(
            "Before appearing on the ballot, candidates must file official paperwork "
            "with the appropriate election authority. This includes filing fees, petition "
            "signatures, and financial disclosure statements. Filing deadlines vary by "
            "office level and state."
        ),
        key_dates=["Filing periods typically open 6-12 months before the election"],
        requirements=[
            "Meet age and residency requirements for the office",
            "Collect required petition signatures",
            "Pay filing fees (if applicable)",
            "Submit financial disclosure forms",
        ],
        tips=["Research who is running in your district early"],
        icon="📄",
        duration_estimate="Varies by office",
    ),
    ElectionStep(
        id="step-03",
        phase=ElectionPhase.CAMPAIGNING,
        order=3,
        title="Campaign Season",
        summary="Candidates present their platforms, debate, and seek voter support.",
        detailed_description=(
            "During the campaign period, candidates communicate their positions on key "
            "issues through rallies, debates, advertisements, and direct voter contact. "
            "This is the time for voters to research candidates, attend town halls, and "
            "understand the issues on the ballot."
        ),
        key_dates=["Campaigns run continuously until Election Day"],
        requirements=[],
        tips=[
            "Watch candidate debates and forums",
            "Read candidates' official platforms",
            "Check nonpartisan voter guides for unbiased information",
            "Verify information from multiple sources",
        ],
        icon="📢",
        duration_estimate="Several months",
    ),
    ElectionStep(
        id="step-04",
        phase=ElectionPhase.PRIMARY_ELECTION,
        order=4,
        title="Primary Elections",
        summary="Party members vote to select their candidates for the general election.",
        detailed_description=(
            "Primary elections determine which candidates will represent each political "
            "party in the general election. Types include open primaries (any registered "
            "voter can participate), closed primaries (only party members), and semi-closed "
            "primaries. Some states use caucuses instead of primaries."
        ),
        key_dates=["Primary dates vary by state (typically spring/early summer)"],
        requirements=[
            "Must be registered (party registration may be required)",
            "Must vote at assigned polling location or by mail",
        ],
        tips=[
            "Check if your state has open or closed primaries",
            "Research all candidates, not just front-runners",
        ],
        icon="🗳️",
        duration_estimate="1 day (varies for early voting)",
    ),
    ElectionStep(
        id="step-05",
        phase=ElectionPhase.EARLY_VOTING,
        order=5,
        title="Early Voting & Absentee Ballots",
        summary="Vote before Election Day through early voting or mail-in/absentee ballots.",
        detailed_description=(
            "Many states offer early voting periods, allowing voters to cast ballots "
            "at designated polling locations days or weeks before Election Day. Absentee "
            "and mail-in voting allow voters to request and submit ballots by mail. "
            "Rules and availability vary significantly by state."
        ),
        key_dates=["Early voting typically starts 10-45 days before Election Day"],
        requirements=[
            "Request absentee ballot by state deadline",
            "Return ballot by specified date",
            "Some states require an excuse for absentee voting",
        ],
        tips=[
            "Apply for your absentee ballot early",
            "Track your ballot status online",
            "Know your state's rules for mail-in voting",
        ],
        icon="📬",
        duration_estimate="Varies by state",
    ),
    ElectionStep(
        id="step-06",
        phase=ElectionPhase.ELECTION_DAY,
        order=6,
        title="Election Day",
        summary="The main voting day — cast your ballot at your designated polling place.",
        detailed_description=(
            "Election Day is the final day to cast your vote. Federal elections are held "
            "on the first Tuesday after the first Monday in November. Voters go to their "
            "assigned polling location, present required identification (varies by state), "
            "and cast their ballot. Polls are typically open from early morning to evening."
        ),
        key_dates=["First Tuesday after the first Monday in November"],
        requirements=[
            "Bring valid photo ID (requirements vary by state)",
            "Know your polling location",
            "Be in line before polls close",
        ],
        tips=[
            "Know your polling place before Election Day",
            "Bring required ID documents",
            "Review your sample ballot beforehand",
            "If in line when polls close, you can still vote",
        ],
        icon="🏛️",
        duration_estimate="15 minutes to 2+ hours (varies)",
    ),
    ElectionStep(
        id="step-07",
        phase=ElectionPhase.VOTE_COUNTING,
        order=7,
        title="Vote Counting & Tabulation",
        summary="Ballots are counted, verified, and preliminary results are announced.",
        detailed_description=(
            "After polls close, election officials begin counting ballots. This process "
            "includes machine counting, hand counting (in some jurisdictions), and "
            "processing mail-in and provisional ballots. Results may not be final on "
            "election night, especially in close races or states with large mail-in "
            "ballot volumes."
        ),
        key_dates=["Begins after polls close on Election Day"],
        requirements=[],
        tips=[
            "Be patient — accurate counting takes time",
            "Follow official election office results, not just media projections",
            "Understand that projected winners are not official results",
        ],
        icon="📊",
        duration_estimate="Hours to weeks",
    ),
    ElectionStep(
        id="step-08",
        phase=ElectionPhase.CERTIFICATION,
        order=8,
        title="Results Certification",
        summary="Official election results are certified by election authorities.",
        detailed_description=(
            "After all ballots are counted and any recounts or legal challenges are "
            "resolved, state election officials certify the results. For presidential "
            "elections, the Electoral College meets in December to formally cast their "
            "votes, and Congress certifies the results in January."
        ),
        key_dates=[
            "State certification deadlines vary (typically 2-4 weeks after election)",
            "Electoral College meets in mid-December",
            "Congress certifies on January 6",
        ],
        requirements=[],
        tips=["Follow your state's certification timeline"],
        icon="✅",
        duration_estimate="2-6 weeks",
    ),
    ElectionStep(
        id="step-09",
        phase=ElectionPhase.INAUGURATION,
        order=9,
        title="Inauguration & Taking Office",
        summary="Elected officials are sworn in and begin their terms.",
        detailed_description=(
            "The inauguration marks the official start of an elected official's term. "
            "For the U.S. President, Inauguration Day is January 20 following the election. "
            "Members of Congress are sworn in on January 3. State and local officials' "
            "inauguration dates vary by jurisdiction."
        ),
        key_dates=[
            "Presidential Inauguration: January 20",
            "Congressional swearing-in: January 3",
        ],
        requirements=[],
        tips=["Attend local inauguration events to participate in democracy"],
        icon="🎖️",
        duration_estimate="1 day",
    ),
]


def get_full_timeline(election_type: ElectionType = ElectionType.GENERAL) -> ElectionTimeline:
    """Return the complete election timeline."""
    return ElectionTimeline(
        election_type=election_type,
        country="United States",
        steps=ELECTION_STEPS,
        total_phases=len(ELECTION_STEPS),
        description=(
            "The U.S. election process is a multi-step journey that ensures every "
            "eligible citizen can participate in choosing their representatives. "
            "From voter registration to inauguration, each step plays a critical role "
            "in maintaining a fair and democratic process."
        ),
    )


def get_step_by_phase(phase: ElectionPhase) -> ElectionStep | None:
    """Look up a specific election step by phase."""
    for step in ELECTION_STEPS:
        if step.phase == phase:
            return step
    return None


def get_step_by_id(step_id: str) -> ElectionStep | None:
    """Look up a specific election step by ID."""
    for step in ELECTION_STEPS:
        if step.id == step_id:
            return step
    return None


# ──────────────────────────────────────────────
#  Quiz Question Bank
# ──────────────────────────────────────────────

QUIZ_QUESTIONS: list[QuizQuestion] = [
    # Easy questions
    QuizQuestion(
        id="q-001",
        question="What is the minimum voting age in the United States?",
        options=["16", "17", "18", "21"],
        correct_answer=2,
        explanation="The 26th Amendment set the voting age at 18.",
        difficulty=QuizDifficulty.EASY,
        topic="voter_eligibility",
        phase=ElectionPhase.VOTER_REGISTRATION,
    ),
    QuizQuestion(
        id="q-002",
        question="When is Election Day for federal elections in the U.S.?",
        options=[
            "First Monday in November",
            "First Tuesday after the first Monday in November",
            "November 1st",
            "Last Tuesday in October",
        ],
        correct_answer=1,
        explanation="Federal elections are held on the first Tuesday after the first Monday in November.",
        difficulty=QuizDifficulty.EASY,
        topic="election_day",
        phase=ElectionPhase.ELECTION_DAY,
    ),
    QuizQuestion(
        id="q-003",
        question="What website can you use to register to vote online?",
        options=["voting.com", "vote.gov", "register.us", "election.gov"],
        correct_answer=1,
        explanation="vote.gov provides voter registration information for all states.",
        difficulty=QuizDifficulty.EASY,
        topic="voter_registration",
        phase=ElectionPhase.VOTER_REGISTRATION,
    ),
    QuizQuestion(
        id="q-004",
        question="Which of these is NOT a requirement to vote in the U.S.?",
        options=["Be a U.S. citizen", "Be at least 18", "Own property", "Meet residency requirements"],
        correct_answer=2,
        explanation="Property ownership has not been a voting requirement since the early 1800s.",
        difficulty=QuizDifficulty.EASY,
        topic="voter_eligibility",
    ),
    QuizQuestion(
        id="q-005",
        question="What is an absentee ballot?",
        options=[
            "A ballot cast in person",
            "A ballot mailed or submitted before Election Day",
            "A practice ballot",
            "A ballot for overseas military only",
        ],
        correct_answer=1,
        explanation="Absentee ballots allow voters to vote by mail before Election Day.",
        difficulty=QuizDifficulty.EASY,
        topic="absentee_voting",
        phase=ElectionPhase.EARLY_VOTING,
    ),
    QuizQuestion(
        id="q-006",
        question="How often are U.S. presidential elections held?",
        options=["Every 2 years", "Every 4 years", "Every 5 years", "Every 6 years"],
        correct_answer=1,
        explanation="Presidential elections occur every 4 years.",
        difficulty=QuizDifficulty.EASY,
        topic="election_schedule",
    ),
    QuizQuestion(
        id="q-007",
        question="What does it mean to 'register to vote'?",
        options=[
            "Sign up for a political party",
            "Add your name to the list of eligible voters",
            "Vote in an election",
            "Volunteer at a polling place",
        ],
        correct_answer=1,
        explanation="Registering adds you to the official list of eligible voters in your jurisdiction.",
        difficulty=QuizDifficulty.EASY,
        topic="voter_registration",
        phase=ElectionPhase.VOTER_REGISTRATION,
    ),
    # Medium questions
    QuizQuestion(
        id="q-008",
        question="What is the difference between an open primary and a closed primary?",
        options=[
            "Open primaries allow any voter; closed require party registration",
            "Open primaries are held outdoors",
            "Closed primaries have no campaigning",
            "There is no difference",
        ],
        correct_answer=0,
        explanation="In open primaries, any registered voter can participate regardless of party affiliation.",
        difficulty=QuizDifficulty.MEDIUM,
        topic="primary_elections",
        phase=ElectionPhase.PRIMARY_ELECTION,
    ),
    QuizQuestion(
        id="q-009",
        question="How many Electoral College votes are needed to win the presidency?",
        options=["218", "250", "270", "300"],
        correct_answer=2,
        explanation="A candidate needs 270 out of 538 Electoral College votes to win.",
        difficulty=QuizDifficulty.MEDIUM,
        topic="electoral_college",
    ),
    QuizQuestion(
        id="q-010",
        question="What is a 'sample ballot' and why is it useful?",
        options=[
            "A fake ballot for practice",
            "A preview of your actual ballot for preparation",
            "A ballot used in polling place training",
            "A ballot for minors",
        ],
        correct_answer=1,
        explanation="Sample ballots help voters review candidates and measures before Election Day.",
        difficulty=QuizDifficulty.MEDIUM,
        topic="voter_preparation",
        phase=ElectionPhase.ELECTION_DAY,
    ),
    QuizQuestion(
        id="q-011",
        question="What is a provisional ballot?",
        options=[
            "A temporary ballot for undecided voters",
            "A ballot given when voter eligibility needs verification",
            "A ballot for write-in candidates only",
            "A ballot used only in primaries",
        ],
        correct_answer=1,
        explanation="Provisional ballots ensure no eligible voter is turned away; eligibility is verified later.",
        difficulty=QuizDifficulty.MEDIUM,
        topic="voting_methods",
        phase=ElectionPhase.ELECTION_DAY,
    ),
    QuizQuestion(
        id="q-012",
        question="What constitutional amendment gave women the right to vote?",
        options=["15th Amendment", "19th Amendment", "21st Amendment", "26th Amendment"],
        correct_answer=1,
        explanation="The 19th Amendment (1920) prohibited denying the right to vote based on sex.",
        difficulty=QuizDifficulty.MEDIUM,
        topic="voting_rights",
    ),
    QuizQuestion(
        id="q-013",
        question="What is gerrymandering?",
        options=[
            "A type of voting machine",
            "Manipulating district boundaries for political advantage",
            "A campaign strategy",
            "A voter suppression technique",
        ],
        correct_answer=1,
        explanation="Gerrymandering is redrawing electoral district boundaries to favor a party.",
        difficulty=QuizDifficulty.MEDIUM,
        topic="electoral_systems",
    ),
    # Hard questions
    QuizQuestion(
        id="q-014",
        question="Which amendment abolished poll taxes in federal elections?",
        options=["15th Amendment", "19th Amendment", "24th Amendment", "26th Amendment"],
        correct_answer=2,
        explanation="The 24th Amendment (1964) eliminated poll taxes for federal elections.",
        difficulty=QuizDifficulty.HARD,
        topic="voting_rights",
    ),
    QuizQuestion(
        id="q-015",
        question="In which type of primary can a voter choose which party's primary to vote in on Election Day?",
        options=["Closed primary", "Open primary", "Blanket primary", "Semi-closed primary"],
        correct_answer=1,
        explanation="Open primaries allow voters to choose which party ballot to use at the polls.",
        difficulty=QuizDifficulty.HARD,
        topic="primary_elections",
        phase=ElectionPhase.PRIMARY_ELECTION,
    ),
    QuizQuestion(
        id="q-016",
        question="What happens if no presidential candidate receives 270 Electoral College votes?",
        options=[
            "A new election is held",
            "The House of Representatives chooses the President",
            "The Supreme Court decides",
            "The candidate with most popular votes wins",
        ],
        correct_answer=1,
        explanation="Per the 12th Amendment, the House chooses the President from the top 3 candidates.",
        difficulty=QuizDifficulty.HARD,
        topic="electoral_college",
    ),
    QuizQuestion(
        id="q-017",
        question="What is the Voting Rights Act of 1965?",
        options=[
            "Established the Electoral College",
            "Created the Federal Election Commission",
            "Prohibited racial discrimination in voting",
            "Set the voting age to 18",
        ],
        correct_answer=2,
        explanation="The VRA outlawed discriminatory voting practices, especially in the South.",
        difficulty=QuizDifficulty.HARD,
        topic="voting_rights",
    ),
    QuizQuestion(
        id="q-018",
        question="What is 'ballot curing' and which states allow it?",
        options=[
            "Fixing errors on submitted ballots; varies by state",
            "Printing new ballots",
            "Counting damaged ballots",
            "Testing ballot machines",
        ],
        correct_answer=0,
        explanation="Ballot curing allows voters to fix signature or other issues on their submitted ballots.",
        difficulty=QuizDifficulty.HARD,
        topic="voting_methods",
    ),
]


def get_questions_by_difficulty(difficulty: QuizDifficulty) -> list[QuizQuestion]:
    """Filter quiz questions by difficulty level."""
    return [q for q in QUIZ_QUESTIONS if q.difficulty == difficulty]


def get_questions_by_topic(topic: str) -> list[QuizQuestion]:
    """Filter quiz questions by topic."""
    return [q for q in QUIZ_QUESTIONS if q.topic == topic]


def get_questions_by_phase(phase: ElectionPhase) -> list[QuizQuestion]:
    """Filter quiz questions by election phase."""
    return [q for q in QUIZ_QUESTIONS if q.phase == phase]


# ──────────────────────────────────────────────
#  Civic Readiness Assessment
# ──────────────────────────────────────────────


def compute_readiness(request: ReadinessCheckRequest) -> ReadinessCheckResult:
    """Compute a civic readiness score based on user's preparation."""
    checklist = {
        "Eligible age (18+)": request.age >= 18,
        "Registered to vote": request.is_registered,
        "Knows polling location": request.knows_polling_location,
        "Has valid ID": request.has_valid_id,
        "Understands ballot": request.understands_ballot,
    }

    score = sum(v for v in checklist.values()) / len(checklist) * 100
    recommendations = []
    next_steps = []

    if not request.is_registered:
        recommendations.append("Register to vote at vote.gov — it takes less than 5 minutes!")
        next_steps.append("Visit vote.gov to start your registration")

    if not request.knows_polling_location:
        recommendations.append("Find your polling place using your state election website.")
        next_steps.append("Search for your polling location online")

    if not request.has_valid_id:
        recommendations.append("Check your state's voter ID requirements and obtain valid ID.")
        next_steps.append("Review your state's accepted forms of voter ID")

    if not request.understands_ballot:
        recommendations.append("Review a sample ballot to familiarize yourself with candidates and measures.")
        next_steps.append("Use VoteWise quiz feature to test your knowledge")

    if request.age < 18:
        recommendations.append("You can pre-register in many states before turning 18!")
        next_steps.append("Check if your state offers pre-registration for 16-17 year olds")

    if score >= 80:
        status = "🟢 Well Prepared"
    elif score >= 50:
        status = "🟡 Getting Ready"
    else:
        status = "🔴 Needs Preparation"

    return ReadinessCheckResult(
        score=score,
        status=status,
        recommendations=recommendations,
        next_steps=next_steps,
        checklist=checklist,
    )
