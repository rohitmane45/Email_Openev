"""
Email Dataset — organized by difficulty level.

Easy   : Clear signals, obvious spam, unambiguous categories.
Medium : Mixed signals, subtle cues, requires reading body carefully.
Hard   : Disguised phishing, multi-topic, misleading subjects.
"""

from typing import Any, Dict, List

# ─────────────────────────────────────────────────────────────────────────────
# EASY  — clear, unambiguous emails
# ─────────────────────────────────────────────────────────────────────────────
EASY_EMAILS: List[Dict[str, Any]] = [
    {
        "id": "e001",
        "subject": "URGENT: Invoice #4821 overdue by 30 days",
        "sender": "accounts@vendorco.com",
        "body": (
            "Dear Finance Team,\n\n"
            "Invoice #4821 for $12,500 is now 30 days overdue. "
            "Please arrange immediate payment to avoid service disruption.\n\n"
            "Best regards,\nVendorCo Accounts"
        ),
        "difficulty": "easy",
        "ground_truth": {
            "is_spam": False, "category": "billing", "priority": "urgent",
            "department": "finance", "response_template": "billing_escalation",
        },
    },
    {
        "id": "e002",
        "subject": "You've won $1,000,000! Click here NOW",
        "sender": "noreply@totallylegit-prizes.win",
        "body": (
            "Congratulations!! You have been selected as our lucky winner. "
            "Click the link below to claim your prize immediately. "
            "Act now before your prize expires!!!"
        ),
        "difficulty": "easy",
        "ground_truth": {
            "is_spam": True, "category": "general", "priority": "low",
            "department": "none", "response_template": "spam_discard",
        },
    },
    {
        "id": "e003",
        "subject": "Cannot login to my account - urgent help needed",
        "sender": "jane.smith@customer.com",
        "body": (
            "Hi Support,\n\n"
            "I've been trying to login to my account for the past 2 hours but keep "
            "getting 'invalid credentials'. I have an important presentation in 1 hour "
            "and need access urgently.\n\nThanks, Jane"
        ),
        "difficulty": "easy",
        "ground_truth": {
            "is_spam": False, "category": "support", "priority": "urgent",
            "department": "customer_support", "response_template": "password_reset_guide",
        },
    },
    {
        "id": "e004",
        "subject": "Interested in enterprise pricing for 500 seats",
        "sender": "procurement@bigcorp.com",
        "body": (
            "Hello,\n\nWe are evaluating your platform for our 500-person engineering team. "
            "Could you share enterprise pricing, SLA terms, and arrange a demo?\n\n"
            "Thanks,\nProcurement, BigCorp"
        ),
        "difficulty": "easy",
        "ground_truth": {
            "is_spam": False, "category": "sales", "priority": "urgent",
            "department": "sales", "response_template": "enterprise_demo_request",
        },
    },
    {
        "id": "e005",
        "subject": "Vacation policy clarification",
        "sender": "employee123@company.com",
        "body": (
            "Hi HR,\n\nI wanted to clarify whether my unused vacation days from last year "
            "roll over to this year. The handbook seems a bit unclear on this.\n\nThanks!"
        ),
        "difficulty": "easy",
        "ground_truth": {
            "is_spam": False, "category": "hr", "priority": "normal",
            "department": "human_resources", "response_template": "hr_policy_info",
        },
    },
    {
        "id": "e006",
        "subject": "Free Viagra cheap pills buy now!!!",
        "sender": "pharmacy@spambase.ru",
        "body": "Buy cheap meds no prescription needed. Best prices!! Click here.",
        "difficulty": "easy",
        "ground_truth": {
            "is_spam": True, "category": "general", "priority": "low",
            "department": "none", "response_template": "spam_discard",
        },
    },
    {
        "id": "e007",
        "subject": "RE: Contract renewal -- deadline tomorrow",
        "sender": "legal@partnerorg.com",
        "body": (
            "Hi,\n\nFollowing up on our contract renewal discussion. "
            "The current contract expires tomorrow and we need your signature "
            "on the updated terms by EOD.\n\nRegards, Legal Team"
        ),
        "difficulty": "easy",
        "ground_truth": {
            "is_spam": False, "category": "billing", "priority": "urgent",
            "department": "legal", "response_template": "contract_escalation",
        },
    },
    {
        "id": "e008",
        "subject": "Interview schedule for Software Engineer role",
        "sender": "hr@hiring-company.com",
        "body": (
            "Dear Candidate,\n\nWe'd like to schedule your technical interview for the "
            "Software Engineer role. Please choose a slot from the calendar link below.\n\n"
            "Best, HR Team"
        ),
        "difficulty": "easy",
        "ground_truth": {
            "is_spam": False, "category": "hr", "priority": "normal",
            "department": "human_resources", "response_template": "interview_scheduling",
        },
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# MEDIUM — ambiguous, requires reading carefully
# ─────────────────────────────────────────────────────────────────────────────
MEDIUM_EMAILS: List[Dict[str, Any]] = [
    {
        "id": "m001",
        "subject": "Following up on our conversation",
        "sender": "alex.morgan@clientbiz.net",
        "body": (
            "Hi,\n\nJust following up on our call last week regarding the renewal of our "
            "annual subscription. We're interested in upgrading to the premium tier but "
            "need the updated pricing sheet before we can move forward. "
            "Our current plan expires in 10 days.\n\nBest,\nAlex"
        ),
        "difficulty": "medium",
        "ground_truth": {
            "is_spam": False, "category": "sales", "priority": "urgent",
            "department": "sales", "response_template": "enterprise_demo_request",
        },
    },
    {
        "id": "m002",
        "subject": "Important update regarding your account",
        "sender": "updates@our-platform-notifications.com",
        "body": (
            "Dear Customer,\n\nWe have detected unusual login activity on your account. "
            "For your security, we have temporarily suspended access. "
            "Please verify your identity by clicking the link within 24 hours "
            "or your account will be permanently deleted.\n\nSecurity Team"
        ),
        "difficulty": "medium",
        "ground_truth": {
            "is_spam": True, "category": "general", "priority": "low",
            "department": "none", "response_template": "spam_discard",
        },
    },
    {
        "id": "m003",
        "subject": "Question about last month's statement",
        "sender": "robert.chen@regularuser.com",
        "body": (
            "Hi,\n\nI was reviewing my statement and noticed a charge of $49.99 on March 1st "
            "that I don't recognize. I've been a customer for 3 years and never seen this "
            "before. Could you look into this? I'm not super urgent about it but just "
            "want to make sure it's correct.\n\nThanks,\nRobert"
        ),
        "difficulty": "medium",
        "ground_truth": {
            "is_spam": False, "category": "billing", "priority": "normal",
            "department": "finance", "response_template": "billing_info",
        },
    },
    {
        "id": "m004",
        "subject": "Team offsite planning - input needed",
        "sender": "manager@company-internal.com",
        "body": (
            "Hi all,\n\nWe're planning the Q2 team offsite for the last week of April. "
            "Please fill out the availability survey by Friday so HR can book the venue. "
            "Also, if you have dietary restrictions, please include them in the form. "
            "This is a great chance to bond as a team!\n\nCheers"
        ),
        "difficulty": "medium",
        "ground_truth": {
            "is_spam": False, "category": "hr", "priority": "normal",
            "department": "human_resources", "response_template": "hr_policy_info",
        },
    },
    {
        "id": "m005",
        "subject": "Your monthly digest is ready",
        "sender": "digest@saas-product.io",
        "body": (
            "Hi there,\n\nYour monthly usage report is ready. This month you used 87% "
            "of your storage quota. You are approaching your limit and may experience "
            "disruptions. Consider upgrading your plan to avoid service interruptions. "
            "Click here to view your report and upgrade options."
        ),
        "difficulty": "medium",
        "ground_truth": {
            "is_spam": False, "category": "billing", "priority": "normal",
            "department": "customer_support", "response_template": "billing_info",
        },
    },
    {
        "id": "m006",
        "subject": "Re: Onboarding documents",
        "sender": "new.hire.2026@gmail.com",
        "body": (
            "Hello,\n\nI'm starting on Monday and was told to send my documents to this "
            "address. I've attached my signed offer letter, ID proof, and bank details "
            "for payroll setup. Please let me know if anything else is needed. "
            "Very excited to join the team!\n\nBest regards,\nPriya Sharma"
        ),
        "difficulty": "medium",
        "ground_truth": {
            "is_spam": False, "category": "hr", "priority": "urgent",
            "department": "human_resources", "response_template": "hr_policy_info",
        },
    },
    {
        "id": "m007",
        "subject": "Exclusive offer just for you!",
        "sender": "deals@trustedpartner-offers.com",
        "body": (
            "Hi,\n\nAs a valued customer, we're offering you an exclusive 40% discount "
            "on your next renewal. This offer is valid for the next 48 hours only. "
            "Reply to this email or call our team to avail this offer. "
            "We hope to continue serving you."
        ),
        "difficulty": "medium",
        "ground_truth": {
            "is_spam": True, "category": "general", "priority": "low",
            "department": "none", "response_template": "spam_discard",
        },
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# HARD — disguised phishing, multi-topic, misleading
# ─────────────────────────────────────────────────────────────────────────────
HARD_EMAILS: List[Dict[str, Any]] = [
    {
        "id": "h001",
        "subject": "[IT SECURITY] Mandatory password reset required",
        "sender": "it-security@company-helpdesk.net",
        "body": (
            "Dear Employee,\n\n"
            "Our security team has detected that your password has not been changed "
            "in 90 days. As per company policy, you must reset your password immediately "
            "to maintain system access.\n\n"
            "Click here to reset: http://company-helpdesk.net/reset?user=you\n\n"
            "Failure to comply within 24 hours will result in account suspension.\n\n"
            "IT Security Team"
        ),
        "difficulty": "hard",
        "ground_truth": {
            "is_spam": True, "category": "general", "priority": "low",
            "department": "none", "response_template": "spam_discard",
        },
    },
    {
        "id": "h002",
        "subject": "Quick question + invoice attached",
        "sender": "sarah.k@longtimeclient.co",
        "body": (
            "Hi,\n\nHope you're well! Two things:\n\n"
            "1) I've attached invoice INV-2094 for the March service fee ($3,200). "
            "Payment terms are Net-30 per our contract.\n\n"
            "2) Also, our team is expanding and we might need 15 additional user licenses "
            "next quarter. Can someone from sales reach out to discuss?\n\n"
            "Thanks,\nSarah"
        ),
        "difficulty": "hard",
        "ground_truth": {
            "is_spam": False, "category": "billing", "priority": "normal",
            "department": "finance", "response_template": "billing_info",
        },
    },
    {
        "id": "h003",
        "subject": "Re: Re: Re: Project update",
        "sender": "cto@startup-client.com",
        "body": (
            "Hi,\n\nSorry for the back-and-forth. To summarize where we stand:\n\n"
            "- The integration has been broken for 3 days, affecting our production system\n"
            "- We are losing $5,000/hour in downtime costs\n"
            "- Our legal team is reviewing the SLA breach clause in our contract\n\n"
            "We need escalation to your engineering AND legal team immediately. "
            "Please treat this as your highest priority.\n\nRegards,\nCTO"
        ),
        "difficulty": "hard",
        "ground_truth": {
            "is_spam": False, "category": "support", "priority": "urgent",
            "department": "customer_support", "response_template": "billing_escalation",
        },
    },
    {
        "id": "h004",
        "subject": "Congratulations on your promotion!",
        "sender": "hr-noreply@company-announcements.io",
        "body": (
            "Dear Team Member,\n\nWe are pleased to announce that based on your "
            "outstanding performance, you have been selected for a promotion. "
            "Please review and sign the updated employment contract attached.\n\n"
            "Note: Your new salary and benefits take effect only after the contract "
            "is signed and returned within 48 hours. Contact us with any questions.\n\n"
            "HR Department"
        ),
        "difficulty": "hard",
        "ground_truth": {
            "is_spam": True, "category": "general", "priority": "low",
            "department": "none", "response_template": "spam_discard",
        },
    },
    {
        "id": "h005",
        "subject": "End of quarter — few items to sort",
        "sender": "finance.ops@enterprise-vendor.com",
        "body": (
            "Hi team,\n\nWith Q1 closing tomorrow, a few quick things:\n\n"
            "1. Invoice #7823 ($28,000) — needs approval before 5 PM today\n"
            "2. Our enterprise contract auto-renews on April 1st — please confirm "
            "you want to continue (we'll charge the card on file)\n"
            "3. New pricing tier takes effect April 1st — your rate increases by 15%\n\n"
            "Please respond urgently.\n\nFinance Ops"
        ),
        "difficulty": "hard",
        "ground_truth": {
            "is_spam": False, "category": "billing", "priority": "urgent",
            "department": "finance", "response_template": "billing_escalation",
        },
    },
    {
        "id": "h006",
        "subject": "Your package could not be delivered",
        "sender": "delivery@fast-courier-track.com",
        "body": (
            "Dear Customer,\n\nWe attempted to deliver your package (Tracking: TRK928471) "
            "but were unable to complete delivery due to an incomplete address.\n\n"
            "To reschedule delivery, please pay a small redelivery fee of $2.99 "
            "via the secure link below. Failure to pay within 24 hours will result "
            "in the package being returned to sender.\n\nFast Courier Service"
        ),
        "difficulty": "hard",
        "ground_truth": {
            "is_spam": True, "category": "general", "priority": "low",
            "department": "none", "response_template": "spam_discard",
        },
    },
    {
        "id": "h007",
        "subject": "Performance review + leave request",
        "sender": "employee.88@company.com",
        "body": (
            "Hi,\n\nTwo things:\n\n"
            "First, I got the calendar invite for my annual performance review next week "
            "- confirming I'll be there.\n\n"
            "Second, I need to request 2 weeks emergency leave starting this Friday "
            "due to a family medical situation. I know it's short notice and I'm sorry "
            "for any inconvenience. Happy to discuss handover.\n\nThank you"
        ),
        "difficulty": "hard",
        "ground_truth": {
            "is_spam": False, "category": "hr", "priority": "urgent",
            "department": "human_resources", "response_template": "hr_policy_info",
        },
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Aggregated pools
# ─────────────────────────────────────────────────────────────────────────────
ALL_EMAILS: List[Dict[str, Any]] = EASY_EMAILS + MEDIUM_EMAILS + HARD_EMAILS

DIFFICULTY_POOLS: Dict[str, List[Dict[str, Any]]] = {
    "easy":   EASY_EMAILS,
    "medium": MEDIUM_EMAILS,
    "hard":   HARD_EMAILS,
    "mixed":  ALL_EMAILS,
}
