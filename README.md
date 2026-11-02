# SEO Autopilot

One private GitHub repo that connects all your WordPress sites (Elementor, Divi or plain Gutenberg). For each site it researches keywords and competitors, writes one original, humanized blog **every 2 days**, makes it pass Rank Math's checks, formats it for that site's page builder and schedules it. Everything shows on one dashboard.

It runs free on **GitHub Actions**, so you don't need a server. **Read [SAFETY.md](SAFETY.md) before switching sites on.**

---

## What happens every day (6:47 am IST)

1. **Mondays:** a full **audit** of every site (broken links, missing meta, thin content, orphans, etc.), plus a **competitor sitemap scan** to find topics competitors cover that you don't.
2. **Mondays and Thursdays:** **keyword research** from Google Search Console (your real queries and striking-distance keywords) and Google Autocomplete.
3. **Which sites are due:** each site gets **1 blog every 2 days**, which is 5 per 10-day cycle, repeating. Sites are staggered, so with 20 sites about 10 write each day.
4. **For each due site, one blog:**

| Step | Tool (all free except the Claude API) |
|---|---|
| Pick a fresh topic (no "benefits/uses" formula, not covered on the site, not used by a sister site) | Search Console, Autocomplete, competitor gaps, Claude |
| See what ranks on Google now: People Also Ask, gaps, facts with sources | Claude web search |
| **Competitor analysis** of the ranking pages and your competitors' posts: word count, headings, FAQ/table/image use, terms most of them cover | Built-in, free (respects robots.txt) |
| Write the article (Rank Math rules built into the brief) | Claude |
| **Humanize:** a human-editor rewrite, then an AI-phrase scrubber, then readability scoring (Flesch, sentence variety, passive voice) | Claude + built-in free checks |
| Remove unsafe links (your other sites, untrusted domains) | Built-in |
| Free licensed **photo** uploaded to WordPress with keyword alt text, used as the featured image and in the body | Pexels API (free) or Openverse CC0 |
| **Rank Math check:** all 21 tests, with automatic fixes (slug, TOC, paragraph length, sources, title) and a targeted rewrite if needed | Built-in |
| **Duplicate check** against every page on all your sites | Built-in |
| **Safety gate:** schedule if everything passes, otherwise save as a **draft** with the reasons | Built-in |
| **Format for the builder:** Divi gets native Divi modules; Elementor and Gutenberg get clean HTML in your Single Post template | Built-in |
| Schedule it to go live after the **3-day review window** | WordPress |

---

## Setup (about 40 minutes, once)

### 1. Repo
Create a **Private** repo on GitHub and upload every file, including the hidden `.github` folder.

### 2. Secrets
Go to **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com → API keys (add credit) |
| `GSC_SERVICE_ACCOUNT_JSON` | See step 5 |
| `PEXELS_API_KEY` | pexels.com/api → free key (optional; without it, Openverse CC0 images are used) |
| `WP_PASS_<SITE KEY>` | One per site, see step 3 |

### 3. WordPress (each site)
1. Create a user for the platform: **Editor** role, or **Administrator** if you want FAQ schema added automatically.
2. **Users → Profile → Application Passwords**, type `SEO Autopilot` and click **Add New**. Copy the password.
3. Save it as a GitHub secret `WP_PASS_` + the site key in capitals with `-` changed to `_`. For example, `nexgen-internet` becomes `WP_PASS_NEXGEN_INTERNET`.
4. Upload **`wordpress-plugin/seo-autopilot-meta.php`** to `wp-content/mu-plugins/`, or zip it and install it as a plugin. This lets the platform set the Rank Math title, description and focus keyword, and switch on the Divi Builder for its posts.

### 4. Builders
- **Elementor sites:** make sure you have a **Single Post template** (Elementor Pro → Theme Builder → Single Post, with a *Post Content* widget), or that your theme styles blog posts. New blogs appear inside it with your fonts and colours. Posts are not marked "Edit with Elementor", which avoids the blank-page bug.
- **Divi sites:** posts arrive as a Divi Builder layout (Text, Image, Toggle (FAQ) and Call-To-Action modules), so you can open them in the Visual Builder. If you use a Divi Theme Builder post template, it wraps them automatically.
- **Detection is automatic** (`builder: auto`). The `test` command shows what it found. If a site is detected wrongly, set `builder: divi`, `elementor` or `gutenberg` in `sites.yaml`.

### 5. Search Console (works across different Google accounts)
1. At console.cloud.google.com, create a project. Go to **APIs & Services → Library → Google Search Console API → Enable**.
2. Go to **IAM & Admin → Service Accounts → Create**, then **Keys → Add key → JSON**. Paste the whole file into the `GSC_SERVICE_ACCOUNT_JSON` secret.
3. For **each site**, open Search Console with whichever Google account owns it, then go to **Settings → Users and permissions → Add user**. Paste the service account email and choose **Restricted**.

### 6. `sites.yaml`
One block per site. The most important fields:

| Field | Meaning |
|---|---|
| `niche`, `audience`, `tone` | Make every site distinct. This is the biggest safety and quality factor. |
| `seed_keywords` | 3–6 core phrases |
| `competitors` | 2–3 competitor domains, used for content gaps and analysis |
| `group` | Sites in the same niche share a group so they never get the same topic |
| `interval_days` | `2` = one blog every 2 days. `5` = two blogs per 10 days. |
| `ymyl: true` | Money, credit or health sites: every post waits as a draft for you |
| `builder` | `auto` / `divi` / `elementor` / `gutenberg` |
| `toc_plugin: true` | Set this if a TOC plugin already inserts tables of contents |
| `author_id` | WordPress user ID of a real author with a bio |
| `enabled` | Keep `false` until `test` passes |

### 7. Test, then switch on
**Actions → SEO Autopilot → Run workflow**:
1. `test`: shows a ✓ or ✗ per site for WordPress, the builder found, and Search Console.
2. `audit` and then `research`: fill the dashboard.
3. `plan`: shows the next topic per site. Nothing is written.
4. `write` with **site** set to one site: writes one blog now. Check it in WordPress under **Posts → Scheduled** (or **Drafts**).
5. Set `enabled: true` for each site. The daily schedule takes over from there.

**To stop everything:** go to **Settings → Variables → New variable** and add `AUTOPILOT_PAUSED` = `true`.

---

## Dashboard

Each run saves **`dashboard.html`**. Open the run in **Actions**, then **Artifacts → dashboard**, unzip it and open the file. It shows per site: the builder, cadence, health score, Search Console trend, every blog with its **Rank Math score**, **humanize score** and review notes (hover for details), issues, competitor gaps, topic candidates, internal links to add and backlink prospecting searches.

(GitHub Pages can host it too, but Pages URLs are public even for private repos.)

---

## Commands

| Command | Does |
|---|---|
| `test` | Checks WordPress access, the builder and Search Console |
| `due` | Lists which sites are due a blog today |
| `plan` | Next topic per site (no writing) |
| `write` | Writes 1 blog **now** for the chosen site(s), ignoring the schedule |
| `daily` | Writes 1 blog for every site that's due today |
| `audit` | Site audit + internal links + competitor gaps |
| `research` | Search Console + Autocomplete |
| `report` | Rebuilds the dashboard |
| `auto` | What the daily schedule runs |

---

## Costs (be aware of these)

| Item | Cost |
|---|---|
| GitHub private repo + Actions | Free. Expect ~800–1,000 of the 2,000 free minutes a month for 20 sites (4 sites are written in parallel). |
| Search Console, Autocomplete, competitor analysis, Openverse, Pexels | Free |
| Claude API | About **$0.40–0.60 per blog** (research with Google searches, writing, the humanize edit, Rank Math fixes) |

At **20 sites × 1 blog every 2 days ≈ 300 blogs a month, that's roughly $120–180 a month.** To lower it, use `interval_days: 3` (about 200 blogs, $80–120), `use_web_research: false` on smaller sites, or set the repo variable `CLAUDE_MODEL` to a cheaper model. The dashboard shows the estimated cost of every run.

---

## Honest limits
- **No search-volume numbers.** The free sources show real demand, but not monthly volumes.
- **No backlink index.** Seeing who links to competitors needs a paid source. The platform gives internal-link fixes and manual prospecting searches.
- **AI detectors:** the humanize step makes text read naturally and removes machine tells. No tool can honestly guarantee a "0% AI" score, and Google doesn't use those detectors. Usefulness and originality are what matter.
- **Rank Math's own score** is calculated by Rank Math when you open the post in WordPress. The built-in checker runs the same tests, so it should show 80–100.
- **Plagiarism:** the built-in check covers all *your* sites. Keep running your online checker during the review window.

---

## Files

```
sites.yaml                 your sites (edit this)
SAFETY.md                  how the platform keeps sites safe + your checklist
seo_platform/
  scheduler.py   1 blog / site / 2 days, staggered      planner.py      topic selection
  writer.py      research brief + article (Claude)     competitors.py  free competitor analysis + gaps
  humanize.py    editor pass, AI-phrase scrubber       rankmath.py     21 Rank Math tests + auto-fix
  images.py      Pexels / Openverse photos             formats.py      Divi / Elementor / Gutenberg output
  safety.py      link rules, traffic pause, gates      originality.py  cross-site duplicate check
  pipeline.py    one blog end to end                   publisher.py    WordPress scheduling
  crawler.py     site audit    gsc.py  Search Console  keywords.py     Autocomplete
  links.py       internal links + prospecting          report.py       dashboard data
docs/index.html            dashboard
wordpress-plugin/          helper for Rank Math / Yoast fields + Divi flag
.github/workflows/         the daily schedule
tests/                     `pytest` (fake WordPress, fake Divi site, fake Claude)
```
