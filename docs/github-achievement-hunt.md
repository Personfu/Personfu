# PersonFu GitHub Achievement Hunt Plan

This plan treats GitHub achievements as a side effect of useful work, not as a reason to spam repositories.

## Rules

- No empty commits.
- No artificial issue churn.
- No fake coauthors.
- No low-quality PRs to unrelated projects.
- No badge farming that damages repo trust.
- Every change should improve docs, tests, automation, visuals, examples, or safe tools.

## Achievement map

| Achievement | Legitimate path | PersonFu action |
|---|---|---|
| Pull Shark | Open PRs that get merged | Use feature branches for meaningful repo updates; merge after checks pass |
| Quickdraw | Close an issue/PR quickly | Only use when a real typo/bug issue is opened and fixed immediately |
| Pair Extraordinaire | Coauthored commits in merged PRs | Pair on real work with collaborators and use accurate `Co-authored-by` trailers |
| YOLO | Merge PR without review | Only for low-risk self-owned docs/manifest PRs if branch rules allow it |
| Starstruck | Repository receives stars | Improve flagship repos, docs, demos, screenshots, and discoverability |
| Galaxy Brain | Accepted discussion answers | Answer real questions in GitHub Discussions with useful, source-backed help |
| Public Sponsor | Sponsor an open-source maintainer | Do through GitHub Sponsors when budget allows |
| Developer Program Member | Join GitHub Developer Program | Register the account and document app/API experiments |
| Security advisory credit | Accepted advisory | Report real vulnerabilities through coordinated disclosure |

## Tonight-safe commit strategy

1. Add additive docs/scripts/manifests across neglected repos.
2. Avoid runtime changes unless the build is verified.
3. Keep commits small enough to review but not noisy.
4. Prefer repo-specific artifacts over generic boilerplate.
5. Check deployment status on Vercel/GitHub Actions after touching active web apps.

## Future PR strategy

For achievements that require PR merges, use normal branches:

```text
feature/personfu-content-map-<repo>
feature/safe-tooling-<repo>
feature/visual-roadmap-<repo>
```

Each PR should include:

- one purpose;
- short test/verification note;
- screenshots if visual;
- no secrets;
- no unsafe attack workflows;
- clear FLLC content-tier mapping when relevant.

## Public credibility priorities

- Pin the best repos.
- Add screenshots and demo links.
- Keep READMEs accurate.
- Use GitHub Pages for safe visual demos.
- Add SECURITY.md, CONTRIBUTING.md, issue templates, and CodeQL where appropriate.
- Write useful discussions and answers instead of shallow engagement farming.
