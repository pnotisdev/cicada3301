# Phase 52: An End hash hunt in web archives

Target: SHA-512-length value of An End, `36367763ab73...2a8b4` (full value in `results/payload/hashes.txt`). Nothing in LP2 is solved.

## Verdict

**No match.** 124,017 digests over 3,739 candidate files (local 43,682 / fetched 80,335); full-512 matches: 0.

## 1. URL list (from local archives)

Harvested from 1,333 text files of 'Other repositories and work/', the wiki download (`work/ref/uncovering_cicada/`, 258 pages, finished) and `work/ref/`: 528 distinct URL strings; 34 distinct 16-character v2 onion hosts (some are placeholders/typos such as `xx3xxxxxxx7xxxxx`, `xxxxxsdvx6pm2rsk`), plus clearnet hosts (pastebin 226 URL strings, imgur ~108, 845145127.com, web.archive.org 23, etc.). Raw list: `work/phase52/urls_raw.json`.

Onion hosts: `33ol2ol4zmiphtjz`, `4l6uipnstbggwjyv`, `5plune7qfnklor46`, `6dq7xsfmdpqmksyw`, `auqgnxjtvdbll3pv`, `avowyfgl5lkzfj3n`, `cginiziglyaobyph`, `cu343l33nqaekrnw`, `e75g73jqcudlwcrn`, `emiwp4muu2ktwknf`, `eq6emgv2ehsrix6t`, `erwfcsdvx6pm2rsk`, `fv7lyucmeozzd5j4`, `gbyh7znm6c7ezsmr`, `jhiwjjlqpyawmpjx`, `jm7d2oei2ddzmqu5`, `kholyg7cewyywujo`, `ky2khlqdf7qdznac`, `ll5afyskb6v6g7ga`, `lw4ipk5choakk5ze`, `nlskglcrw6k3pevc`, `p7amjopgric7dfdi`, `pklmx2eeh6fjt7zf`, `q4utgdi2n4m4uim5`, `qw7mhchzvuq6f2mf`, `r7ynbvzmfi4q467h`, `sms4tor3vcr2geip`, `sq6wmgv2zcsrix6t`, `ut3qtzbrvs7dtvzp`, `wzwmcwmsk5cb7gjn`, `xsxnaksict6egxkq`, `xx3xxxxxxx7xxxxx`, `xxxxxsdvx6pm2rsk`, `y2wyuvrqraowagc5`

## 2. Wayback CDX captures per onion host (all gateway forms; counts are CDX rows incl. non-200)

| onion host | forms with captures (rows) |
|---|---|
| `33ol2ol4zmiphtjz` | 33ol2ol4zmiphtjz.onion.to (43) |
| `4l6uipnstbggwjyv` | none |
| `5plune7qfnklor46` | none |
| `6dq7xsfmdpqmksyw` | none |
| `auqgnxjtvdbll3pv` | auqgnxjtvdbll3pv.onion.to (68); auqgnxjtvdbll3pv.tor2web.org (7) |
| `avowyfgl5lkzfj3n` | avowyfgl5lkzfj3n.onion.to (15); avowyfgl5lkzfj3n.tor2web.org (1) |
| `cginiziglyaobyph` | none |
| `cu343l33nqaekrnw` | cu343l33nqaekrnw.onion.to (64); cu343l33nqaekrnw.tor2web.org (2) |
| `e75g73jqcudlwcrn` | none |
| `emiwp4muu2ktwknf` | emiwp4muu2ktwknf.onion.to (17) |
| `eq6emgv2ehsrix6t` | none |
| `erwfcsdvx6pm2rsk` | none |
| `fv7lyucmeozzd5j4` | fv7lyucmeozzd5j4.onion.to (71); fv7lyucmeozzd5j4.tor2web.org (1) |
| `gbyh7znm6c7ezsmr` | none |
| `jhiwjjlqpyawmpjx` | jhiwjjlqpyawmpjx.onion (19); jhiwjjlqpyawmpjx.onion.to (357); jhiwjjlqpyawmpjx.tor2web.org (2); jhiwjjlqpyawmpjx.onion.city (18); jhiwjjlqpyawmpjx.onion.sh (2); jhiwjjlqpyawmpjx.onion.link (3) |
| `jm7d2oei2ddzmqu5` | jm7d2oei2ddzmqu5.onion.to (17) |
| `kholyg7cewyywujo` | none |
| `ky2khlqdf7qdznac` | ky2khlqdf7qdznac.onion.to (14) |
| `ll5afyskb6v6g7ga` | none |
| `lw4ipk5choakk5ze` | lw4ipk5choakk5ze.onion (1); lw4ipk5choakk5ze.onion.to (121); lw4ipk5choakk5ze.onion.city (37); lw4ipk5choakk5ze.onion.cab (3); lw4ipk5choakk5ze.tor2web.io (2); lw4ipk5choakk5ze.onion.ws (6); lw4ipk5choakk5ze.onion.nu (1); lw4ipk5choakk5ze.onion.link (8) |
| `nlskglcrw6k3pevc` | nlskglcrw6k3pevc.onion.to (18) |
| `p7amjopgric7dfdi` | p7amjopgric7dfdi.onion.to (32) |
| `pklmx2eeh6fjt7zf` | pklmx2eeh6fjt7zf.onion.to (39) |
| `q4utgdi2n4m4uim5` | none |
| `qw7mhchzvuq6f2mf` | none |
| `r7ynbvzmfi4q467h` | none |
| `sms4tor3vcr2geip` | sms4tor3vcr2geip.onion (2); sms4tor3vcr2geip.onion.to (51); sms4tor3vcr2geip.tor2web.org (9); sms4tor3vcr2geip.onion.city (20); sms4tor3vcr2geip.onion.link (4); sms4tor3vcr2geip.onion.lt (5) |
| `sq6wmgv2zcsrix6t` | none |
| `ut3qtzbrvs7dtvzp` | ut3qtzbrvs7dtvzp.tor2web.org (19) |
| `wzwmcwmsk5cb7gjn` | wzwmcwmsk5cb7gjn.onion.to (25) |
| `xsxnaksict6egxkq` | xsxnaksict6egxkq.onion.to (23); xsxnaksict6egxkq.onion.link (4) |
| `xx3xxxxxxx7xxxxx` | none |
| `xxxxxsdvx6pm2rsk` | none |
| `y2wyuvrqraowagc5` | none |

Clearnet / other queries with captures:

- `1853143003544.tk/*`: 13 rows
- `845145127.com/*`: 934 rows
- `3301.org/*`: 14 rows
- `cicada3301.com/*`: 1495 rows (cap 2000; NOT fetched, modern site)
- `cicadasolver.tumblr.com/*`: 101 rows
- `dragonstudios.tk/*`: 1 rows
- `cicada3301.org/*`: 2000 rows (cap 2000; NOT fetched, modern site)
- `cicada3301.boards.net/*`: 2000 rows (cap 2000; NOT fetched, modern site)
- `www.cicadasolvers.com/*`: 2000 rows (cap 2000; NOT fetched, modern site)
- 318 exact pastebin/imgur/845145127/other URLs had captures (of 376 queried); see `work/phase52/cdx_results.json`.

Total queries: 862; with at least one capture: 366; failed: 0.

## 3. Fetched bytes (Wayback `id_` mode)

2025 captures attempted (tier 1: onion/gateway/845145127.com/1853143003544.tk/3301.org/tumblr = 399 unique (URL, content digest) pairs with status 200; tier 2: pastebin/dpaste/845145127 exact URLs). 2009 fetched, 16 not retrievable (404/blocked). Stored in git-ignored `work/ref/an_end_hunt/` with `manifest.jsonl` (URL, capture time, fetch time, SHA-256). Bytes only; nothing opened or executed.

Local archive copies hashed too: every file in `Other repositories and work/` (1.3 GB), the wiki download and `work/ref/online_2026-10-21/` (1,826 files).

## 4. Hashing

Functions: sha512, sha3_512, blake2b-512 (hashlib); whirlpool (own pure-Python, checked on the published empty-string and 'abc' vectors) and streebog-512 (`gostcrypto`, checked on 'abc'). Whirlpool and streebog were computed only for variants of at most 30,000 bytes (pure Python is slow); the three hashlib functions for every file. Binary media (jpg/png/mp4/pdf/docx...) got raw bytes only. Variants for text/HTML: raw; body without HTTP headers; LF; CRLF; each with/without one trailing newline; visible text (tags, scripts, comments stripped, entities decoded) as-is / stripped / whitespace-collapsed / one line per non-empty line, each with and without a trailing newline.

Positive control: a sample page's every (variant, function) digest was planted as the target and found 50/50 times. Prefix/suffix-12 near-hits were also searched (chance per digest ~2^-47): none unless listed below.

- Local pass: 1826 files, 43,682 digests, hits []
- Fetched pass: 1913 unique bodies, 80,335 digests, hits []

## 5. Not reachable / not done

- Ahmia: reachable (needs the form's hidden token), but returns nothing for the v2 hosts tried (auqgnxjtvdbll3pv, cu343l33nqaekrnw, cginiziglyaobyph, fv7lyucmeozzd5j4, avowyfgl5lkzfj3n); it indexes v3 onions only. Results: `work/phase52/ahmia_results.json`.
- Wayback served 'Temporarily Offline' / timeouts at times; every query was retried until it answered (0 failed).
- Excluded from fetching: cicada3301.com / cicada3301.org / cicada3301.boards.net / www.cicadasolvers.com (modern sites, 4,479 unique captures, not deep-web pages), imgur image captures, a reddit listing page.
- Blocked by antivirus, not hashed: `http://845145127.com` @20170606010037 (Windows Defender: Trojan:HTML/Redirector.SLYB!MTB, an injected script in an old archived page; quarantined, copy deleted, not re-fetched). Another 23 captures (all 845145127.com archived pages, same site) became unreadable on disk after fetching; presumed also quarantined by the antivirus, not verified, so treated as not hashed: http://845145127.com/ @20180806090558, http://845145127.com/ @20220601125451, http://845145127.com/web/20140201000000/http://845145127.com/ @20200810221958, http://www.845145127.com/_static/css/banner-styles.css?v=_99BHQfY @20200817134926, http://845145127.com/ @20170912015807, http://845145127.com/ @20181110155856, http://845145127.com/ @20240302053644, http://845145127.com/162667212858.jpg @20181023012849, http://845145127.com/web/20130601000000/http://845145127.com/ @20200811031102, http://www.845145127.com/ @20240305140836, https://845145127.com/ @20250827232459, http://845145127.com/ @20171027223707, http://845145127.com/162667212858.jpg @20201111232249, http://845145127.com/web/20130701000000/http://845145127.com/ @20200811031014, http://845145127.com/web/20140215000000/http://845145127.com/ @20200810221941, http://www1.845145127.com/?tm=1&subid4=1671628304.0366530000&kw=Hacking&KW1=Ethical%20Cracking%20And%20Penetration%20Testing&KW2=IP%20Scanner%20Network%20Monitoring&KW3=Cloud%20Security%20Management&searchbox=0&domainname=0&backfill=0 @20221221131144, https://845145127.com/ @20250828202603, http://845145127.com @20170606010037, http://845145127.com/ @20180521081414, http://845145127.com/ @20201110123626, http://845145127.com/_static/css/iconochive.css?v=qtvMKcIJ @20200817135112, http://845145127.com/web/20130901000000/http://845145127.com/ @20200814024658, http://www.845145127.com/ @20250818112915, http://www1.845145127.com/?tm=1&subid4=1671628313.0430340000&kw=Hacking&KW1=Ethical%20Cracking%20And%20Penetration%20Testing&KW2=IP%20Scanner%20Network%20Monitoring&KW3=Cloud%20Security%20Management&searchbox=0&domainname=0&backfill=0 @20221221131154.
- Only Wayback was queried; archive.today, Common Crawl, and tor2web-era mirrors outside Wayback were not.
- A content hash matches only if the page bytes were captured exactly (Wayback's `id_` mode is the original body, but servers that rewrote or compressed content, or a page never captured, cannot be excluded). Captures with non-200 status were not fetched.

## 6. Antivirus follow-up

Defender quarantined or deleted fetched captures (flag names reported to me: Redirector.SLYB, Redirector.BAA, JS/KryptoStealer). All are recorded as **blocked by antivirus, not hashed**: 24 captures (14 distinct URLs, all on 845145127.com) are missing on disk, listed by `timestamp_sha256prefix` in `work/phase52/skiplist_blocked.txt`; the owner's count is 26, so 2 more may have gone after my last check and are not distinguishable from the manifest. These captures are never fetched again (the fetcher skips anything already in the manifest). No further downloads were needed: every capture inside the scope in section 3 had already been fetched, so the hunt is complete as scoped. Because these blocked pages are exactly the injected-script 845145127.com pages, a match among them cannot be excluded; hashing them would need the bytes held outside the antivirus's reach, which was not attempted.
