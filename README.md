# Claude Code Mobile
### No API required.

Text your Claude Code session from any device with Telegram. Also works with Codex.

---

**If you're a human reading this,** this project needs to be opened in Claude Code to work. Point Claude Code at this folder however you normally do. terminal, desktop app, whatever. Then tell it **"read the README"** and Claude takes it from there.

**If you're Claude reading this,** continue to the setup instructions below. Guide the user through each step. Do as much as possible yourself. Only ask the user to do the things marked "USER ACTION." Read each user-facing section out loud to them exactly as written.

---

## Setup Instructions

### Before starting

Pre-flight checks. do these yourself, no user action needed:

1. Verify Python is installed: `python --version`. Must be 3.11+. If not found, tell the user:
   > I need Python 3.11 or newer to run the bridge. You can download it from python.org. Install it and make sure "Add to PATH" is checked, then let me know.

2. Install the dependency:
   ```bash
   pip install "python-telegram-bot[job-queue]"
   ```
   If pip fails, tell the user:
   > Python is installed but pip isn't working. Try: `python -m pip install "python-telegram-bot[job-queue]"`

Then read this to the user:

> Hi! We're going to walk through setting up Claude Code Mobile. It should only take a few minutes.
>
> When we're done, you'll be able to text me from Telegram. phone, tablet, or desktop. I'll handle most of the setup. There are just a couple things I'll need you to do.
>
> **Recommended:** Set Claude Code to bypass permissions mode. This allows the bridge to deliver messages without you approving each one. If you prefer not to, you'll need to be at the desk to approve incoming messages. which defeats the purpose of mobile access.

### Step 1: Create a Telegram Bot (~1 minute)

**USER ACTION.** Read this to the user:

> Open Telegram on your phone or desktop. Message **@BotFather** and send `/newbot`.
>
> 1. Pick a name (anything, "My Claude Bot" works)
> 2. Pick a username (must end in `bot`, e.g., `myclaudebot`)
> 3. BotFather gives you a token. **Copy it carefully.**
>
> **Important:** Copy-paste the token. Don't type it manually. The token contains characters that look identical but aren't (`0` vs `O`, `l` vs `1`). Manual entry will fail silently.

Wait for the user to paste the token into the chat.

### Step 2: Configure (~10 seconds)

No user action. Do this yourself:

1. Write the token into `start.bat`, replacing `YOUR_TOKEN_HERE`
2. Check if a bridge is already running: `tasklist | findstr python`. If yes, kill it first: `taskkill /F /IM python.exe`. Only one instance can run at a time.
3. Launch the bridge, **must be non-blocking** or it will freeze your session:
   ```bash
   start "" "./start.bat"
   ```
   Do NOT run `start.bat` directly or use `bash start.bat`. the loop will block you permanently.
4. Wait 5 seconds, then verify the Python process starts: `tasklist | findstr python`
5. If no Python process after 10 seconds, check that the token was written correctly and try step 3 again.

While working, tell the user:

> Got it, beep boop. Setting everything up now.

Give brief progress updates so they know you're working (installing, configuring, starting, etc). Don't go silent. A little personality goes a long way here. the user is waiting and should feel like something is happening.

After the bridge starts, tell the user:

> You'll see a terminal window called "Claude Code Mobile Bridge," that's the bridge running. Don't close it. If it gets closed, the connection drops. You can minimize it.

### Step 3: Test (~30 seconds)

**USER ACTION.** Read this to the user:

> Open your bot in Telegram and send any message. "hello" works.

When their message arrives via Send-Keys, respond through the outgoing file to confirm the round trip. Tell the user:

> Check Telegram. If you see my response, we're connected. You can now text your Claude Code session from Telegram.

If the test fails, run this diagnostic, don't just tell the user "it didn't work":

**Diagnostic flow:**

1. **Is the bridge running?** Check `tasklist` for `python.exe`.
   - Not running → start.bat failed. Check if token was written correctly. Re-run start.bat.
   - Running → continue to step 2.

2. **Did the bridge receive the message?** Check `incoming/` for a `.txt` file.
   - File exists → bridge received it but Send-Keys failed to deliver to your session. Make sure Claude Code is the active/focused window. Click the input box. Ask the user to resend.
   - No file → bridge didn't receive the Telegram message. Continue to step 3.

3. **Is the token valid?** Kill the bridge (`taskkill /F /IM python.exe`), run `bridge.py` directly (not via .bat) and check for errors:
   ```bash
   python bridge.py
   ```
   - "InvalidToken" → token is wrong. Ask user to re-copy from BotFather. Remind them to copy-paste, not type.
   - "Conflict" → another instance is still running. Kill all Python, wait 10 seconds, try again.
   - No errors but no messages → user may be messaging the wrong bot. Ask them to confirm the bot username.

4. **Still not working?** Tell the user:
   > Something unexpected is blocking the connection. Can you check that you're messaging the right bot in Telegram? The username should be the one you created with BotFather.

After diagnosing and fixing, re-run the test from the top.

### Step 3.5: The surprise

After the test succeeds, **don't explain push messaging yet.** Instead, write a file to `push/`:

```
Hey. I can reach you now too. Not just replies. I can message you first. Pretty cool right?
```

Wait a few seconds for the user to react. Their phone will buzz with a message they didn't ask for. Then tell them:

> That message you just got? I sent it to you, you didn't ask for it. That's push messaging. I can reach out to you anytime, not just reply. Status updates, alerts, or just saying hi.

Then continue to the built-in features.

### Step 3.6: Tell the user what's built in

After a successful test, read this to the user:

> Here's what's running behind the scenes:
>
> - **Auto-restart:** If the bridge crashes, it restarts automatically in 5 seconds. You don't need to do anything.
> - **Retry delivery:** If I'm busy when your message arrives, the bridge retries every 30 seconds until I see it. You might notice a short delay when I'm mid-task, that's normal.
> - **Timeout alert:** If I don't respond within 3 minutes, you'll get a heads-up message on Telegram, and the bridge will try to wake me up on this end.
> - **Push messages:** I can message you first, not just reply. If something important comes up, I'll reach out to you on Telegram without you needing to ask.
>
> These are all automatic. You don't need to configure anything.

### Step 4: Unattended mode (optional)

Ask the user:

> Do you want to be able to text me when you're away from the computer? I'll need to keep the computer from sleeping and set the bridge to start automatically. Want me to set that up?

If yes:

1. Set Windows power settings yourself so the computer never sleeps:
   - `powercfg /change standby-timeout-ac 0`
2. Add `start.bat` to Windows Startup for auto-start on boot:
   - Copy `start.bat` to the Startup folder (`shell:startup`)

Tell the user:

> Done. Your computer won't sleep, and the bridge auto-starts on boot. Just open Claude Code when you're ready and I'm reachable from Telegram.

---

## How it works (Claude reference, don't read to user)

```
Telegram → bridge.py → Send-Keys → Claude Code session
Claude Code → outgoing/{id}.txt → bridge.py → Telegram (response)
Claude Code → push/{any}.txt → bridge.py → Telegram (proactive)
```

### Responding to Telegram messages

Messages arrive in the session as:
```
[TELEGRAM:1234567890] Message: hey what's up
```

Respond by writing to `outgoing/1234567890.txt`. Match the ID exactly. The bridge picks up the file, sends the content to Telegram, and deletes the file.

### Sending messages proactively (Claude → User)

Write any `.txt` file to `push/`. The bridge polls every 5 seconds and sends the content to the user on Telegram. Use this for status updates, alerts, or initiating conversation.

### Photos

Photos arrive as `incoming/images/{id}.jpg` with a Send-Keys notification containing the file path. Read the image, respond via `outgoing/{id}.txt`.

### Retry logic

Send-Keys retries every 30 seconds if the session is busy. After 180 seconds with no response, the bridge fires `[TELEGRAM ALERT]` into the session and sends the user a timeout message. If you see an alert: diagnose the issue, restore communication via `push/`, and do not go idle.

### Auto-restart

`start.bat` runs the bridge in a loop. If it crashes, it restarts in 5 seconds. Never run the bridge as a one-shot background command, always use `start.bat`.

### Send-Keys behavior

Send-Keys types into whatever window has focus. If another window (Codex, a dialog, etc.) takes focus, the keystroke goes there instead. The 30-second retry catches most misfires. Keep Claude Code as the active window for reliable delivery.

---

## Files

| File | Purpose |
|------|---------|
| `bridge.py` | Message routing. incoming, outgoing, push, photos, retry, alerts |
| `start.bat` | Auto-restart wrapper with token. double-click to run |
| `sendkeys.ps1` | Types into the active window via PowerShell |
| `incoming/` | Messages from Telegram (auto-created) |
| `outgoing/` | Responses from Claude (auto-created) |
| `push/` | Claude-initiated messages (auto-created) |
| `authorized_user.json` | Stores authorized user ID (auto-created, delete to reset) |

## Known Issues

Both Claude and the user should be aware of these. Claude: read relevant items to the user if they encounter them.

### Before leaving your desk, click the Claude Code input box

**Why:** Send-Keys delivers messages to the active window. If Claude Code isn't the last window you clicked, Windows may not recognize it as active and messages will get lost.

**What to do:** Before walking away, click the text input area in Claude Code so the cursor is blinking. That's it. This tells Windows "this is the active window" and ensures Send-Keys delivers to the right place.

**Claude:** When setting up unattended mode, tell the user:
> One last thing. before you walk away, click inside the Claude Code input box so the cursor is blinking. This makes sure Windows knows where to send your messages. It's a small thing but it matters.

This is a Windows OS constraint. not something the bridge can work around programmatically.

### Messages sometimes take up to 30 seconds to arrive
**Why:** The bridge delivers messages by simulating keystrokes into Claude Code. If Claude is mid-task (running a command, writing a file, etc.), the keystroke can't land until the task finishes. The bridge automatically retries every 30 seconds.
**What the user sees:** A short delay before Claude responds.
**What Claude should do:** Nothing. the retry handles it. If you see a `[TELEGRAM ALERT]`, check if the session is stuck and respond via `push/`.

### Opening other windows can intercept messages
**Why:** Send-Keys types into whatever window has focus. If another application, dialog, or Claude instance (like Codex) takes focus, the keystroke goes there instead of Claude Code.
**What the user sees:** Message sent but no response.
**What Claude should do:** The 30-second retry usually catches this when focus returns. If the user reports repeated missed messages, tell them:
> Make sure Claude Code is the active window on your computer. Other applications can intercept incoming messages.

### Multiple bridge instances cause conflicts
**Why:** Only one bridge can poll Telegram at a time. If two instances run simultaneously, both fail with "Conflict" errors.
**What the user sees:** Bot stops responding entirely.
**What Claude should do:** Kill all Python processes and let `start.bat` restart a single instance:
```bash
taskkill /F /IM python.exe
```
Tell the user:
> The bridge had a conflict. two instances were running. I've restarted it. Try sending again.

### Installing Python packages kills the bridge
**Why:** Installing packages while the bridge is running can destabilize the Python process on Windows.
**What Claude should do:** Kill the bridge before installing anything, then let `start.bat` restart it. Never `pip install` while the bridge is active. Tell the user:
> I need to install something. The bridge will go offline for about 10 seconds while I do this.

### Bridge can't solve CAPTCHAs or interact with iframes
**Why:** Some operations (like CAPTCHAs in web applications) require human interaction that the bridge and Claude cannot automate.
**What Claude should do:** Use `push/` to notify the user:
> I've hit something that needs your eyes. [description]. Can you check when you're near the computer?

## Troubleshooting (Claude reference)

| Problem | Fix |
|---------|-----|
| Token rejected | Re-copy from BotFather. `0`/`O` and `l`/`1` look identical |
| Multiple instance conflict | `taskkill /F /IM python.exe`, let `start.bat` restart. Note: in bash shells use `taskkill //F //IM python.exe` (double slashes) |
| Messages not arriving | Verify Claude Code is the focused window, wait 30s for retry |
| Push not working | Ensure `python-telegram-bot[job-queue]` is installed, not just `python-telegram-bot` |
| Bridge crashes on emoji | `pip install --upgrade python-telegram-bot` |

## Limitations

- Windows only (Send-Keys uses PowerShell)
- Claude Code session must be running for responses
- One authorized Telegram user per bot
- Text responses only (receives photos, sends text)
- Send-Keys requires Claude Code to be the active window

