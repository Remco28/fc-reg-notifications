# Email Notifications: Lightweight Playbook

This doc distills quick guidance for sending low-volume transactional email from side projects, based on our TECHADVISOR chats.

## When Your Needs Are Tiny
- Volume is handful per day, maybe just you. Reliability still matters because transactional mail must reach the inbox even at small scale.
- Prefer plain-text or very simple HTML templates so rendering is predictable.

## Provider vs. Gmail SMTP
- Dedicated transactional services (SendGrid, Mailgun Flex, Postmark, Mailtrap Transactional) handle deliverability, throttling, and bounces for you. Most offer free tiers that cover <100 emails/day.
- "Single sender" modes let you verify an existing address (e.g., `yourname@gmail.com`) when you do not yet have a custom domain.
- Gmail/Outlook personal SMTP can technically send mail with an app password, but providers rate-limit and may flag automation; expect reauth friction and inconsistent delivery.

## Setup Checklist (Single Sender)
1. Sign up for a transactional provider that supports single-sender verification.
2. Verify the email address you plan to send from by clicking their confirmation link.
3. Generate an API key (preferred) or SMTP credentials; store them in `.env` / secret manager, never in git.
4. Call their REST API or SMTP endpoint from the app. Log provider message IDs so you can trace issues.
5. Handle failure responses with retries or an in-app alert so you notice delivery problems.
6. Send a test message and confirm it lands in the inbox (check spam folder too).

## Lightweight App Practices
- Wrap email sending in a helper/service so future template or provider swaps stay localized.
- Keep a plain-text fallback even if you later add HTML styling.
- Add a manual resend command/path for quick testing.
- Separate staging credentials from production ones to avoid polluting your reputation stats.

## Planning Ahead for a Custom Domain
- Reserve the domain early. When ready, set up a subdomain like `notify.example.com` for transactional traffic.
- Publish SPF, DKIM, and DMARC once the provider gives you DNS records. This greatly improves inbox placement.
- Re-verify the new domain inside your provider and rotate API keys if needed.

## Bounce & Complaint Handling
- Even at low volume, keep the provider webhook (or polling endpoint) in mind. Wire it up when you add more recipients so you stop mailing hard-bounced addresses automatically.
- Monitor provider dashboards for error spikes or spam complaints.

## Self-Hosting Reality Check
- Operating Postfix/Exim on a VPS requires DNS tuning, IP reputation warming, TLS upkeep, spam filtering, and abuse monitoring.
- Fresh VPS IPs start with zero reputation; inboxes will often spam-folder or block your messages until you build history.
- For hobby workloads, managed services remain far less work and more reliable. Consider self-hosting only if you need tight control or have the ops budget to maintain it.

## Quick Decision Matrix
- **Need mail today, no domain** → Single-sender mode on SendGrid/Mailgun/Postmark.
- **Have domain, want minimal work** → Same providers but authenticate the domain via SPF/DKIM/DMARC.
- **Care about privacy/control and accept the overhead** → Research self-hosting (Postfix, rspamd, etc.), budget days for setup and ongoing maintenance.

Keep this doc handy when spinning up future projects so you can get emails out the door fast without diving back into deliverability rabbit holes.
