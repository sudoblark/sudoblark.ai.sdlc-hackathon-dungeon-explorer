# sudoblark.ai.sdlc-hackathon-dungeon-explorer

This repository is a fully worked example project from the LLMs in the SDLC hackathon run by Sudoblark. Specifically, it is a silly little ASCII Dungeon Explorer made in two hours to demonstrate the principles of the hackathon.

For further context please see:

1. The [LLMs in the SDLC](https://sudoblark.com/talks/llms-in-the-sdlc/) hackathon guide, given to attendees prior to the hackathon.
2. The [sudoblark.ai.sdlc-hackathon](https://github.com/sudoblark/sudoblark.ai.sdlc-hackathon) starter code repository, from which this repository is cloned.
3. The [dungeon-explorer/](dungeon-explorer/README.md) README for details on how to play the game!

## How it was built

I built it the way attendees do at the hackathon:

1. I cloned the starter repo, which brings the agent's rules in [AGENTS.md](AGENTS.md), the `log-ticket` and `start-ticket` skills, and sample tickets.
2. I picked [TKT-05](work/TKT-05%20Build%20an%20ASCII%20dungeon%20explorer.md), the dungeon explorer. The agent asked me about the tooling and proposed a commit plan, which I signed off.
3. We worked the plan one commit at a time. The agent built each commit and proposed its message, and I reviewed and committed it. Stretch goals, and ideas from play-testing, became new rows in the plan.
4. I merged the result in [PR #1](https://github.com/sudoblark/sudoblark.ai.sdlc-hackathon-dungeon-explorer/pull/1) and released it as [0.1.0](https://github.com/sudoblark/sudoblark.ai.sdlc-hackathon-dungeon-explorer/releases/tag/0.1.0).

TKT-05 records every decision and the reason for it, so it's the best place to see how the agent and I worked together.

## Playing the game

You need [uv](https://docs.astral.sh/uv/). From the `dungeon-explorer` folder:

```bash
uv sync
uv run dungeon-explorer
```

The [game's README](dungeon-explorer/README.md) covers the keys, the symbols and the settings.

## Licence

See [LICENSE.txt](LICENSE.txt).
