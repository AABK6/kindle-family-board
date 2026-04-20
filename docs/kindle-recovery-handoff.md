# Kindle Recovery Handoff Pointer

The full recovery handoff for the current Kindle brick/recovery incident is stored in the shared recovery workspace:

```text
C:\Users\aabec\OneDrive\Documents\Playground\kindle-recovery\KINDLE_RECOVERY_HANDOFF.md
```

That file is intentionally long and self-contained so it can be pasted into a fresh Codex session on the AMD PC.

## Critical Summary

As of 2026-04-20, the Kindle Family Board device is not healthy:

- `Disable Diagnostics` now works, so this is no longer just a stuck-diags issue.
- Main boot reaches the Kindle tree/progress screen, then falls to `Your Kindle needs repair` with small `framework` text.
- Tequila diags can be booted from i.MX recovery using `imx_usb_loader`.
- USB storage enumerates as `1949:0004`, but Windows sees `Kindle Internal Storage` as `No Media / 0 bytes`.
- Diags USBnet enumerates as `0525:a4a2` and pings at `192.168.15.244`, but no SSH/telnet/HTTP ports are open.
- SelectBoot fastboot payload loads successfully, then the device disappears instead of enumerating as Kindle fastboot `1949:d0d0`.
- SelectBoot main payload loads successfully, but main still reaches `Your Kindle needs repair`.
- `M) MoviNand` produced `user sw md5sum error, update again`; it is not a FAT recovery menu.
- `D -> U USB Bundle Install` still produced `No Media / 0 bytes`.

## Next Recommended Recovery

Use an Intel/AMD PC with Kubrick or an equivalent x86 Linux K4 debrick setup.

The user accepts wiping/factory reset/re-hacking if that keeps the Kindle usable. The preferred destructive recovery target is user storage/FAT and local state, not arbitrary full eMMC erase.

After the Kindle is usable again, reinstall:

- K4 jailbreak
- MKK/KUAL
- USBNetwork
- linkss/screensaver hack
- this repo's Kindle runtime via `scripts/deploy_to_kindle.py`

Do not copy secrets from the old conversation into docs or prompts.

