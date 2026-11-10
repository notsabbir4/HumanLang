# The website's server side (Supabase)

The website is static. Three things need a server, and they live in one Supabase project:

- **Accounts** (sign in with GitHub) and **profiles**.
- **Shared programs** (code together): tables `rooms`, `room_members`, and private Realtime channels.
- **Nina**: the Edge Function in `functions/nina`.

The two values in `website/build.py` (`SUPABASE`) are public on purpose. Secret keys never go in this repository.

## Switching things on (done once, in the Supabase dashboard)

1. **GitHub sign-in:** Authentication > Sign In / Providers > GitHub. Make a GitHub OAuth App
   (GitHub > Settings > Developer settings > OAuth Apps > New). Its callback URL is shown on the Supabase GitHub page.
   Paste the Client ID and Client Secret into Supabase. Under Authentication > URL Configuration set the Site URL to
   `https://notsabbir4.github.io/HumanLang/` and add `https://notsabbir4.github.io/HumanLang/**` to the redirect URLs.
2. **Nina** (pick one; both are added in Edge Functions > Secrets):
   - **Free:** `GEMINI_API_KEY` from https://aistudio.google.com/apikey (Google's free tier; each person gets 60 steps a day).
     Optional `GEMINI_MODEL` to choose a model (default `gemini-flash-latest`).
   - **Paid:** `ANTHROPIC_API_KEY` (used instead of Gemini if both are set; 300 steps a day). Optional `NINA_MODEL`.
   `NINA_DAILY_LIMIT` changes the daily steps per person for either.

`functions/nina/gemini_test.ts` tests the Gemini part: `deno run --allow-all gemini_test.ts`.
