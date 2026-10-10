# Hackathon submission copy

## Project name
TrustLens

## One-line pitch
Paste a job offer, shop link or business name and get a scam check backed by live Google evidence, not a guess.

## How SerpApi is used
| Engine | Question it answers |
|---|---|
| google_maps | Does this business exist at a real address? Rating, reviews, phone, website |
| google_maps_reviews (lowest rating first) | What do unhappy customers actually complain about? |
| google_jobs | Is the role advertised publicly by the company that claims to be hiring? |
| google_shopping | Is the price near the market median? Is the seller one Google lists? |
| google | Do other pages tie the name to scams or fraud? Adaptive follow-up on forums |
| google_news | Any reputable coverage, positive or negative? |

## AI tools used
Claude (Anthropic) helped write the code and documentation. The app can optionally call Claude at runtime
to phrase the plain-language summary; the score and verdict are computed by deterministic rules.
