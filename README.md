# sudoblark.ai.sdlc-hackathon

This repository is the starter code for the LLMs in the SDLC hackathon run by Sudoblark. As such, it's intended to be utilised alongside the [LLMs in the SDLC](https://sudoblark.com/whitepapers/llms-in-the-sdlc) guide. That guide covers the workflow we're trying to emulate, as well as setup instructions.

## Quick start

Install the prerequisites from the guide, create an empty repository in your own GitHub account, then:

```bash
git clone https://github.com/sudoblark/sudoblark.ai.sdlc-hackathon.git
cd sudoblark.ai.sdlc-hackathon
git remote set-url origin https://github.com/<your-username>/<your-repository>.git
git push -u origin main
claude
```

In Claude Code, run `/start-ticket TKT-01` to work a starter ticket, or describe your own idea and ask the agent to log it as a ticket.

## What's in the repository

| Path | What it's for |
| --- | --- |
| `AGENTS.md` | Dictates agent behaviour. |
| `CLAUDE.md` | Imports `AGENTS.md`, because Claude Code reads `CLAUDE.md`. |
| `.claude/skills/log-ticket/` | Used to log tickets in a standardised format. |
| `.claude/skills/start-ticket/` | Used to work on an already logged ticket, one atomic commit at a time. |
| `.claude/settings.json` | Claude Code's permission rules. |
| `work/` | Tickets, one file each, including five starter projects. Used for convenience, but in the actual workplace you'll probably use an external ticketing system. |

## The expected workflow

1. Use `/log-ticket` in a fresh agent conversation to describe an idea, refine it with an agent, then log it as a ticket under the `work/` folder. 
2. Use `/start-ticket` in a fresh agent conversation to work through the ticket, one commit at a time.
   1. The agent should work one atomic commit at a time. Building out a row of the plan, running checks, then proposing a commit message. It'll then wait for you to review the code, commit it or push back.
   1. Once you're happy with the commit, and have informed the agent the commit has been committed, it'll move on to the next commit in the plan.
   1. Once all commits are done in the plan, the agent will move on to any identified post-commit testing before asking you to close the ticket.


To avoid scope creep, any new work found along the way either:

1. Becomes a new row in the commit plan if it's small enough, and you approve the change in the commit plan.
2. Becomes a new ticket, as you have deemed the scope creep too great for it to be actioned in the current ticket.

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) with the ticket number at the end, as `AGENTS.md` describes.

## Starter tickets

| Ticket | Project |
| --- | --- |
| [TKT-01](work/TKT-01%20Build%20a%20tabletop%20dice%20roller.md) | Build a tabletop dice roller |
| [TKT-02](work/TKT-02%20Build%20a%20Caesar%20cipher%20cracker.md) | Build a Caesar cipher cracker |
| [TKT-03](work/TKT-03%20Build%20a%20text%20adventure.md) | Build a text adventure |
| [TKT-04](work/TKT-04%20Build%20a%20space%20trading%20game.md) | Build a space trading game |
| [TKT-05](work/TKT-05%20Build%20an%20ASCII%20dungeon%20explorer.md) | Build an ASCII dungeon explorer |

These are just some fun ideas to get you started. Populating them as detailed tickets is the first task of the hackathon; that, or logging a ticket with your own fun idea to work on!

## Using a different agent

Agents that read `AGENTS.md`, such as GitHub Copilot, follow the repository's rules, but the skills and permission settings are written for Claude Code. You can still follow the workflow by asking your agent to read `.claude/skills/start-ticket/SKILL.md` and work through it.

## Licence

See [LICENSE.txt](LICENSE.txt).
