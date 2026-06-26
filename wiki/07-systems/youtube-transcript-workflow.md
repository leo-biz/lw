---
title: YouTube Transcript Workflow
node_type: playbook
domain: systems
status: AI_REVIEWED
audience: technical/internal
tags:
  - systems
  - learning
  - youtube-transcript
  - playbook
  - ai-reviewed
created: 2026-05-30
updated: 2026-05-30
---

# YouTube Transcript Workflow

## Purpose

Preserve compact YouTube transcript sources and turn useful videos into application, not piles of caption markup.

## Default Fetch

Use:

```bash
python3 scripts/fetch_youtube_transcript.py "<youtube-url>"
```

This writes one raw source file:

```text
raw/transcripts/<video-id>.md
```

The Markdown file holds source metadata and a timestamped transcript. Raw transcripts stay on disk and are not loaded into agent context unless an agent deliberately opens or searches them.

The fetcher also refreshes `raw/transcripts/manifest.md`, a lightweight registry agents can scan before opening transcript files.

Use `--json` only when an automation specifically needs structured snippets:

```bash
python3 scripts/fetch_youtube_transcript.py "<youtube-url>" --json
```

## Playlist Capture

Use `scripts/youtube_queue.py` when YouTube playlists are the capture interface:

```text
YouTube Inbox playlist
-> transcript captured in raw/transcripts/
-> video moved to YouTube Captured playlist
-> focused AI review later, only when useful
```

Run a bounded pass:

```bash
python3 scripts/youtube_queue.py --limit 5
```

Use `--dry-run` to preview the batch. A fetch failure must leave the video in the inbox playlist.

The destination playlist means `Captured`, not `Reviewed`. Capture preserves the source; it does not mean the source has been synthesized or approved.

## Scheduled Capture

Install a local `launchd` job:

```bash
sh scripts/install_youtube_queue_launchd.sh
```

The default interval is six hours and each pass processes at most five queued videos. To choose another interval, reinstall with a number of seconds:

```bash
INTERVAL_SECONDS=43200 sh scripts/install_youtube_queue_launchd.sh
```

Compact summaries are appended to the Git-ignored local file `runs/youtube-queue.jsonl`. Empty runs are recorded with zero counts. A failed transcript remains queued and appears in the summary's `failed` count. Scheduler stdout and stderr are also kept under `runs/` for local troubleshooting.

## Credentials

Keep OAuth material outside the vault:

```text
~/.config/leo-life/youtube/client_secrets.json
~/.config/leo-life/youtube/youtube_token.json
```

Use `LEO_LIFE_YOUTUBE_CONFIG_DIR` to override that directory. OAuth files were moved out of the vault on 2026-05-30. The queue script temporarily supports the older `scripts/` credential location only as a migration fallback, and those paths remain Git-ignored.

## Fallback

Use `yt-dlp` VTT captions only when `youtube-transcript-api` cannot retrieve a usable transcript.

VTT is a fallback because rolling captions repeat text and inline timing markup wastes context.

## Metadata

The fetcher creates `raw/transcripts/<video-id>.md`. Add creator, publish date, duration, and a processing note when the video is worth preserving.

## Manifest

`raw/transcripts/manifest.md` is a lightweight index auto-generated from the `status` frontmatter field in each transcript file. Agents scan it before opening transcript files to avoid loading unnecessary content.

**Always refresh the manifest after any status change** (`AI_REVIEWED`, `HUMAN_REVIEWED`, etc.):

```bash
python3 scripts/fetch_youtube_transcript.py --refresh-manifest
```

A stale manifest causes agents to scan or skip the wrong files. Refresh it as the last step after marking a transcript reviewed, not as an afterthought.

## Review

For useful videos:

1. Preserve the compact raw Markdown source.
2. Create a focused review under `wiki/05-learning/transcript-reviews/`.
3. Extract only durable ideas.
4. Create tasks only when there is a clear outcome and definition of done.
5. Update the learning inbox, index, review inbox, and log when meaningful.
6. Run `python3 scripts/fetch_youtube_transcript.py --refresh-manifest` to sync the manifest.

## Installation

```bash
python3 -m pip install --user youtube-transcript-api
```

The library uses unofficial YouTube caption access and may break or face IP blocking. Keep `yt-dlp` as a fallback.

## Linked Nodes

- implements: [[learning-to-application-loop]]
- related_to: [[../05-learning/learning-inbox]]
- related_to: [[vault-maintainer-protocol]]
