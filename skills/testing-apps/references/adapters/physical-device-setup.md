# Physical iOS device setup

One-time-per-Mac (mostly) setup for `agent-device` to drive a real, cabled iPhone/iPad
instead of a simulator. Each layer fails with a different error; fix them in this
order rather than guessing. `agent-device help physical-device` has the tool's own
reference — this file is the symptom-to-fix map for the specific failures actually
hit, faster than re-deriving them from the general docs.

## 1. iOS Developer Mode (on the device)

Symptom: `agent-device apps`/`open` fails with *"The operation failed because
Developer Mode is disabled."*

Fix: on the device, **Settings > Privacy & Security > Developer Mode > on**, then let
it restart and unlock it. Ask the user to do this — it's a physical action on their
device.

## 2. macOS Developer Mode for Apple dev tools

Symptom: `agent-device snapshot -i` fails with *"Developer mode is disabled for Apple
development tools"* / hint to run `DevToolsSecurity -enable`.

Fix: the user runs `sudo DevToolsSecurity -enable` **in their own terminal**, entering
their macOS password at that native prompt. Never accept the password pasted into
chat — if it arrives that way anyway, don't use it, and tell the user to run the
command themselves instead. Confirm with `DevToolsSecurity -status`.

## 3. A local, usable code-signing identity

Symptom: `security find-identity -v -p codesigning` reports 0 valid identities, even
though `security find-certificate -a -c "Apple Development"` shows one. A certificate
without a matching **local private key** (e.g. synced from another Mac) counts as
invalid for signing.

Fix: in Xcode, **Settings > Accounts**, sign in with the Apple ID that should own the
identity (ask the user which one if more than one is plausible), select it, **Manage
Certificates… > + > Apple Development**. This generates a new certificate together
with a local private key. Re-check with `security find-identity -v -p codesigning`.

## 4. The device registered to the Apple Developer team

Symptom: build fails with *"Your team has no devices from which to generate a
provisioning profile."* — true by default for a fresh Personal (free) team; Apple only
registers a device's UDID once Xcode has actually built something to it.

Fix: in Xcode, create any throwaway project (File > New > Project > App), set its
**Signing & Capabilities > Team** to the target account, give it a **unique** Bundle
Identifier (a taken/generic one like `test.test` fails registration with its own
error), select the physical device as the run destination, and hit Run. The build
itself doesn't need to succeed — device registration happens as a side effect of
Xcode attempting it. A `codesign wants to access key "..." in your keychain` prompt
may appear here too; the user enters their **macOS login keychain password** (usually
the same as their account password) directly into that native dialog, never into chat.

## 5. Env vars for `agent-device` itself

Once 1-4 are done, every `agent-device open` on that device needs:

```
export AGENT_DEVICE_IOS_TEAM_ID=<team id, e.g. from the cert subject's OU field>
export AGENT_DEVICE_IOS_BUNDLE_ID=<unique reverse-DNS id, e.g. com.<you>.agentdevice.runner>
```

Find the team id from the certificate if unsure:

```
security find-certificate -c "Apple Development: <name>" -p ~/Library/Keychains/login.keychain-db \
  | openssl x509 -noout -subject
```

The team id is the `OU=` field.

Remember: a daemon already running from before these exports were set will ignore
them. Kill it first (see `mobile.md`'s daemon section) in the same command as the
export + `open`.
