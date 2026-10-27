# Marcie Privacy Policy

_Last updated: October 27, 2026_

Marcie is a Discord bot that looks up Final Fantasy Trading Card Game (FFTCG) cards. This policy explains what information Marcie handles, why, and how long it is kept. Marcie is run by btawa ("we").

## What Marcie stores

For each Discord server Marcie is added to, we store:

- the server's ID
- the server's name
- the command prefix set for that server (`?` by default)

This is used only to know which prefix to respond to in each server. It is kept for as long as Marcie is in the server and deleted when Marcie is removed.

We do not store any information about individual users.

## What Marcie logs

To find and fix problems, Marcie writes a log entry each time a command is used. A log entry contains:

- the text of the command (for example `?name auron` or `/adv name:yuna`)
- the card or result that was returned
- the time, and a random request ID that is also shown on Marcie's reply

Logs do not include your Discord user ID, username, or which server the command came from. Logs are deleted automatically as they rotate out, and are not kept long term.

## Messages Marcie reads

Discord lets Marcie see messages in channels it has access to. Marcie only checks whether a message is a Marcie command (for example, it starts with the server's prefix). Other messages are ignored and are never stored or logged. After a search with several matches, Marcie also reads the next message from the person who ran the command, to see whether it is the number of a card.

## Services Marcie uses

- **Discord** delivers all messages and commands. Discord's own [Privacy Policy](https://discord.com/privacy) applies to your use of Discord.
- **Card data** comes from our own card API. Card images are hosted on Google Cloud Storage and loaded by Discord, not by your device directly.
- **ffdecks.com**: when you use the `ffdeck` command, Marcie sends the deck link you provided to ffdecks.com to fetch the decklist. No information about you is sent.

We do not sell, rent, or share any information with anyone else, and Marcie has no advertising or analytics.

## Your choices

- Server owners and administrators can remove Marcie at any time. This deletes the stored server information.
- If you have a question about your data or want to ask for something to be removed, contact us in the [Marcie support Discord](https://discord.gg/ZUZY7wb).

Because log entries are not linked to a user ID or username, we generally cannot identify which entries came from a specific person.

## Legal basis

Where data protection laws such as the GDPR apply, we process the information above based on our legitimate interest in running Marcie and keeping it working.

## Children

Marcie is available only through Discord, which requires users to meet its minimum age. We do not knowingly collect information about children.

## Changes to this policy

If this policy changes, the updated version will be posted here with a new "Last updated" date.
