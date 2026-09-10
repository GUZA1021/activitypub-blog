# ActivityPub Federated Blogging Platform

A Django blogging platform that federates with the wider Fediverse
(Mastodon and other ActivityPub servers) using the ActivityPub protocol.

Bachelor project (BADM500), Computer Science, University of Southern Denmark.

## Live

**https://activitypub-blog.onrender.com**

Findable from Mastodon or any Fediverse server by searching
`@username@activitypub-blog.onrender.com`.

Hosted on Render's free tier, so the first request after inactivity takes
~30 seconds to wake the instance.

## What it does

A working blog — registration, login, posts, comments, pagination, user
search — extended with the building blocks needed to act as a real
ActivityPub actor. A Mastodon user can find, follow, and read posts from
this blog in their own feed, and reply to posts as comments.

Verified end-to-end against mastodon.social: actor discovery, follow/accept,
content delivery, and incoming replies.

## Implemented

| Feature | Description |
|---|---|
| Actor endpoint | Each user exposed as an ActivityPub `Person` (inbox, outbox, followers, public key) |
| WebFinger | Resolves `user@domain` handles to actor URLs (RFC 7033) |
| Inbox / Outbox | `OrderedCollection` endpoints for incoming and outgoing activities |
| HTTP Signatures | RSA-SHA256 signing of outgoing federation traffic, with SHA-256 body digest |
| Incoming Follow / Undo | Stores and removes remote followers, replies with a signed `Accept` |
| Outgoing Follow | WebFinger lookup of a remote actor, then a signed `Follow` to their inbox |
| Content delivery | Pushes `Create(Note)` to every follower inbox on publish |
| Incoming Create | Stores remote replies as comments via `inReplyTo` |

## Stack

- **Backend** — Django, Python
- **Database** — PostgreSQL in production, SQLite in development
- **Frontend** — Django templates, Bulma
- **Auth** — Django's built-in auth, with `AbstractUser` extended to carry a
  per-user RSA key pair
- **Deployment** — Render (Gunicorn/WSGI)

Views are split by concern: `blog_views.py` for the blog itself,
`activitypub_view.py` for actor, outbox, collections and outgoing
federation, `activitypub_inbox.py` for incoming activities.

## Running locally

Federation needs a public HTTPS domain, so a local instance runs as a plain
blog with federation disabled.

    cd code/activitypub
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

To exercise federation, expose the server through a tunnel (ngrok or
similar) — Mastodon will not talk to `localhost`.

## Architecture

Documented with the C4 model (Context → Container → Component), plus a
sequence diagram of the full Follow/Accept flow against Mastodon.
See [BAproject.pdf](report/BAproject.pdf).

## Things that turned out to be harder than expected

**Spec-compliant is not the same as compatible.** Blog posts were originally
`Article` objects, which is what the spec suggests for long-form content.
Mastodon renders `Article` as a bare clickable link showing only the title.
Switching to `Note` made posts render natively in the feed. The Fediverse is
shaped as much by how the dominant implementation behaves as by the
specification.

**HTTP Signature formatting is unforgiving.** The signing string must
reconstruct byte-for-byte on the receiving end, in exact header order. One
concrete example: the `Date` header needs the weekday
(`Mon, 22 Oct 2013 14:36:43 GMT`), but Mastodon's own documentation shows it
without — an easy detail to copy wrong. A mismatch fails silently.

**A `unique=True` in the wrong place.** The `Follower` model made
`actor_url` unique across the whole table, meaning a given remote actor could
only follow one local user. The symptom was strange: a follow from Mastodon
would appear to work, then the follower count dropped back to zero after
about twenty seconds. Fixed with a composite unique constraint on
`(actor_url, user)`.

**Federation can only be debugged in production.** Mastodon requires public
HTTPS, so every change had to be deployed before it could be tested, and a
failed federation attempt usually produced no error at all on either side —
just silence. Most debugging was print statements, Render logs, and diffing
JSON output against the spec.

## Testing

Manual: JSON output from each endpoint compared against the ActivityStreams
2.0 spec and Mastodon's documentation, then live verification against
mastodon.social for actor search, follow, delivery and replies.

## Known limitations

- **Incoming HTTP Signatures are not verified.** Outgoing requests are
  signed, but activities arriving at the inbox are accepted without checking
  the sender's signature — a remote server could impersonate an actor. This
  is the first thing a real deployment would need.
- The outbox returns every activity at once rather than paginating with
  `OrderedCollectionPage`.
- Delivery is synchronous, with no queue and no retry, so a follower on an
  offline instance simply misses the post.
- No shared-inbox optimisation: an instance with many followers receives the
  same activity once per follower.
- Private keys are stored unencrypted in the database.

## Team

Bachelor project by Mohammad Adnan Amin and Karim Adnan Amin, supervised by
Stelios Tsampas, University of Southern Denmark, June 2026.

The work was done jointly rather than split into separate modules. The
federation layer in particular was built and debugged together, since most
of the difficulty was in figuring out what Mastodon actually expected.
This repository is my copy, published with Mohammad's consent.

## References

- [ActivityPub (W3C)](https://www.w3.org/TR/activitypub/)
- [ActivityStreams 2.0 (W3C)](https://www.w3.org/TR/activitystreams-core/)
- [RFC 7033 — WebFinger](https://datatracker.ietf.org/doc/html/rfc7033)
- [Mastodon documentation](https://docs.joinmastodon.org/)
- Prodromou, E. *ActivityPub*. O'Reilly, 2024.