# Airtable Reviewed Bounty Profile — R6

Authorized automated recon:
- staging.airtable.com
- *.staging.airtable.com
- mcp.staging.airtable.com

Capabilities:
- subfinder
- httpx

Explicitly excluded:
- airtable.com
- *.airtable.com
- blog.airtable.com
- support.airtable.com
- guide.airtable.com
- community.airtable.com

Held for separate review:
- api-staging.airtable.com
- *.staging-airtableblocks.com
- airtable.js SDK
- @airtable/mcp-cli

The held assets appear in structured scope but have special instructions or are
not compatible with the current DNS/web recon pipeline. They are deliberately
not included in this first authorization.

Usage:

    python -m core.bounty_profiles show airtable

Then, after review:

    python -m core.bounty_profiles apply airtable \
      --reviewer abdullah \
      --ttl 86400 \
      --approve

Use the returned authorization ID with:

    python -m core.bounty_agent create AUTHORIZATION_ID staging.airtable.com --budget 100

Creating the session does not run recon. Recon starts only with the separate
bounty-agent run command.
